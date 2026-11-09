"""Group the probability map into candidate hanging glaciers and rank them with a geometric index.

A candidate is a set of connected glacier pixels (8-connectivity) with a probability ≥ 0.5,
of at least 1 ha. For each candidate, the variables describe what matters for a hanging glacier
that may break off: how much ice (area), how steep the ice (mean surface slope), and how high it
would fall (height of the rock step below its lower edge).

Geometric index: mean of the percentile ranks (0–1) of these three variables among all candidates.
It is a relative ranking within the massif, chosen before looking at the results; it is not calibrated
against observed ice avalanches.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import shapes
from scipy import ndimage
from shapely.geometry import shape

THRESHOLD = 0.5
MIN_AREA_HA = 1
INDEX_VARIABLES = ["area_ha", "slope_mean", "fall_height"]


def label_candidates(prob, res):
    """Connected patches of probability ≥ THRESHOLD of at least MIN_AREA_HA. Returns the label grid and count."""
    patches, n = ndimage.label(prob >= THRESHOLD, structure=np.ones((3, 3)))
    sizes = ndimage.sum(patches > 0, patches, range(1, n + 1)) * res**2 / 1e4
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes >= MIN_AREA_HA
    patches[~keep[patches]] = 0
    # renumber 1..k
    ids = np.unique(patches[patches > 0])
    lookup = np.zeros(n + 1, "int32")
    lookup[ids] = np.arange(1, len(ids) + 1)
    return lookup[patches], len(ids)


def describe(cand, n, res, prob, layers, glaciers, polygons_grid, block):
    """One row per candidate: location, size, terrain and overlap with the manual mapping."""
    idx = range(1, n + 1)
    mean = lambda a: ndimage.mean(a, cand, idx)
    pct = lambda a, q: np.array([np.percentile(a[cand == i], q) for i in idx])
    glacier_of = [np.bincount(layers["glacier"][cand == i]).argmax() - 1 for i in idx]

    df = pd.DataFrame({
        "candidate_id": list(idx),
        "glacier": glaciers["name"].fillna("unnamed").to_numpy()[glacier_of],
        "sgi_id": glaciers["sgi-id"].to_numpy()[glacier_of],
        "glacier_area_km2": glaciers["area_km2"].to_numpy()[glacier_of],
        "area_ha": ndimage.sum(cand > 0, cand, idx) * res**2 / 1e4,
        "mean_prob": mean(prob),
        "z_min": ndimage.minimum(layers["elevation"], cand, idx),
        "z_max": ndimage.maximum(layers["elevation"], cand, idx),
        "slope_mean": mean(layers["slope"]),
        "fall_height": pct(layers["step_height"], 90),     # height of the step below the lower edge (m)
        "northness": mean(layers["northness"]),
        "in_block": ndimage.maximum(block > 0, cand, idx).astype(bool),
        "mapped_share": mean(polygons_grid > 0),            # share covered by the manual mapping
    })
    ranks = df[INDEX_VARIABLES].rank(pct=True)
    df["geometric_index"] = ranks.mean(axis=1)
    df["rank"] = df["geometric_index"].rank(ascending=False, method="min").astype(int)
    return df.round({"glacier_area_km2": 2, "area_ha": 1, "mean_prob": 2, "z_min": 0, "z_max": 0,
                     "slope_mean": 1, "fall_height": 0, "northness": 2, "mapped_share": 2, "geometric_index": 3})


def polygons_of(cand, transform, crs):
    rows = [{"candidate_id": int(v), "geometry": shape(g)}
            for g, v in shapes(cand, mask=cand > 0, transform=transform)]
    return gpd.GeoDataFrame(rows, crs=crs).dissolve("candidate_id").reset_index()
