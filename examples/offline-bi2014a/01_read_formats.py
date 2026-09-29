#!/usr/bin/env python3
"""Step 1 - what is actually in an EEG file.

Runs on the committed excerpts in sample/, so it needs no download and only
numpy + scipy + pandas. It answers three questions the files themselves do not:

  * is the .csv the same data as the .mat, and if not, by how much?
  * what do the marker columns contain?
  * what does a file with a header give you that a headerless one does not?

    python3 01_read_formats.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

SAMPLE = Path(__file__).resolve().parent / "sample"
FS = 512.0  # BI2014a; stated in docs/30-adapting/bi2014a-16ch-dry.md, not in the file


def rule(title):
    print(f"\n{title}\n" + "-" * len(title))


def compare_formats():
    rule("1. The same 20 seconds, in .mat and in .csv")
    mat_p = SAMPLE / "bi2014a_subject01_excerpt.mat"
    csv_p = SAMPLE / "bi2014a_subject01_excerpt.csv"

    mat = sio.loadmat(mat_p)["samples"]
    csv = pd.read_csv(csv_p, header=None).values

    print(f"  .mat  {mat.shape}  {mat.dtype}  {mat_p.stat().st_size/1e3:8.0f} kB")
    print(f"  .csv  {csv.shape}  {csv.dtype}  {csv_p.stat().st_size/1e3:8.0f} kB")
    print(f"  the text copy is {csv_p.stat().st_size/mat_p.stat().st_size:.2f}x the size")
    print("  (this .mat is compressed, as the dataset's own files are. an uncompressed")
    print("   .mat of the same array would be 1,557 kB - bigger than the text. 'binary is")
    print("   smaller' is a property of the encoder, not of being binary.)")

    if mat.shape != csv.shape:
        sys.exit("shapes differ - the excerpts are not the same rows")

    eeg_m, eeg_c = mat[:, 1:17], csv[:, 1:17]
    err = np.abs(eeg_m - eeg_c)
    nz = eeg_m != 0
    rel = err[nz] / np.abs(eeg_m[nz])

    print("\n  they are NOT identical: the .csv is rounded to 5 significant figures")
    print(f"    median relative error   {np.median(rel):.1e}")
    print(f"    median absolute error   {np.median(err):.4f} uV")
    print(f"    largest absolute error  {err.max():.4f} uV", end="")
    i = np.unravel_index(err.argmax(), err.shape)
    print(f"   (at a sample of {eeg_m[i]:,.0f} uV)")
    print(f"    95th pct |amplitude|    {np.percentile(np.abs(eeg_m), 95):,.0f} uV")
    print(f"    marker columns          {'identical' if np.array_equal(mat[:, 17:], csv[:, 17:]) else 'DIFFER'}")

    ratio = np.percentile(np.abs(eeg_m), 95) / max(np.median(err), 1e-12)
    print(f"\n  the error is ~{ratio:,.0f}x smaller than the signal, so it cannot")
    print("  affect a result here. that is a fact about this data, not about rounding.")
    print("  note the largest error lands on the largest sample: rounding to significant")
    print("  figures holds RELATIVE error constant, so absolute error scales with amplitude.")
    return mat


def read_markers(mat):
    rule("2. The marker columns - which are the experiment")
    for col in (17, 18):
        v, n = np.unique(mat[:, col], return_counts=True)
        keep = v != 0
        events = ", ".join(f"{int(a)}x{b}" for a, b in zip(v[keep], n[keep]))
        print(f"  column {col}: {int(n[keep].sum()):4d} events   {events or '(none)'}")
    print("\n  column 18 is the oddball code: 1 = non-target, 2 = target.")
    print("  column 17 identifies WHICH item flashed, and standard tooling ignores it.")
    print("  nothing in the file says any of this.")


def read_headed():
    rule("3. A file with a header, and what it still does not tell you")
    df = pd.read_csv(SAMPLE / "muse_raw_excerpt.csv")
    print(f"  columns: {list(df.columns)}")
    t = df["timestamps"].values
    dt = np.median(np.diff(t))
    print(f"\n  named channels - a real improvement over 19 anonymous columns.")
    print(f"  rate derived from the time column: {1/dt:.1f} Hz (median dt = {dt:.4f} s)")
    print("  the dataset description for this recording says 256 Hz. the file says 250.")
    print("  one of them is wrong and the file cannot tell you which.")
    p95 = np.nanpercentile(np.abs(df[["TP9", "AF7", "AF8", "TP10"]].values), 95)
    print(f"\n  95th pct |amplitude| = {p95:.1f} - consistent with microvolts, but the")
    print("  file never states its units. that inference is yours, and it can be wrong.")
    mk = df["Marker0"].dropna()
    vals = sorted(float(v) for v in set(mk.unique()))
    print(f"\n  Marker0 is non-empty in {len(mk)} of {len(df)} rows, and every one of those")
    print(f"  holds {vals} - so there are no events at all in this excerpt. a marker column")
    print("  that exists is not a marker column that contains anything, and a script that")
    print("  epochs on it would produce zero epochs and no error.")


def read_derived():
    rule("4. A file where the processing already happened")
    df = pd.read_csv(SAMPLE / "mindmonitor_excerpt.csv")
    band = [c for c in df.columns if c.split("_")[0] in
            ("Delta", "Theta", "Alpha", "Beta", "Gamma")]
    raw = [c for c in df.columns if c.startswith("RAW_")]
    print(f"  {len(df.columns)} columns: {len(band)} band powers, {len(raw)} raw channels,"
          f" {len(df.columns)-len(band)-len(raw)} other")
    print(f"  band-power columns: {', '.join(band[:4])}, ... ({len(band)} total)")
    print("\n  half this file is already-computed band power. you cannot recover the raw")
    print("  signal from it, you cannot re-filter it, and you cannot check how it was")
    print("  computed. if you want to do your own processing, use the RAW_ columns only -")
    print("  and note there are just four of them.")


if __name__ == "__main__":
    if not SAMPLE.exists():
        sys.exit(f"no sample directory at {SAMPLE}")
    print(__doc__.strip().splitlines()[0])
    mat = compare_formats()
    read_markers(mat)
    read_headed()
    read_derived()
    rule("So")
    print("  none of these files states its own sample rate, units, channel positions or")
    print("  what its markers mean. that is normal. write it down alongside the data:")
    print("  see docs/30-adapting/ for one description per device, and a script that")
    print("  checks a description against a real recording.")
