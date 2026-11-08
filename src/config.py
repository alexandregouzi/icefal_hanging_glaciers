"""Paramètres communs à tout le projet (emprise, résolution, chemins)."""

from pathlib import Path

# Racine du projet : ce fichier est dans src/
ROOT = Path(__file__).resolve().parent.parent

# Emprise d'étude en LV95 (EPSG:2056) : xmin, ymin, xmax, ymax, en mètres.
# Construite à partir des 113 glaciers SGI2023 qui recoupent la zone initiale
# (7,6–7,95° E, 46,0–46,15° N), avec 500 m de marge pour inclure les parois au-dessus
# des glaciers, puis arrondie au kilomètre (= alignée sur les dalles swissALTI3D).
EMPRISE = (2_608_000, 1_090_000, 2_642_000, 1_113_000)
CRS = "EPSG:2056"

# Résolution du MNT pour les calculs régionaux (m)
RES_MNT = 10

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
