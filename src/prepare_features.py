"""Build the classifier inputs on the 10 m grid: terrain variables and labels.

All variables come from the DEM and the SGI2023 outlines only (no imagery), so that the
labels, drawn from the orthophotos, are not used to build the inputs.

Outputs (data/processed/):
    features_10m.tif   one band per variable (names in the band descriptions)
    labels_10m.tif     band 1 glacier: index of the SGI2023 glacier (row in sgi2023_zone.gpkg + 1), 0 = no glacier
                       band 2 hanging: 1 inside a mapped hanging glacier polygon, else 0
                       band 3 confidence: confidence of that polygon (1–3), 0 = none
                       band 4 block: mapping block (1–4), 0 = outside the blocks
                       band 5 hanging_revised: as band 2, plus the polygons added after the review of the
                              false alarms (source = 'review')
                       band 6 excluded: pixels of the reviewed false alarms judged hanging or unsure but not
                              redrawn as a polygon (left out of the revised labels: neither hanging nor not)

Band 2 uses only the polygons of the initial, blind mapping (source = 'initial'): it is the reference for
the evaluation. Bands 5–6 are the labels corrected after looking at the model's errors (notebook 04).

Usage (from the project root):
    python src/prepare_features.py
"""

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from scipy import ndimage

from config import DEM_RES, PROCESSED, RAW
from downslope import walk_downslope
from relief import aspect, curvature, slope

DEM = PROCESSED / f"dem_{DEM_RES}m.tif"
OUT_FEATURES = PROCESSED / f"features_{DEM_RES}m.tif"
OUT_LABELS = PROCESSED / f"labels_{DEM_RES}m.tif"
MAPPING = RAW / "manual_mapping.gpkg"
REVIEW = RAW / "false_alarms_review.gpkg"

WINDOW = 21  # neighbourhood for the context variables: 21 × 21 pixels = 210 m


def burn(shapes, grid, dtype="int16"):
    """Rasterize (geometry, value) pairs on the DEM grid (a pixel is inside if its centre is)."""
    shapes = list(shapes)
    if not shapes:
        return np.zeros(grid["shape"], dtype)
    return rasterize(shapes, out_shape=grid["shape"], transform=grid["transform"], fill=0, dtype=dtype)


def labels(grid):
    glaciers = gpd.read_file(PROCESSED / "sgi2023_zone.gpkg", layer="glaciers")
    polygons = gpd.read_file(MAPPING, layer="hanging_glaciers")
    polygons["geometry"] = polygons.make_valid()  # a few hand-drawn polygons may self-intersect
    initial = polygons[polygons["source"] == "initial"]
    blocks = gpd.read_file(MAPPING, layer="blocks")
    blocks = blocks[blocks["status"] == "done"]

    glacier = burn(zip(glaciers.geometry, range(1, len(glaciers) + 1)), grid)
    ice = glacier > 0                              # labels only on glacier ice (SGI2023 outlines)
    confidence = burn(zip(initial.geometry, initial["confidence"].astype(int)), grid) * ice
    is_hanging = (confidence > 0).astype("int16")
    block = burn(zip(blocks.geometry, blocks["block_id"].astype(int)), grid)

    # Revised labels: all polygons; reviewed false alarms judged hanging/unsure without a polygon are excluded.
    # A false alarm that a review polygon overlaps is described by that polygon (the rest of it is not hanging).
    revised = (burn(((g, 1) for g in polygons.geometry), grid) * ice).astype("int16")
    review = gpd.read_file(REVIEW, layer="false_alarms")
    review_polygons = polygons[polygons["source"] == "review"].union_all()
    pending = review[review["verdict"].isin(["missed_hanging", "unsure"]) & ~review.intersects(review_polygons)]
    excluded = (burn(((g, 1) for g in pending.geometry), grid) * ice * (1 - revised)).astype("int16")

    return glaciers, {"glacier": glacier, "hanging": is_hanging, "confidence": confidence, "block": block,
                      "hanging_revised": revised, "excluded": excluded}


def features(z, glaciers, glacier):
    """Terrain variables. Context variables summarise a 210 m neighbourhood around each pixel;
    the last four follow the steepest-descent path below each glacier pixel."""
    s = slope(z, DEM_RES)
    a = aspect(z, DEM_RES)
    z_low = np.where(np.isnan(z), np.inf, z)      # missing DEM (outside Switzerland, no glacier there)
    s_zero = np.where(np.isnan(s), 0, s)

    # Per-glacier values, spread to the glacier's pixels
    inside = glacier > 0
    idx = glacier[inside] - 1
    area = np.full(z.shape, np.nan, "float32")
    area[inside] = glaciers["area_km2"].to_numpy()[idx]
    zmin = glaciers["masl_min"].to_numpy()[idx]
    zmax = glaciers["masl_max"].to_numpy()[idx]
    rel_elev = np.full(z.shape, np.nan, "float32")
    rel_elev[inside] = np.clip((z[inside] - zmin) / (zmax - zmin), 0, 1)

    below = walk_downslope(z, inside, s, DEM_RES)  # what lies downslope (see downslope.py)

    return {
        "elevation": z,                                                           # m
        "slope": s,                                                               # degrees
        "northness": np.cos(a),                                                   # 1 = north-facing
        "eastness": np.sin(a),                                                    # 1 = east-facing
        "curvature": curvature(ndimage.uniform_filter(z, 3), DEM_RES),            # 1/100 m, DEM smoothed over 30 m
        "slope_mean_210m": ndimage.uniform_filter(s_zero, WINDOW),                # mean slope around the pixel
        "slope_max_210m": ndimage.maximum_filter(s_zero, WINDOW),                 # steepest terrain nearby (rock step?)
        "drop_210m": z - ndimage.minimum_filter(z_low, WINDOW),                   # m above the lowest point nearby
        "dist_to_edge": ndimage.distance_transform_edt(inside) * DEM_RES,         # m to the glacier outline
        "rel_elevation": rel_elev,                                                # 0 = glacier's lowest point, 1 = highest
        "log10_glacier_area": np.log10(area),                                     # size of the SGI2023 unit (km²)
        **below,                                                                  # drop_below_200m, slope_max_below,
    }                                                                             # dist_to_exit, step_height


def main():
    with rasterio.open(DEM) as src:
        z = src.read(1)
        profile = src.profile
    grid = {"shape": z.shape, "transform": profile["transform"]}

    glaciers, lab = labels(grid)
    feat = features(z, glaciers, lab["glacier"])

    profile.update(count=len(feat), dtype="float32", nodata=np.nan, compress="deflate", predictor=3, tiled=True)
    with rasterio.open(OUT_FEATURES, "w", **profile) as dst:
        for i, (name, band) in enumerate(feat.items(), start=1):
            dst.write(band.astype("float32"), i)
            dst.set_band_description(i, name)

    profile.update(count=len(lab), dtype="int16", nodata=None, predictor=2)
    with rasterio.open(OUT_LABELS, "w", **profile) as dst:
        for i, (name, band) in enumerate(lab.items(), start=1):
            dst.write(band, i)
            dst.set_band_description(i, name)

    ice = lab["glacier"] > 0
    in_blocks = ice & (lab["block"] > 0)
    print(f"{OUT_FEATURES.name}: {len(feat)} variables ({', '.join(feat)})")
    print(f"{OUT_LABELS.name}: {ice.sum():,} glacier pixels, {in_blocks.sum():,} in the mapping blocks, "
          f"of which {lab['hanging'][in_blocks].sum():,} hanging ({lab['hanging'][in_blocks].mean():.1%})")
    print(f"revised labels: {lab['hanging_revised'][in_blocks].sum():,} hanging, "
          f"{lab['excluded'][in_blocks].sum():,} excluded (reviewed false alarms not redrawn)")
    outside = lab["hanging"].astype(bool) & ~in_blocks
    print(f"hanging pixels outside the blocks (glaciers crossing a block edge, not used): {outside.sum():,}")


if __name__ == "__main__":
    main()
