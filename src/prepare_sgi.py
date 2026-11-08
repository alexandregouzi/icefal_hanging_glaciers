"""Extrait les glaciers SGI2023 entièrement contenus dans l'emprise d'étude.

On ne garde que les glaciers entiers (pas de contour coupé à la limite), pour que
les variables calculées par glacier (surface, pente, altitudes) restent justes.

Usage (depuis la racine du projet) :
    python src/prepare_sgi.py
"""

import geopandas as gpd
from shapely.geometry import box

from config import CRS, EMPRISE, PROCESSED, RAW

OUT = PROCESSED / "sgi2023_zone.gpkg"


def main():
    sgi = gpd.read_file(RAW / "sgi2023" / "SGI_2023_glaciers.shp").to_crs(CRS)
    emprise = box(*EMPRISE)

    dedans = sgi[sgi.within(emprise)].copy()
    coupes = sgi[sgi.intersects(emprise) & ~sgi.within(emprise)]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    dedans.to_file(OUT, layer="glaciers", driver="GPKG")
    print(f"{len(dedans)} glaciers entiers ({dedans['area_km2'].sum():.1f} km²) -> "
          f"{OUT.relative_to(PROCESSED.parent.parent)}")
    print(f"{len(coupes)} glaciers à cheval sur la limite, écartés : "
          + ", ".join(sorted(coupes["name"].fillna("sans nom"))))


if __name__ == "__main__":
    main()
