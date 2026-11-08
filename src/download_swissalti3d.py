"""Download the swissALTI3D tiles (2 m) covering the study extent.

Source: swisstopo STAC API (data.geo.admin.ch), open data.
Each tile covers 1 km x 1 km. When a tile exists for several years, the most recent
one is kept. Tiles already on disk are not downloaded again.

Usage (from the project root):
    python src/download_swissalti3d.py
"""

import json
import urllib.request

from pyproj import Transformer

from config import EXTENT, RAW

RESOLUTION = "2"  # metres; resampled to 10 m afterwards
OUT_DIR = RAW / "swissalti3d"

STAC_URL = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items"


def extent_wgs84(extent):
    """WGS84 rectangle containing the LV95 extent (the STAC API only accepts WGS84)."""
    to_wgs84 = Transformer.from_crs(2056, 4326, always_xy=True)
    xmin, ymin, xmax, ymax = extent
    lons, lats = to_wgs84.transform([xmin, xmin, xmax, xmax], [ymin, ymax, ymin, ymax])
    return min(lons), min(lats), max(lons), max(lats)


def list_items(bbox):
    """Return all STAC tiles intersecting the rectangle (handles pagination)."""
    url = f"{STAC_URL}?bbox={','.join(f'{v:.5f}' for v in bbox)}&limit=100"
    items = []
    while url:
        with urllib.request.urlopen(url, timeout=60) as response:
            page = json.load(response)
        items += page["features"]
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
    return items


def tile_in_extent(tile, extent):
    """Tile '2612-1094' has its south-west corner at (2 612 000, 1 094 000)."""
    x_km, y_km = (int(v) for v in tile.split("-"))
    xmin, ymin, xmax, ymax = extent
    return xmin <= x_km * 1000 < xmax and ymin <= y_km * 1000 < ymax


def latest_tif_per_tile(items, resolution):
    """For each tile (e.g. '2612-1094'), keep the GeoTIFF URL of the most recent year."""
    latest = {}  # tile -> (year, url)
    for item in items:
        _, year, tile = item["id"].split("_")  # e.g. 'swissalti3d_2019_2612-1094'
        for name, asset in item["assets"].items():
            if name.endswith(".tif") and f"_{resolution}_2056_" in name:
                if tile not in latest or year > latest[tile][0]:
                    latest[tile] = (year, asset["href"])
    return latest


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tiles = latest_tif_per_tile(list_items(extent_wgs84(EXTENT)), RESOLUTION)
    tiles = {t: v for t, v in tiles.items() if tile_in_extent(t, EXTENT)}
    print(f"{len(tiles)} tiles in the extent, saved to {OUT_DIR}")

    new = 0
    for tile, (year, url) in sorted(tiles.items()):
        target = OUT_DIR / url.split("/")[-1]
        if target.exists():
            continue
        # Write to a .part file first, so an interrupted download is never mistaken for a complete tile
        partial = target.with_suffix(".part")
        urllib.request.urlretrieve(url, partial)
        partial.rename(target)
        new += 1
    print(f"Done: {new} new tiles downloaded.")


if __name__ == "__main__":
    main()
