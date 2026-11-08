"""Settings shared by the whole project (study extent, resolution, paths)."""

from pathlib import Path

# Project root: this file lives in src/
ROOT = Path(__file__).resolve().parent.parent

# Study extent in LV95 (EPSG:2056): xmin, ymin, xmax, ymax, in metres.
# Built from the 113 SGI2023 glaciers that intersect the initial area
# (7.6–7.95° E, 46.0–46.15° N), with a 500 m margin to include the rock walls above
# the glaciers, then rounded to the kilometre (= aligned with the swissALTI3D tiles).
EXTENT = (2_608_000, 1_090_000, 2_642_000, 1_113_000)
CRS = "EPSG:2056"

# DEM resolution for regional computations (m)
DEM_RES = 10

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
