#!/usr/bin/env python3
"""Step 2 - markers to epochs to a classifier, on real downloaded data.

Downloads BI2014a subject by subject via MOABB (Zenodo record 3266223) and shows
the middle of the pipeline explicitly: how many epochs of each class come out,
what one looks like, and whether a target can be told from a non-target.

    python3 02_epoch_and_score.py                # 2 subjects, ~110 MB, a few minutes
    python3 02_epoch_and_score.py --subjects 8   # more data, proportionally longer

Downloads land in ~/mne_data and are reused. Subject zips are 30-60 MB each.
"""
# --- keep this ABOVE the numpy/sklearn imports -------------------------------
# n_jobs=1 controls how many PROCESSES scikit-learn forks. It does nothing about
# the threads that OpenBLAS/MKL spawn inside every matrix operation, which
# default to one per core. On a 16-core laptop that is a load average of ~14 from
# a script that looks single-threaded, and it is enough to brown out a machine
# with marginal power delivery. These variables are only read at import time, so
# they have to be set before numpy is loaded.
import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "2")
# raise these if your machine is happy being loaded; the results do not change.
# -----------------------------------------------------------------------------

import argparse
import time
from pathlib import Path

import numpy as np
import yaml
from moabb.datasets import BI2014a
from moabb.paradigms import P300
from pyriemann.estimation import ERPCovariances
from pyriemann.tangentspace import TangentSpace
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline

# same epoching as 03_channels_4_vs_16.py, so the numbers are comparable
TMIN, TMAX, RESAMPLE = -0.2, 0.8, 128

DESCRIPTION = (Path(__file__).resolve().parents[2]
               / "docs/30-adapting/bi2014a-16ch-dry.md")


def channel_positions():
    """Where the electrodes sat - which is in the device description, not the data.

    This is the whole point of docs/30-adapting/: the array MOABB hands back has
    16 rows and no idea what any of them is.
    """
    text = DESCRIPTION.read_text()
    meta = yaml.safe_load(text.split("---", 2)[1])
    return meta.get("channels", {}).get("positions") or []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subjects", type=int, default=2,
                    help="how many subjects to fetch and use (default 2, max 64)")
    args = ap.parse_args()

    dataset = BI2014a()
    dataset.subject_list = dataset.subject_list[: args.subjects]
    print(f"subjects: {dataset.subject_list}")

    paradigm = P300(tmin=TMIN, tmax=TMAX, resample=RESAMPLE)

    t0 = time.time()
    print("\nfetching and epoching (first run downloads; later runs are cached)...")
    X, y, meta = paradigm.get_data(dataset=dataset)
    print(f"done in {time.time() - t0:.0f}s")

    # --- what epoching produced -------------------------------------------
    n_ep, n_ch, n_t = X.shape
    print(f"\nepochs         {n_ep}")
    print(f"channels       {n_ch}")
    print(f"samples/epoch  {n_t}  ({TMIN}s to {TMAX}s at {RESAMPLE} Hz)")
    classes, counts = np.unique(y, return_counts=True)
    for c, n in zip(classes, counts):
        print(f"  {c:<12} {n:5d}  ({n/n_ep:.1%})")
    print("\nthe class imbalance IS the paradigm: rare targets among frequent non-targets.")
    print("it is also why accuracy is the wrong score here - always guessing the majority")
    print("class would score ~80%. the metric below is ROC AUC, where chance is 0.50.")

    # --- the averaged evoked difference -----------------------------------
    tgt = X[y == "Target"].mean(axis=0)
    ntg = X[y == "NonTarget"].mean(axis=0)
    diff = tgt - ntg
    t = np.linspace(TMIN, TMAX, n_t)
    win = (t >= 0.25) & (t <= 0.50)          # where a P300 is expected
    peak_ch = np.abs(diff[:, win]).max(axis=1).argmax()
    peak_t = t[win][np.abs(diff[peak_ch, win]).argmax()]
    # MOABB returns the array already scaled to microvolts.
    amp = diff[peak_ch, win][np.abs(diff[peak_ch, win]).argmax()]
    pos = channel_positions()
    ch_name = pos[peak_ch] if peak_ch < len(pos) else f"index {peak_ch}"
    print(f"\nlargest target/non-target difference in 250-500 ms:")
    print(f"  channel {ch_name}, at {peak_t*1000:.0f} ms, {amp:+.2f} uV")
    print("  a positive deflection a few uV in size, 250-500 ms after a rare stimulus,")
    print("  is what 'a P300' means. finding it here is a sanity check on the markers:")
    print("  if their timing were wrong, this would be smeared away and would not appear.")
    print(f"\n  ('{ch_name}' came from docs/30-adapting/bi2014a-16ch-dry.md, not from the")
    print("   data. the array above is 16 anonymous rows. without that file this line")
    print("   would read 'channel index 4', which tells you nothing about the head.)")

    # --- does it classify? -------------------------------------------------
    clf = make_pipeline(
        ERPCovariances(estimator="lwf"),
        TangentSpace(),
        LogisticRegression(class_weight="balanced", max_iter=1000),
    )
    print("\n5-fold cross-validation, pooled across subjects...")
    t0 = time.time()
    scores = cross_val_score(
        clf, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0),
        scoring="roc_auc", n_jobs=1,
    )
    print(f"  ROC AUC {scores.mean():.3f} +/- {scores.std():.3f}   ({time.time()-t0:.0f}s)")
    print("\nNOTE: this pools every subject into one pool, so a fold can train on one")
    print("recording and test on another from the same person. that inflates the score.")
    print("03_channels_4_vs_16.py evaluates per session per subject, which is the honest")
    print("comparison - expect its numbers to be lower than this one.")


if __name__ == "__main__":
    main()
