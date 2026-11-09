"""What lies below each glacier pixel: walk down the line of steepest descent.

A hanging glacier is defined by what is under its front (a rock step), which the local
slope does not see. From every glacier pixel we follow the steepest-descent path (D8: at each
step, move to the lowest of the 8 neighbours) and record what the path crosses.
Holes in the SGI outlines (rock bands inside a glacier) count as "not glacier", so a band of
rock between two parts of the same glacier is seen as the exit of the upper part.
"""

import numpy as np
from scipy import ndimage

# The 8 neighbours (row offset, column offset)
OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def steepest_descent(z, res):
    """For each pixel, the flat index of its steepest downhill neighbour (itself in a pit or on the edge)."""
    rows, cols = z.shape
    zp = np.pad(z, 1, constant_values=np.inf)
    best_drop = np.zeros(z.shape)
    target = np.arange(z.size).reshape(z.shape)
    r, c = np.indices(z.shape)
    for dr, dc in OFFSETS:
        neighbour = zp[1 + dr:rows + 1 + dr, 1 + dc:cols + 1 + dc]
        drop = (z - neighbour) / (res * np.hypot(dr, dc))   # gradient towards that neighbour
        better = drop > best_drop
        best_drop[better] = drop[better]
        target[better] = ((r + dr) * cols + (c + dc))[better]
    return target.ravel()


def walk_downslope(z, ice, slope, res, max_dist=500):
    """Follow the steepest-descent path from every glacier pixel, up to max_dist metres.

    z: DEM, ice: boolean glacier mask, slope: slope (degrees), res: pixel size (m).
    Returns a dict of 2D arrays (NaN outside the glaciers):
        drop_below_200m   elevation lost over the first 200 m of path (m)
        slope_max_below   steepest slope crossed in the first 200 m (degrees)
        dist_to_exit      path length until the path leaves the glacier (m; max_dist if it does not)
        step_height       elevation lost over the first 100 m after the exit: height of what lies
                          below the glacier's lower edge (m; 0 if no exit within max_dist)
    """
    zs = ndimage.uniform_filter(np.where(np.isnan(z), np.nanmax(z), z), 3)  # smooth to avoid 1-pixel pits
    target = steepest_descent(zs, res)
    zf, icef, sf = z.ravel(), ice.ravel(), np.nan_to_num(slope.ravel())

    start = np.flatnonzero(icef)
    pos = start.copy()
    dist = np.zeros(len(start))                 # path length walked so far
    exit_dist = np.full(len(start), np.nan)     # path length at which the path left the glacier
    exit_z = np.full(len(start), np.nan)        # elevation at the exit
    drop200 = np.full(len(start), np.nan)
    smax = np.zeros(len(start))
    step = np.zeros(len(start))
    cols = z.shape[1]

    while True:
        nxt = target[pos]
        moving = (nxt != pos) & (dist < max_dist + 100)
        if not moving.any():
            break
        dr = nxt // cols - pos // cols
        dc = nxt % cols - pos % cols
        dist = dist + moving * res * np.hypot(dr, dc)
        pos = np.where(moving, nxt, pos)

        within200 = dist <= 200
        smax = np.where(within200, np.maximum(smax, sf[pos]), smax)
        reached200 = np.isnan(drop200) & (dist >= 200)
        drop200[reached200] = zf[start[reached200]] - zf[pos[reached200]]

        leaving = np.isnan(exit_dist) & ~icef[pos] & (dist <= max_dist)
        exit_dist[leaving] = dist[leaving]
        exit_z[leaving] = zf[pos[leaving]]
        after = ~np.isnan(exit_dist) & (dist - exit_dist <= 100)
        step = np.where(after, np.maximum(step, exit_z - zf[pos]), step)

    # Paths that stopped (pit) before 200 m: use the drop to where they stopped
    short = np.isnan(drop200)
    drop200[short] = zf[start[short]] - zf[pos[short]]

    out = {}
    for name, values in [("drop_below_200m", drop200), ("slope_max_below", smax),
                         ("dist_to_exit", np.where(np.isnan(exit_dist), max_dist, exit_dist)),
                         ("step_height", step)]:
        grid = np.full(z.shape, np.nan, "float32")
        grid.flat[start] = values
        out[name] = grid
    return out
