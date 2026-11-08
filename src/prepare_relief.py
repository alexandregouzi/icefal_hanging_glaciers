"""Compute the layers derived from the 10 m DEM (for now: slope).

Usage (from the project root):
    python src/prepare_relief.py
"""

import numpy as np
import rasterio

from config import DEM_RES, PROCESSED
from relief import slope

DEM = PROCESSED / f"dem_{DEM_RES}m.tif"
OUT = PROCESSED / f"slope_{DEM_RES}m.tif"


def main():
    with rasterio.open(DEM) as src:
        z = src.read(1)
        profile = src.profile

    s = slope(z, DEM_RES).astype("float32")
    with rasterio.open(OUT, "w", **profile) as dst:
        dst.write(s, 1)

    print(f"{OUT.relative_to(PROCESSED.parent.parent)}: median slope {np.nanmedian(s):.0f}°, "
          f"{np.nanmean(s > 35):.0%} of pixels steeper than 35°, max {np.nanmax(s):.0f}°")


if __name__ == "__main__":
    main()
