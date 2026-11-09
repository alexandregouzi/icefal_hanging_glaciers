"""Layer to check the top-ranked candidate hanging glaciers on the imagery in QGIS.

The candidates outside the mapping blocks were never checked by eye. This writes
candidates_review.gpkg to the QGIS kit folder:
    to_check     the 20 best-ranked candidates, plus the candidates that touch a mapping block but are not
                 mapped at all; empty `verdict` (hanging / not_hanging / unsure) and `notes` fields
    candidates   all candidates, for context

Input: data/processed/candidates.gpkg (notebooks/05_candidates.ipynb).
An existing review file is never overwritten, since it holds the verdicts.

With --random N, a random sample of N further candidates outside the mapping blocks is appended to
`to_check` of an existing review file (fixed seed). Unlike the top 20, this sample is representative of
all the candidates found outside the blocks, so the share judged hanging estimates the precision of the
model outside its training area.

Usage (from the project root):
    python src/prepare_candidate_review.py /mnt/c/Users/<user>/icefal_qgis
    python src/prepare_candidate_review.py /mnt/c/Users/<user>/icefal_qgis --random 25
"""

import subprocess
import sys
from pathlib import Path

import geopandas as gpd

import qgis_styles
from config import PROCESSED
from prepare_mapping_kit import add_default_style

TOP = 20
SEED = 0


def main(out_dir):
    out = out_dir / "candidates_review.gpkg"
    if out.exists():
        sys.exit(f"{out} already exists (it may hold your verdicts): not overwritten.")
    cand = gpd.read_file(PROCESSED / "candidates.gpkg", layer="candidates")
    cols = ["rank", "candidate_id", "glacier", "sgi_id", "area_ha", "slope_mean", "fall_height", "z_min", "z_max",
            "geometric_index", "in_block", "mapped_share", "geometry"]
    cand = cand[cols].sort_values("rank")

    unmapped_in_block = cand["in_block"] & (cand["mapped_share"] == 0)
    to_check = cand[(cand["rank"] <= TOP) | unmapped_in_block].copy()
    to_check["reason"] = ["top 20" if r <= TOP else "in a block, not mapped" for r in to_check["rank"]]
    to_check["verdict"] = None
    to_check["notes"] = None

    to_check.to_file(out, layer="to_check", driver="GPKG")
    cand.to_file(out, layer="candidates", driver="GPKG")
    add_default_style(out, "to_check", "geometry", qgis_styles.candidates_to_check_qml())
    add_default_style(out, "candidates", "geometry", qgis_styles.candidates_qml())
    print(f"{out}: {len(to_check)} candidates to check "
          f"({(to_check['reason'] == 'top 20').sum()} top 20, {unmapped_in_block.sum()} in a block but not mapped), "
          f"{len(cand)} candidates in total")
    print(to_check.drop(columns="geometry")[["rank", "candidate_id", "glacier", "area_ha", "in_block", "reason"]]
          .to_string(index=False))


def add_random_sample(out_dir, n):
    out = out_dir / "candidates_review.gpkg"
    if any(out.with_name(out.name + s).exists() for s in ("-wal", "-shm")):
        sys.exit(f"{out} is open in QGIS: close QGIS and run again.")
    cand = gpd.read_file(out, layer="candidates")
    to_check = gpd.read_file(out, layer="to_check")
    pool = cand[~cand["in_block"] & ~cand["candidate_id"].isin(to_check["candidate_id"])]
    sample = pool.sample(n=min(n, len(pool)), random_state=SEED).sort_values("rank").copy()
    sample["reason"] = "random sample"
    sample["verdict"] = None
    sample["notes"] = None
    tmp = out_dir / "random_sample_tmp.gpkg"
    sample.to_file(tmp, layer="to_check", driver="GPKG")
    subprocess.run(["ogr2ogr", "-append", "-update", str(out), str(tmp), "to_check", "-nln", "to_check"], check=True)
    tmp.unlink()
    print(f"appended {len(sample)} randomly drawn candidates outside the blocks (seed {SEED}, "
          f"out of {len(pool)} not yet checked); ranks: {sample['rank'].tolist()}")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[2] == "--random":
        add_random_sample(Path(sys.argv[1]), int(sys.argv[3]))
    elif len(sys.argv) == 2:
        main(Path(sys.argv[1]))
    else:
        sys.exit(__doc__)
