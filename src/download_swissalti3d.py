"""Télécharge les dalles swissALTI3D (2 m) couvrant l'emprise d'étude.

Source : API STAC de swisstopo (data.geo.admin.ch), données libres.
Chaque dalle fait 1 km x 1 km. Quand une dalle existe pour plusieurs années,
on garde la plus récente. Les dalles déjà présentes ne sont pas retéléchargées.

Usage (depuis la racine du projet) :
    python src/download_swissalti3d.py
"""

import json
import urllib.request

from pyproj import Transformer

from config import EMPRISE, RAW

RESOLUTION = "2"  # mètres ; on rééchantillonne ensuite à 10 m
OUT_DIR = RAW / "swissalti3d"

STAC_URL = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items"


def emprise_wgs84(emprise):
    """Rectangle WGS84 qui contient l'emprise LV95 (l'API STAC n'accepte que le WGS84)."""
    vers_wgs84 = Transformer.from_crs(2056, 4326, always_xy=True)
    xmin, ymin, xmax, ymax = emprise
    lons, lats = vers_wgs84.transform([xmin, xmin, xmax, xmax], [ymin, ymax, ymin, ymax])
    return min(lons), min(lats), max(lons), max(lats)


def list_items(bbox):
    """Renvoie toutes les dalles STAC qui intersectent le rectangle (gère la pagination)."""
    url = f"{STAC_URL}?bbox={','.join(f'{v:.5f}' for v in bbox)}&limit=100"
    items = []
    while url:
        with urllib.request.urlopen(url, timeout=60) as response:
            page = json.load(response)
        items += page["features"]
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
    return items


def dalle_dans_emprise(tile, emprise):
    """Une dalle '2612-1094' a son coin sud-ouest en (2 612 000, 1 094 000)."""
    x_km, y_km = (int(v) for v in tile.split("-"))
    xmin, ymin, xmax, ymax = emprise
    return xmin <= x_km * 1000 < xmax and ymin <= y_km * 1000 < ymax


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
    tiles = latest_tif_per_tile(list_items(emprise_wgs84(EMPRISE)), RESOLUTION)
    tiles = {t: v for t, v in tiles.items() if dalle_dans_emprise(t, EMPRISE)}
    print(f"{len(tiles)} dalles dans l'emprise, enregistrées dans {OUT_DIR}")

    nouvelles = 0
    for tile, (year, url) in sorted(tiles.items()):
        target = OUT_DIR / url.split("/")[-1]
        if target.exists():
            continue
        # On écrit d'abord dans un .part : une dalle interrompue ne sera pas prise pour complète
        partial = target.with_suffix(".part")
        urllib.request.urlretrieve(url, partial)
        partial.rename(target)
        nouvelles += 1
    print(f"Terminé : {nouvelles} nouvelles dalles téléchargées.")


if __name__ == "__main__":
    main()
