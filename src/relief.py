"""Terrain computations on a DEM."""

import numpy as np


def hillshade(z, res, azimuth=315, altitude=45):
    """Classic hillshade: sun in the north-west (315°), 45° above the horizon.

    z: DEM (2D, row 0 = north), res: pixel size in m.
    Returns a value between -1 and 1 (bright = facing the sun).
    """
    dy, dx = np.gradient(z, res)
    dy = -dy  # rows run from north to south: flip so that the y axis points north
    slope_rad = np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, -dy)  # downslope direction, measured from north
    az, alt = np.radians(azimuth), np.radians(altitude)
    return np.sin(alt) * np.cos(slope_rad) + np.cos(alt) * np.sin(slope_rad) * np.cos(az - aspect)


def slope(z, res):
    """Slope in degrees (0 = flat, 90 = vertical), from centred differences.

    z: DEM (2D), res: pixel size in m. Pixels next to a NaN are NaN;
    on the grid edges, np.gradient uses a one-sided difference.
    """
    dy, dx = np.gradient(z, res)
    return np.degrees(np.arctan(np.hypot(dx, dy)))
