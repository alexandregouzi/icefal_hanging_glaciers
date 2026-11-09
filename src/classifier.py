"""Random forest and leave-one-block-out cross-validation, shared by notebooks 03 and 04."""

import numpy as np
import rasterio
from sklearn.ensemble import RandomForestClassifier

from config import DEM_RES, PROCESSED

# Variables of the main model: every terrain variable except the area of the SGI unit, which lets
# the forest take the shortcut "small unit = hanging" and miss hanging parts of large glaciers
# (see notebook 03).
EXCLUDED_VARIABLES = ["log10_glacier_area"]


def make_forest():
    return RandomForestClassifier(n_estimators=200, min_samples_leaf=20, max_features="sqrt",
                                  class_weight="balanced_subsample", n_jobs=-1, random_state=0)


def cross_validate(X, y, block):
    """Leave-one-block-out: out-of-fold probability of 'hanging' for every sample, and the forest of each fold."""
    proba, forests = np.zeros(len(y)), {}
    for k in np.unique(block):
        test = block == k
        forests[k] = make_forest().fit(X[~test], y[~test])
        proba[test] = forests[k].predict_proba(X[test])[:, 1]
    return proba, forests


def load_grids():
    """Feature stack (variables × rows × cols), variable names, label bands (dict of 2D arrays), DEM profile."""
    with rasterio.open(PROCESSED / f"features_{DEM_RES}m.tif") as src:
        names = list(src.descriptions)
        features = src.read()
        profile = src.profile
    with rasterio.open(PROCESSED / f"labels_{DEM_RES}m.tif") as src:
        labels = dict(zip(src.descriptions, src.read()))
    return features, names, labels, profile


def write_probability(prob, profile, path):
    profile = profile.copy()
    profile.update(count=1, dtype="float32", nodata=np.nan, compress="deflate")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(prob.astype("float32"), 1)
