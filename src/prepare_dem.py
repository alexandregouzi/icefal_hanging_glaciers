"""Merge the swissALTI3D tiles (2 m) into a single 10 m DEM over the study extent.

Mean resampling: each 10 m pixel is the exact mean of the 5 x 5 pixels at 2 m it
contains (fine roughness is smoothed out without shifting the terrain).
The mean is computed here, tile by tile, rather than leaving the resampling to GDAL:
GDAL may read the overviews embedded in the files, and the mean is then no longer
exact (differences of several metres were found in steep terrain).

The grid is aligned exactly on EXTENT, so that all derived layers
(slope, labels, predictions) share the same pixels.

Usage (from the project root):
    python src/prepare_dem.py
"""

import numpy as np
import rasterio
from rasterio.transform import from_origin

from config import CRS, DEM_RES, EXTENT, PROCESSED, RAW

OUT = PROCESSED / f"dem_{DEM_RES}m.tif"


def block_mean(z, factor):
    """Mean over factor x factor blocks (e.g. 500 x 500 px at 2 m -> 100 x 100 px at 10 m)."""
    h, w = z.shape
    return z.reshape(h // factor, factor, w // factor, factor).mean(axis=(1, 3))


def main():
    xmin, ymin, xmax, ymax = EXTENT
    width, height = (xmax - xmin) // DEM_RES, (ymax - ymin) // DEM_RES
    dem = np.full((height, width), np.nan, dtype="float32")  # NaN where there is no tile

    files = sorted((RAW / "swissalti3d").glob("*.tif"))
    for f in files:
        with rasterio.open(f) as tile:
            factor = round(DEM_RES / tile.res[0])  # 10 m / 2 m = 5
            z = tile.read(1, masked=True).filled(np.nan)
            b = tile.bounds
        # Position of the tile in the output grid (row 0 = north)
        col = int((b.left - xmin) // DEM_RES)
        row = int((ymax - b.top) // DEM_RES)
        block = block_mean(z, factor)
        dem[row:row + block.shape[0], col:col + block.shape[1]] = block

    profile = dict(driver="GTiff", height=height, width=width, count=1, dtype="float32",
                   crs=CRS, transform=from_origin(xmin, ymax, DEM_RES, DEM_RES), nodata=np.nan,
                   compress="deflate", tiled=True, blockxsize=256, blockysize=256)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT, "w", **profile) as dst:
        dst.write(dem, 1)

    print(f"{len(files)} tiles -> {OUT.relative_to(PROCESSED.parent.parent)}")
    print(f"  {width} x {height} pixels of {DEM_RES} m, {np.isfinite(dem).mean():.1%} covered, "
          f"elevations {np.nanmin(dem):.0f}–{np.nanmax(dem):.0f} m")


if __name__ == "__main__":
    main()
