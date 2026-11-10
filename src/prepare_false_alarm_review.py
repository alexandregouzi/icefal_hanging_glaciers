"""Turn the false alarms of the cross-validation into a layer to check on the imagery in QGIS.

A false alarm is a glacier pixel of a mapping block predicted hanging (out-of-fold probability ≥ 0.5)
but outside the mapped polygons. Connected pixels are grouped into patches; patches of at least 1 ha
are written to false_alarms_review.gpkg (layer false_alarms) in the QGIS kit folder, with an empty
`verdict` field to fill in: missed_hanging, model_error or unsure.

Input: data/processed/oof_probability_10m.tif (saved by notebooks/03_classifier.ipynb).
An existing review file is never overwritten, since it holds the verdicts.

Usage (from the project root):
    python src/prepare_false_alarm_review.py /mnt/c/Users/<user>/icefal_qgis
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from scipy import ndimage
from shapely.geometry import shape

import qgis_styles
from config import CRS, DEM_RES, PROCESSED
from prepare_mapping_kit import add_default_style

MIN_AREA_HA = 1
THRESHOLD = 0.5


def false_alarm_patches():
    with rasterio.open(PROCESSED / f"oof_probability_{DEM_RES}m.tif") as src:
        p = src.read(1)
        transform = src.transform
    with rasterio.open(PROCESSED / f"labels_{DEM_RES}m.tif") as src:
        labels = dict(zip(src.descriptions, src.read()))
    glacier, hanging, block = labels["glacier"], labels["hanging"], labels["block"]
    glaciers = gpd.read_file(PROCESSED / "sgi2023_zone.gpkg", layer="glaciers")

    alarm = (p >= THRESHOLD) & (hanging == 0) & (glacier > 0) & (block > 0)
    patches, n = ndimage.label(alarm, structure=np.ones((3, 3)))  # 8-connected
    near_mapped = ndimage.binary_dilation(hanging == 1, iterations=1)

    rows = []
    for geom, value in shapes(patches.astype("int32"), mask=alarm, transform=transform):
        rows.append({"label": int(value), "geometry": shape(geom)})
    gdf = gpd.GeoDataFrame(rows, crs=CRS).dissolve("label").reset_index()

    stats = []
    for label in gdf["label"]:
        px = patches == label
        stats.append({
            "area_ha": px.sum() * DEM_RES**2 / 1e4,
            "block": int(np.bincount(block[px]).argmax()),
            "glacier": glaciers["name"].iloc[np.bincount(glacier[px]).argmax() - 1],
            "mean_prob": float(p[px].mean()),
            "touches_mapped": bool((px & near_mapped).any()),  # edge of a mapped polygon, or a separate place
        })
    gdf = gdf.join(gpd.GeoDataFrame(stats)).drop(columns="label")
    gdf = gdf[gdf["area_ha"] >= MIN_AREA_HA].sort_values("area_ha", ascending=False).reset_index(drop=True)
    gdf.insert(0, "patch_id", np.arange(1, len(gdf) + 1))
    gdf["area_ha"] = gdf["area_ha"].round(1)
    gdf["mean_prob"] = gdf["mean_prob"].round(2)
    gdf["verdict"] = None
    gdf["notes"] = None
    return gdf


def main(out_dir):
    out = out_dir / "false_alarms_review.gpkg"
    if out.exists():
        sys.exit(f"{out} already exists (it may hold your verdicts): not overwritten.")
    gdf = false_alarm_patches()
    gdf.to_file(out, layer="false_alarms", driver="GPKG")
    add_default_style(out, "false_alarms", "geometry", qgis_styles.false_alarms_qml())
    print(f"{out}: {len(gdf)} patches ≥ {MIN_AREA_HA} ha ({gdf['area_ha'].sum():.0f} ha), "
          f"{gdf['touches_mapped'].sum()} touching a mapped polygon")
    print(gdf.drop(columns=["geometry", "verdict", "notes"]).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
