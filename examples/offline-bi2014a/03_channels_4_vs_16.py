#!/usr/bin/env python3
"""Step 3 - how much do you lose with four frontal electrodes instead of sixteen?

The question a consumer headband raises, answered by measurement: the same data,
the same epochs, the same classifiers, evaluated on all 16 channels and then on
the 4 frontal ones a forehead-only device would have.

    python3 03_channels_4_vs_16.py                # 4 subjects, ~215 MB, ~10-20 min
    python3 03_channels_4_vs_16.py --subjects 64  # the full run, hours

Evaluation is within-session, per subject: train and test never share a session,
so the score is what this pipeline would do on that person's unseen data.

results/ holds the full 64-subject run for comparison. A short run will be
noisier - 4 subjects is 8 scores per cell - but should land in the same place.

Adapted from res/eeg-benchmark/03_benchmark.py; the pipelines and paradigm are
unchanged so the numbers stay comparable.
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

import pandas as pd
from moabb.datasets import BI2014a
from moabb.evaluations import WithinSessionEvaluation
from moabb.paradigms import P300
from pyriemann.estimation import ERPCovariances, XdawnCovariances
from pyriemann.tangentspace import TangentSpace
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

CHANNEL_SETS = {
    "4ch_frontal": ["Fp1", "F3", "F4", "Fp2"],   # what a forehead band reaches
    "16ch_full": None,                            # every channel in the dataset
}
TMIN, TMAX, RESAMPLE = -0.2, 0.8, 128


def make_pipelines(n_channels):
    # xDAWN cannot ask for more spatial filters than there are channels
    nfilter = 2 if n_channels <= 4 else 4
    return {
        "ERPCov+LogReg": make_pipeline(
            ERPCovariances(estimator="lwf"),
            TangentSpace(),
            LogisticRegression(class_weight="balanced", max_iter=1000),
        ),
        "XdawnCov+LogReg": make_pipeline(
            XdawnCovariances(nfilter=nfilter),
            TangentSpace(),
            LogisticRegression(class_weight="balanced", max_iter=1000),
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subjects", type=int, default=4,
                    help="how many subjects to fetch and use (default 4, max 64)")
    ap.add_argument("--out", default="my_results",
                    help="directory for results.csv and summary.csv (default my_results)")
    args = ap.parse_args()

    dataset = BI2014a()
    dataset.subject_list = dataset.subject_list[: args.subjects]
    print(f"subjects: {len(dataset.subject_list)} -> {dataset.subject_list}")

    all_results = []
    for cond_name, channels in CHANNEL_SETS.items():
        n_ch = len(channels) if channels else 16
        paradigm = P300(channels=channels, tmin=TMIN, tmax=TMAX, resample=RESAMPLE)

        # BI2014a has one session per subject, so only within-session CV is possible.
        print(f"\n=== {cond_name} ({n_ch} channels) ===", flush=True)
        t0 = time.time()
        evaluation = WithinSessionEvaluation(
            paradigm=paradigm,
            datasets=[dataset],
            overwrite=True,
            error_score="raise",
            suffix=f"{cond_name}_n{args.subjects}",
            n_jobs=1,          # serial on purpose; this is not a machine to load up
        )
        try:
            results = evaluation.process(make_pipelines(n_ch))
        except Exception as e:
            print(f"FAILED {cond_name}: {e}", flush=True)
            continue
        results["channel_set"] = cond_name
        all_results.append(results)
        print(f"=== done in {time.time()-t0:.0f}s, {len(results)} scores ===", flush=True)

    if not all_results:
        raise SystemExit("no results - nothing to summarise")

    final = pd.concat(all_results, ignore_index=True)
    os.makedirs(args.out, exist_ok=True)
    final.to_csv(f"{args.out}/results.csv", index=False)
    summary = final.groupby(["channel_set", "pipeline"])["score"].agg(
        ["mean", "std", "count"])
    summary.to_csv(f"{args.out}/summary.csv")

    print("\nROC AUC, chance = 0.50\n")
    print(summary.to_string())
    print(f"\nwritten to {args.out}/")

    try:
        full = summary.xs("16ch_full")["mean"].mean()
        four = summary.xs("4ch_frontal")["mean"].mean()
        print(f"\n  16 channels  {full:.3f}")
        print(f"   4 frontal   {four:.3f}")
        print(f"   difference  {full-four:.3f} AUC")
        print("\ncompare against results/summary.csv (all 64 subjects): 0.846/0.831 at 16")
        print("channels, 0.659/0.650 at 4. landing ~0.05 away with a short run is normal -")
        print("the per-subject spread is about 0.10, far larger than any difference between")
        print("the pipelines.")
        if args.subjects < 16:
            print(f"\nwith {args.subjects} subjects you have {args.subjects*2} scores per cell, which is")
            print("enough to see the 16-vs-4 gap and NOT enough to compare the two pipelines")
            print("against each other. for that, see results/README.md - over 64 subjects they")
            print("separate at 16 channels and converge at 4, which says the limit with four")
            print("frontal electrodes is the electrodes rather than the algorithm.")
    except KeyError:
        pass


if __name__ == "__main__":
    main()
