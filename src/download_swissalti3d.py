"""Télécharge les dalles swissALTI3D (2 m) couvrant la zone d'étude.

Source : API STAC de swisstopo (data.geo.admin.ch), données libres.
Chaque dalle fait 1 km x 1 km. Quand une dalle existe pour plusieurs années,
on garde la plus récente.

Usage (depuis la racine du projet) :
    python src/download_swissalti3d.py
"""

import json
import urllib.request
from pathlib import Path

# Emprise du massif Mischabel–Weisshorn en WGS84 (lon_min, lat_min, lon_max, lat_max)
BBOX = (7.6, 46.0, 7.95, 46.15)
RESOLUTION = "2"  # mètres ; on rééchantillonne ensuite à 10 m
OUT_DIR = Path("data/raw/swissalti3d")

STAC_URL = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items"


def list_items(bbox):
    """Renvoie toutes les dalles STAC qui intersectent l'emprise (gère la pagination)."""
    url = f"{STAC_URL}?bbox={','.join(map(str, bbox))}&limit=100"
    items = []
    while url:
        with urllib.request.urlopen(url, timeout=60) as response:
            page = json.load(response)
        items += page["features"]
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
    return items


def latest_tif_per_tile(items, resolution):
    """Pour chaque dalle (ex. '2612-1094'), garde l'URL du GeoTIFF de l'année la plus récente."""
    latest = {}  # tuile -> (année, url)
    for item in items:
        _, year, tile = item["id"].split("_")  # ex. 'swissalti3d_2019_2612-1094'
        for name, asset in item["assets"].items():
            if name.endswith(".tif") and f"_{resolution}_2056_" in name:
                if tile not in latest or year > latest[tile][0]:
                    latest[tile] = (year, asset["href"])
    return latest


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tiles = latest_tif_per_tile(list_items(BBOX), RESOLUTION)
    print(f"{len(tiles)} dalles à télécharger dans {OUT_DIR}")

    for i, (tile, (year, url)) in enumerate(sorted(tiles.items()), start=1):
        target = OUT_DIR / url.split("/")[-1]
        if target.exists():
            continue
        # On écrit d'abord dans un .part : une dalle interrompue ne sera pas prise pour complète
        partial = target.with_suffix(".part")
        urllib.request.urlretrieve(url, partial)
        partial.rename(target)
        if i % 50 == 0:
            print(f"  {i}/{len(tiles)}")
    print("Terminé.")


if __name__ == "__main__":
    main()
