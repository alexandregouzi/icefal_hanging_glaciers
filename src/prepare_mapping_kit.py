"""Build the kit used to map hanging glaciers by hand in QGIS.

The kit is written to a folder given on the command line (QGIS runs on Windows and
handles GeoPackages better on a Windows drive than across the WSL share):

    manual_mapping.gpkg   the file you edit
        hanging_glaciers  empty polygon layer to draw in (front_type, state, confidence, notes, source)
        blocks            the 4 mapping blocks; set status to 'done' when a block is finished
    helpers.gpkg          read-only reference layers
        glaciers          the 127 SGI2023 glaciers of the study extent
        centerlines       SGI2023 centre lines (flow direction; downstream end = front)
        boreholes         glenglat boreholes (Alphubel, Chessjengletscher)
    dem_10m.tif           shown as a hillshade (style file dem_10m.qml)
    slope_10m.tif         slope classes 30/40/50° (style file slope_10m.qml)

The styles and forms (cliff/ramp and current/former lists, confidence 1–3) are applied
automatically by QGIS. `state` is 'current' for a hanging glacier today and 'former' only for
obvious former hanging glaciers (front clearly retreated from the rock step); former ones are
not used as training labels.
An existing manual_mapping.gpkg is never overwritten: it is only upgraded in place (missing
fields and layers are added, styles refreshed, drawn features untouched), and only when QGIS
does not have it open.

Usage (from the project root, with the outputs of prepare_dem/prepare_relief/prepare_sgi):
    python src/prepare_mapping_kit.py /mnt/c/Users/<user>/icefal_qgis
"""

import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

import qgis_styles
from config import CRS, DEM_RES, PROCESSED, RAW

# Mapping blocks (km in LV95: xmin, ymin, xmax, ymax), chosen in contrasting settings.
# Blocks 1 and 3 contain the glenglat boreholes (Alphubel and Chessjengletscher).
BLOCKS = [
    (1, "Alphubel–Täschhorn", (2629, 1099, 2634, 1104)),
    (2, "Weisshorn–Bisgletscher", (2617, 1103, 2622, 1108)),
    (3, "Fee–Allalin", (2634, 1097, 2639, 1102)),
    (4, "Zinal–Moming", (2613, 1098, 2618, 1103)),
]


def blocks_layer():
    rows = [dict(block_id=i, name=name, status="todo", image_year=None, notes="",
                 geometry=box(*(v * 1000 for v in km)))
            for i, name, km in BLOCKS]
    gdf = gpd.GeoDataFrame(rows, crs=CRS)
    gdf["image_year"] = gdf["image_year"].astype("Int64")
    return gdf


def empty_hanging_glaciers_layer():
    return gpd.GeoDataFrame(
        {"front_type": pd.Series(dtype="str"),
         "state": pd.Series(dtype="str"),
         "confidence": pd.Series(dtype="Int64"),
         "notes": pd.Series(dtype="str"),
         "source": pd.Series(dtype="str")},
        geometry=gpd.GeoSeries([], crs=CRS),
    )


def boreholes_layer():
    b = pd.read_csv(RAW / "glenglat" / "data" / "borehole.csv")
    b = b[b["glacier_name"].isin(["Alphubel South", "Chessjengletscher"])]
    b = b[["id", "glacier_name", "label", "elevation", "depth", "to_bed", "date_min", "longitude", "latitude"]]
    return gpd.GeoDataFrame(b, geometry=gpd.points_from_xy(b["longitude"], b["latitude"]), crs=4326).to_crs(CRS)


def add_default_style(gpkg, layer, geometry_column, qml):
    """Store a QML style in the GeoPackage so QGIS applies it when the layer is opened."""
    with sqlite3.connect(gpkg) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS layer_styles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, f_table_catalog TEXT, f_table_schema TEXT,
            f_table_name TEXT, f_geometry_column TEXT, styleName TEXT, styleQML TEXT, styleSLD TEXT,
            useAsDefault BOOLEAN, description TEXT, owner TEXT, ui TEXT, update_time DATETIME)""")
        con.execute("DELETE FROM layer_styles WHERE f_table_name = ?", (layer,))
        con.execute(
            "INSERT INTO layer_styles (f_table_catalog, f_table_schema, f_table_name, f_geometry_column, "
            "styleName, styleQML, styleSLD, useAsDefault, description, owner, ui, update_time) "
            "VALUES ('', '', ?, ?, ?, ?, '', 1, 'icefal mapping kit', '', '', ?)",
            (layer, geometry_column, layer, qml, datetime.now(timezone.utc).isoformat()),
        )


def upgrade_mapping_file(mapping):
    """Add missing fields/layers to an existing mapping file, without touching its features."""
    if any(mapping.with_name(mapping.name + suffix).exists() for suffix in ("-wal", "-shm")):
        sys.exit(f"{mapping} is open in QGIS (lock files present): close QGIS and run again.")

    with sqlite3.connect(mapping) as con:  # read-only queries
        columns = [row[1] for row in con.execute("PRAGMA table_info(hanging_glaciers)")]

    if "state" not in columns:
        # Through GDAL (ogrinfo), not plain sqlite3: the GeoPackage spatial-index triggers
        # call GDAL functions (ST_IsEmpty, ...) that plain SQLite does not know.
        for sql in ("ALTER TABLE hanging_glaciers ADD COLUMN state TEXT",
                    "UPDATE hanging_glaciers SET state = 'current'"):
            subprocess.run(["ogrinfo", "-q", str(mapping), "-sql", sql], check=True)
        print("  added field hanging_glaciers.state (existing polygons set to 'current')")

    if "source" not in columns:
        for sql in ("ALTER TABLE hanging_glaciers ADD COLUMN source TEXT",
                    "UPDATE hanging_glaciers SET source = 'initial'"):
            subprocess.run(["ogrinfo", "-q", str(mapping), "-sql", sql], check=True)
        print("  added field hanging_glaciers.source (existing polygons set to 'initial')")


def main(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. File to edit: never overwritten, since it holds the manual work
    mapping = out_dir / "manual_mapping.gpkg"
    if mapping.exists():
        print(f"{mapping} already exists: upgrading in place.")
        upgrade_mapping_file(mapping)
        for layer, qml in [("hanging_glaciers", qgis_styles.hanging_glaciers_qml()),
                           ("blocks", qgis_styles.blocks_qml())]:
            add_default_style(mapping, layer, "geometry", qml)
    else:
        empty_hanging_glaciers_layer().to_file(mapping, layer="hanging_glaciers", driver="GPKG",
                                               geometry_type="Polygon")
        blocks_layer().to_file(mapping, layer="blocks", driver="GPKG")
        add_default_style(mapping, "hanging_glaciers", "geometry", qgis_styles.hanging_glaciers_qml())
        add_default_style(mapping, "blocks", "geometry", qgis_styles.blocks_qml())
        print(f"Created {mapping} (layers hanging_glaciers, blocks)")

    # 2. Reference layers: rebuilt each time
    helpers = out_dir / "helpers.gpkg"
    helpers.unlink(missing_ok=True)
    glaciers = gpd.read_file(PROCESSED / "sgi2023_zone.gpkg", layer="glaciers")
    centerlines = gpd.read_file(RAW / "sgi2023" / "SGI_2023_centerlines.shp").to_crs(CRS)
    centerlines = centerlines[centerlines["sgi-id"].isin(glaciers["sgi-id"])]
    glaciers.to_file(helpers, layer="glaciers", driver="GPKG")
    centerlines.to_file(helpers, layer="centerlines", driver="GPKG")
    boreholes_layer().to_file(helpers, layer="boreholes", driver="GPKG")
    add_default_style(helpers, "glaciers", "geometry", qgis_styles.glaciers_qml())
    add_default_style(helpers, "centerlines", "geometry", qgis_styles.centerlines_qml())
    add_default_style(helpers, "boreholes", "geometry", qgis_styles.boreholes_qml())
    print(f"Created {helpers} ({len(glaciers)} glaciers, {len(centerlines)} centre lines, boreholes)")

    # 3. Rasters, each with a .qml style file that QGIS picks up automatically
    for name, qml in [(f"dem_{DEM_RES}m", qgis_styles.dem_hillshade_qml()),
                      (f"slope_{DEM_RES}m", qgis_styles.slope_qml())]:
        shutil.copy2(PROCESSED / f"{name}.tif", out_dir / f"{name}.tif")
        (out_dir / f"{name}.qml").write_text(qml, encoding="utf-8")
    print(f"Copied dem_{DEM_RES}m.tif and slope_{DEM_RES}m.tif with their styles")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
