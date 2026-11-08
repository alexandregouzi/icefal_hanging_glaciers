"""Assemble les dalles swissALTI3D (2 m) en un seul MNT à 10 m sur l'emprise d'étude.

Rééchantillonnage par moyenne : chaque pixel de 10 m est la moyenne exacte des 5 x 5
pixels de 2 m qu'il contient (on lisse la rugosité fine sans décaler le relief).
On fait la moyenne nous-mêmes, dalle par dalle, plutôt que de laisser GDAL rééchantillonner :
GDAL peut passer par les aperçus (overviews) intégrés aux fichiers et la moyenne n'est
alors plus exacte (écarts de plusieurs mètres constatés en terrain raide).

La grille est calée exactement sur EMPRISE, pour que toutes les couches dérivées
(pente, étiquettes, prédictions) partagent les mêmes pixels.

Usage (depuis la racine du projet) :
    python src/prepare_dem.py
"""

import numpy as np
import rasterio
from rasterio.transform import from_origin

from config import CRS, EMPRISE, PROCESSED, RAW, RES_MNT

OUT = PROCESSED / f"mnt_{RES_MNT}m.tif"


def moyenne_par_blocs(z, facteur):
    """Moyenne sur des blocs facteur x facteur (ex. 500 x 500 px à 2 m -> 100 x 100 px à 10 m)."""
    h, w = z.shape
    return z.reshape(h // facteur, facteur, w // facteur, facteur).mean(axis=(1, 3))


def main():
    xmin, ymin, xmax, ymax = EMPRISE
    largeur, hauteur = (xmax - xmin) // RES_MNT, (ymax - ymin) // RES_MNT
    mnt = np.full((hauteur, largeur), np.nan, dtype="float32")  # NaN là où il n'y a pas de dalle

    fichiers = sorted((RAW / "swissalti3d").glob("*.tif"))
    for f in fichiers:
        with rasterio.open(f) as tuile:
            facteur = round(RES_MNT / tuile.res[0])  # 10 m / 2 m = 5
            z = tuile.read(1, masked=True).filled(np.nan)
            b = tuile.bounds
        # Position de la dalle dans la grille de sortie (ligne 0 = nord)
        col = int((b.left - xmin) // RES_MNT)
        lig = int((ymax - b.top) // RES_MNT)
        bloc = moyenne_par_blocs(z, facteur)
        mnt[lig:lig + bloc.shape[0], col:col + bloc.shape[1]] = bloc

    profil = dict(driver="GTiff", height=hauteur, width=largeur, count=1, dtype="float32",
                  crs=CRS, transform=from_origin(xmin, ymax, RES_MNT, RES_MNT), nodata=np.nan,
                  compress="deflate", tiled=True, blockxsize=256, blockysize=256)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT, "w", **profil) as dst:
        dst.write(mnt, 1)

    print(f"{len(fichiers)} dalles -> {OUT.relative_to(PROCESSED.parent.parent)}")
    print(f"  {largeur} x {hauteur} pixels de {RES_MNT} m, {np.isfinite(mnt).mean():.1%} couverts, "
          f"altitudes {np.nanmin(mnt):.0f}–{np.nanmax(mnt):.0f} m")


if __name__ == "__main__":
    main()
