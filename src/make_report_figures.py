"""Figures of the report, in the format of glaciology journals (18 cm wide, 8 pt text, panel letters).

    fig1_study_area.pdf/png   (a) study area and mapping blocks, (b) manual mapping in block 4
    fig2_validation.pdf/png   (a) precision–recall curves, (b) out-of-fold errors in block 4
    fig3_candidates.pdf/png   candidate hanging glaciers and geometric index

Inputs: outputs of prepare_features.py and notebooks 03–05. The cross-validation on the revised labels
(notebook 04) is run again here (same forest, same folds, fixed seed), which takes a few minutes.

Usage (from the project root):
    python src/make_report_figures.py
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from sklearn.metrics import average_precision_score, precision_recall_curve

from classifier import EXCLUDED_VARIABLES, cross_validate, load_grids
from config import CRS, DEM_RES, PROCESSED, RAW, ROOT
from relief import hillshade

FIG = ROOT / "figures"
MM = 1 / 25.4
FULL_WIDTH = 180 * MM

# Colours (checked for colour-blind readers with the dataviz palette validator)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, GREY = "#0b0b0b", "#52514e"
OUTLINE = "#3b3b3b"
INDEX_RAMP = ["#9ec5f4", "#5598e7", "#256abf", "#0d366b"]   # one hue, light to dark (geometric index quartiles)
ZOOM_BLOCK = 4

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.edgecolor": INK, "savefig.dpi": 300,
    "pdf.fonttype": 42,
})


# ---------------------------------------------------------------- map helpers

def km_axes(ax):
    """LV95 coordinates in km on the axes."""
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1000:.0f}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1000:.0f}"))
    ax.set_xlabel("Easting (km, LV95)")
    ax.set_ylabel("Northing (km, LV95)")


def scale_bar(ax, length_km, loc=(0.04, 0.05)):
    """Black and white scale bar in the lower-left corner (map units: m)."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x0 + loc[0] * (x1 - x0)
    y = y0 + loc[1] * (y1 - y0)
    h = 0.012 * (y1 - y0)
    half = length_km * 500
    ax.add_patch(Rectangle((x, y), half, h, fc=INK, ec=INK, lw=0.5, zorder=10))
    ax.add_patch(Rectangle((x + half, y), half, h, fc="white", ec=INK, lw=0.5, zorder=10))
    for dx, label in [(0, "0"), (2 * half, f"{length_km} km")]:
        ax.text(x + dx, y + 2 * h, label, ha="center", va="bottom", fontsize=6.5, zorder=10,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.3))


def north_arrow(ax, loc=(0.95, 0.88)):
    ax.annotate("N", xy=(loc[0], loc[1] + 0.08), xytext=loc, xycoords="axes fraction", ha="center", va="center",
                fontsize=8, fontweight="bold", zorder=10,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.8))


def panel_letter(ax, letter):
    ax.text(0.01, 0.99, f"({letter})", transform=ax.transAxes, ha="left", va="top", fontsize=9, fontweight="bold",
            zorder=11, bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5))


def show_hillshade(ax, shade, transform, window=None):
    rows, cols = shade.shape
    x0, y1 = transform * (0, 0)
    x1, y0 = transform * (cols, rows)
    ax.set_facecolor("#9a9a9a")   # no-data cells of the DEM
    ax.imshow(shade, cmap="gray", vmin=-0.3, vmax=1.1, extent=(x0, x1, y0, y1), interpolation="bilinear", zorder=0)
    if window:
        ax.set_xlim(window[0], window[2])
        ax.set_ylim(window[1], window[3])
    else:
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
    ax.set_aspect("equal")


def window_of(d, block_id):
    return d["blocks"].set_index("block_id").loc[block_id].geometry.bounds


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"figures/{name}.png and .pdf")


# ---------------------------------------------------------------- data

def load():
    with rasterio.open(PROCESSED / f"dem_{DEM_RES}m.tif") as src:
        dem = src.read(1)
        transform = src.transform
    d = {
        "dem": dem,
        "transform": transform,
        "shade": hillshade(dem, DEM_RES),
        "glaciers": gpd.read_file(PROCESSED / "sgi2023_zone.gpkg", layer="glaciers"),
        "blocks": gpd.read_file(RAW / "manual_mapping.gpkg", layer="blocks"),
        "polygons": gpd.read_file(RAW / "manual_mapping.gpkg", layer="hanging_glaciers"),
        "candidates": gpd.read_file(PROCESSED / "candidates.gpkg", layer="candidates"),
    }
    b = pd.read_csv(RAW / "glenglat" / "data" / "borehole.csv")
    b = b[b["glacier_name"].isin(["Alphubel South", "Chessjengletscher"])]
    d["boreholes"] = gpd.GeoDataFrame(b, geometry=gpd.points_from_xy(b["longitude"], b["latitude"]),
                                      crs=4326).to_crs(CRS)
    return d


# ---------------------------------------------------------------- figure 1

def figure_study_area(d):
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(FULL_WIDTH, 0.47 * FULL_WIDTH),
                                     gridspec_kw={"width_ratios": [1.48, 1]})

    show_hillshade(ax_a, d["shade"], d["transform"])
    d["glaciers"].plot(ax=ax_a, facecolor="#d6e6f7", edgecolor=BLUE, lw=0.3, alpha=0.9, zorder=1)
    d["blocks"].boundary.plot(ax=ax_a, color=INK, lw=1.0, zorder=3)
    for _, blk in d["blocks"].iterrows():
        x0, _, _, y1 = blk.geometry.bounds
        ax_a.text(x0 + 200, y1 - 250, str(blk["block_id"]), ha="left", va="top", fontsize=8, fontweight="bold",
                  zorder=4, bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.8))
    d["boreholes"].plot(ax=ax_a, marker="^", color=ORANGE, markersize=14, edgecolor=INK, linewidth=0.4, zorder=5)
    km_axes(ax_a)
    scale_bar(ax_a, 5, loc=(0.13, 0.92))
    north_arrow(ax_a)
    panel_letter(ax_a, "a")
    ax_a.add_patch(Rectangle(window_of(d, ZOOM_BLOCK)[:2], 5000, 5000, fc="none", ec=ORANGE, lw=1.4, zorder=4))
    ax_a.legend(handles=[Patch(fc="#d6e6f7", ec=BLUE, lw=0.5, label="SGI2023 glacier"),
                         Patch(fc="none", ec=INK, lw=1.0, label="Mapping block"),
                         Patch(fc="none", ec=ORANGE, lw=1.4, label="Extent of (b)"),
                         Line2D([], [], marker="^", ls="", color=ORANGE, mec=INK, mew=0.4, ms=5, label="Borehole")],
                loc="lower right", frameon=True, framealpha=0.9, edgecolor="none")

    blk = d["blocks"].set_index("block_id").loc[ZOOM_BLOCK]
    window = blk.geometry.bounds
    show_hillshade(ax_b, d["shade"], d["transform"], window)
    d["glaciers"].plot(ax=ax_b, facecolor="none", edgecolor=BLUE, lw=0.5, zorder=1)
    p = d["polygons"]
    p[p["source"] == "initial"].plot(ax=ax_b, facecolor=BLUE, alpha=0.55, edgecolor=BLUE, lw=0.6, zorder=2)
    p[p["source"] == "review"].plot(ax=ax_b, facecolor=ORANGE, alpha=0.55, edgecolor=ORANGE, lw=0.6, zorder=2)
    km_axes(ax_b)
    ax_b.set_ylabel("")
    scale_bar(ax_b, 1)
    panel_letter(ax_b, "b")
    ax_b.legend(handles=[Patch(fc=BLUE, alpha=0.55, label="Hanging glacier, blind mapping"),
                         Patch(fc=ORANGE, alpha=0.55, label="Added after review"),
                         Patch(fc="none", ec=BLUE, lw=0.5, label="SGI2023 outline")],
                loc="lower right", frameon=True, framealpha=0.9, edgecolor="none")
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig1_study_area")


# ---------------------------------------------------------------- figure 2

def figure_validation(d, grids):
    features, names, labels, _ = grids
    train = (labels["glacier"] > 0) & (labels["block"] > 0)
    use = [names.index(n) for n in names if n not in EXCLUDED_VARIABLES]
    X = features[use][:, train].T
    b = labels["block"][train]
    y_init = labels["hanging"][train]
    y_rev = labels["hanging_revised"][train]
    keep = labels["excluded"][train] == 0
    with rasterio.open(PROCESSED / f"oof_probability_{DEM_RES}m.tif") as src:
        p_init = src.read(1)[train]
    print("running the cross-validation on the revised labels...")
    p_rev, _ = cross_validate(X[keep], y_rev[keep], b[keep])

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(FULL_WIDTH, 0.6 * FULL_WIDTH),
                                     gridspec_kw={"width_ratios": [1, 1.05]})
    curves = [
        ("Blind labels", y_init, p_init, INK, "-", 1.4),
        ("Revised labels, same predictions", y_rev[keep], p_init[keep], BLUE, "--", 1.2),
        ("Revised labels, retrained", y_rev[keep], p_rev, ORANGE, "-", 1.4),
        ("Slope only, blind labels", y_init, X[:, [names[i] for i in use].index("slope")], GREY, ":", 1.0),
        ("Step height only, blind labels", y_init, X[:, [names[i] for i in use].index("step_height")], GREY, "-.", 1.0),
    ]
    for label, yy, pp, col, ls, lw in curves:
        pr, rc, _ = precision_recall_curve(yy, pp)
        ax_a.plot(rc, pr, ls, color=col, lw=lw, label=f"{label} (AP = {average_precision_score(yy, pp):.2f})")
    ax_a.axhline(y_init.mean(), color=GREY, lw=0.6)
    ax_a.text(0.02, y_init.mean() + 0.015, "Random classifier", ha="left", va="bottom", fontsize=6.5, color=GREY)
    ax_a.set(xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1))
    ax_a.spines[["top", "right"]].set_visible(False)
    ax_a.legend(loc="upper left", bbox_to_anchor=(0, -0.13), frameon=False, handlelength=2.2)
    panel_letter(ax_a, "a")
    ax_a.set_box_aspect(1)

    # Out-of-fold errors (revised labels) in the zoom block
    P = np.full(labels["glacier"].size, np.nan)
    P[np.flatnonzero(train)[keep]] = p_rev
    P = P.reshape(labels["glacier"].shape)
    hang = labels["hanging_revised"] == 1
    pred = P >= 0.5
    known = ~np.isnan(P)
    cls = np.full(P.shape, np.nan)
    cls[known & hang & pred] = 0
    cls[known & hang & ~pred] = 1
    cls[known & ~hang & pred] = 2
    blk = d["blocks"].set_index("block_id").loc[ZOOM_BLOCK]
    window = blk.geometry.bounds
    show_hillshade(ax_b, d["shade"], d["transform"], window)
    d["glaciers"].plot(ax=ax_b, facecolor="#d6e6f7", edgecolor=BLUE, lw=0.4, alpha=0.6, zorder=1)
    rows, cols = P.shape
    x0, y1 = d["transform"] * (0, 0)
    x1, y0 = d["transform"] * (cols, rows)
    ax_b.imshow(cls, cmap=ListedColormap([BLUE, ORANGE, AQUA]), vmin=-0.5, vmax=2.5, extent=(x0, x1, y0, y1),
                interpolation="nearest", zorder=2)
    ax_b.set_xlim(window[0], window[2])
    ax_b.set_ylim(window[1], window[3])
    km_axes(ax_b)
    scale_bar(ax_b, 1)
    panel_letter(ax_b, "b")
    ax_b.legend(handles=[Patch(fc=BLUE, label="Hanging, detected"), Patch(fc=ORANGE, label="Hanging, missed"),
                         Patch(fc=AQUA, label="False alarm"), Patch(fc="#d6e6f7", ec=BLUE, lw=0.4, label="Other glacier ice")],
                loc="lower right", frameon=True, framealpha=0.9, edgecolor="none")
    fig.tight_layout(w_pad=1.5)
    save(fig, "fig2_validation")


# ---------------------------------------------------------------- figure 3

def figure_candidates(d):
    c = d["candidates"].copy()
    c["class"] = pd.qcut(c["geometric_index"], 4, labels=False)
    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 0.66 * FULL_WIDTH))
    show_hillshade(ax, d["shade"], d["transform"])
    d["glaciers"].plot(ax=ax, facecolor="#eef3f9", edgecolor="#8aa9cc", lw=0.3, alpha=0.8, zorder=1)
    d["blocks"].boundary.plot(ax=ax, color=INK, lw=0.7, ls="--", zorder=2)
    for k, colour in enumerate(INDEX_RAMP):
        sub = c[c["class"] == k]
        sub.plot(ax=ax, facecolor=colour, edgecolor=colour, lw=0.6, zorder=3 + k)
    top = c.nsmallest(10, "rank")
    for _, row in top.iterrows():
        pt = row.geometry.representative_point()
        ax.annotate(str(row["rank"]), (pt.x, pt.y), xytext=(5, 5), textcoords="offset points", fontsize=6.5,
                    fontweight="bold", zorder=10, arrowprops=dict(arrowstyle="-", lw=0.4, color=INK),
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.4))
    km_axes(ax)
    scale_bar(ax, 5, loc=(0.04, 0.93))
    north_arrow(ax)
    q = c["geometric_index"].quantile([0, 0.25, 0.5, 0.75, 1]).round(2).to_numpy()
    handles = [Patch(fc=col, ec=col, label=f"{q[k]:.2f}–{q[k + 1]:.2f}") for k, col in enumerate(INDEX_RAMP)][::-1]
    handles += [Patch(fc="none", ec=INK, ls="--", lw=0.7, label="Mapping block")]
    ax.legend(handles=handles, title="Geometric index", loc="lower right", frameon=True, framealpha=0.9,
              edgecolor="none", title_fontsize=7)
    fig.tight_layout()
    save(fig, "fig3_candidates")


def main():
    d = load()
    figure_study_area(d)
    figure_candidates(d)
    figure_validation(d, load_grids())


if __name__ == "__main__":
    main()
