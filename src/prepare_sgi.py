"""Extract the SGI2023 glaciers that lie entirely within the study extent.

Only whole glaciers are kept (no outline cut at the boundary), so that per-glacier
variables (area, slope, elevations) stay correct.

Usage (from the project root):
    python src/prepare_sgi.py
"""

import geopandas as gpd
from shapely.geometry import box

from config import CRS, EXTENT, PROCESSED, RAW

OUT = PROCESSED / "sgi2023_zone.gpkg"


def main():
    sgi = gpd.read_file(RAW / "sgi2023" / "SGI_2023_glaciers.shp").to_crs(CRS)
    extent = box(*EXTENT)

    inside = sgi[sgi.within(extent)].copy()
    crossing = sgi[sgi.intersects(extent) & ~sgi.within(extent)]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    inside.to_file(OUT, layer="glaciers", driver="GPKG")
    print(f"{len(inside)} whole glaciers ({inside['area_km2'].sum():.1f} km²) -> "
          f"{OUT.relative_to(PROCESSED.parent.parent)}")
    print(f"{len(crossing)} glaciers crossing the boundary, left out: "
          + ", ".join(sorted(crossing["name"].fillna("unnamed"))))


if __name__ == "__main__":
    main()
