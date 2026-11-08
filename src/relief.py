"""Fonctions de calcul sur le relief (MNT)."""

import numpy as np


def ombrage(z, res, azimut=315, hauteur=45):
    """Ombrage classique : soleil au nord-ouest (315°), 45° au-dessus de l'horizon.

    z : MNT (2D, ligne 0 = nord), res : taille de pixel en m.
    Renvoie une valeur entre -1 et 1 (clair = face au soleil).
    """
    dy, dx = np.gradient(z, res)
    dy = -dy  # les lignes vont du nord vers le sud : on remet l'axe y vers le nord
    pente = np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, -dy)  # direction de la descente, comptée depuis le nord
    az, h = np.radians(azimut), np.radians(hauteur)
    return np.sin(h) * np.cos(pente) + np.cos(h) * np.sin(pente) * np.cos(az - aspect)
