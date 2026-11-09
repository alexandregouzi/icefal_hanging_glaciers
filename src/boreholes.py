"""Borehole temperatures of Beer et al. (2026) from the glenglat database.

Beer et al. (2026) measured 23 boreholes on 6 Swiss sites (2,760–3,820 m) with the same method in 2024–2026,
including Alphubel and Chessjengletscher in the study area. For each borehole we keep the mean temperature of
each sensor over the last 365 days of equilibrium profiles (profiles disturbed by drilling are flagged
`equilibrium = false` in glenglat and left out).
"""

import pandas as pd

from config import RAW

GLENGLAT = RAW / "glenglat" / "data"
SOURCES = ["beer2026", "beer2026a"]


def boreholes():
    """Borehole table of the Beer et al. (2026) sites."""
    b = pd.read_csv(GLENGLAT / "borehole.csv")
    return b[b["source_id"] == "beer2026"].set_index("id")


def annual_profiles(min_days=300):
    """Mean temperature per borehole and sensor depth over the last 365 days of equilibrium profiles.

    Returns a table (borehole_id, depth, temperature, days) for boreholes with at least min_days of record.
    """
    profiles = pd.concat([pd.read_csv(GLENGLAT / s / "profile.csv") for s in SOURCES])
    values = pd.concat([pd.read_csv(GLENGLAT / s / "measurement.csv") for s in SOURCES])
    profiles = profiles[profiles["equilibrium"] == True].copy()   # noqa: E712 (column of booleans)
    profiles["date"] = pd.to_datetime(profiles["date_min"])
    x = values.merge(profiles[["borehole_id", "id", "date"]],
                     left_on=["borehole_id", "profile_id"], right_on=["borehole_id", "id"])

    rows = []
    for bid, g in x.groupby("borehole_id"):
        last = g["date"].max()
        g = g[g["date"] > last - pd.Timedelta(days=365)]
        days = (g["date"].max() - g["date"].min()).days
        if days < min_days:
            continue
        mean = g.groupby("depth")["temperature"].mean()
        rows += [{"borehole_id": bid, "depth": d, "temperature": t, "days": days} for d, t in mean.items()]
    return pd.DataFrame(rows)


def near_surface_temperature(profiles, top=10, bottom=20):
    """Mean annual temperature between `top` and `bottom` m depth, per borehole (NaN if no sensor there)."""
    sel = profiles[profiles["depth"].between(top, bottom)]
    return sel.groupby("borehole_id")["temperature"].mean()
