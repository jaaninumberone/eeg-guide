#!/usr/bin/env python3
"""Compare a device description against a data file, and report the disagreements.

    python3 src/check_device.py docs/30-adapting/muse-4ch-consumer.md recording.csv

It reports; it does not stop you. Every line it prints is a statement about two things
that should agree and do not, and you are the one who decides which of them is wrong.

The reason this exists: almost nothing in an EEG file describes itself. The sample rate,
the units, the reference, and often the channel order all live outside it -- in a paper,
in a library, or in someone's memory. Writing them down is the first half of the job.
Checking that what you wrote matches what you have is the second, and it takes seconds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml

OK, WARN, BAD = "ok  ", "note", "MISMATCH"


def load_description(path: Path) -> dict:
    text = path.read_text()
    if not text.lstrip().startswith("---"):
        raise SystemExit(f"{path}: no YAML front matter found")
    return yaml.safe_load(text.split("---", 2)[1])


def load_data(path: Path, header_rows) -> tuple[np.ndarray, list[str] | None]:
    """Return (array, header names or None). Handles .csv and .mat."""
    if path.suffix.lower() == ".mat":
        from scipy.io import loadmat
        m = loadmat(path, squeeze_me=True)
        arrays = {k: v for k, v in m.items()
                  if not k.startswith("__") and getattr(v, "ndim", 0) == 2}
        if not arrays:
            raise SystemExit(f"{path}: no 2-D array inside; keys are {list(m)}")
        name, arr = sorted(arrays.items())[0]
        print(f"  (.mat variable {name!r})")
        return np.asarray(arr, float), None

    lines = [l for l in path.read_text(errors="replace").splitlines() if l.strip()]
    skip = header_rows if isinstance(header_rows, int) else 0
    names = None
    if skip:
        names = [c.strip() for c in lines[skip - 1].split(",")]
    body = lines[skip:]
    rows = [r.split(",") for r in body]
    width = min(len(r) for r in rows)
    arr = np.array([[float(v) if v.strip() not in ("", "NaN", "nan") else np.nan
                     for v in r[:width]] for r in rows])
    return arr, names


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("description")
    ap.add_argument("data")
    args = ap.parse_args(argv)

    d = load_description(Path(args.description))
    acq, fil, chan = d.get("acquisition", {}), d.get("file", {}), d.get("channels", {})

    print(f"description : {args.description}")
    print(f"data        : {args.data}")
    print(f"device      : {d.get('device')}\n")

    arr, names = load_data(Path(args.data), fil.get("header_rows"))
    findings: list[tuple[str, str]] = []

    def say(level, msg):
        findings.append((level, msg))
        print(f"  [{level}] {msg}")

    # ── shape ────────────────────────────────────────────────────────────────
    print(f"file has {arr.shape[0]:,} rows x {arr.shape[1]} columns")
    data_cols = fil.get("data_columns") or []
    n_declared = acq.get("n_channels")
    if isinstance(n_declared, int) and data_cols:
        if len(data_cols) != n_declared:
            say(BAD, f"n_channels says {n_declared} but data_columns lists "
                     f"{len(data_cols)}")
        else:
            say(OK, f"{n_declared} channels, {len(data_cols)} data columns")
    if data_cols and max(data_cols) >= arr.shape[1]:
        say(BAD, f"data_columns references column {max(data_cols)} but the file has "
                 f"only {arr.shape[1]}")

    # ── sample rate, from the time column ────────────────────────────────────
    tcol, tkind = fil.get("time_column"), fil.get("time_kind")
    declared_fs = acq.get("sample_rate_hz")
    if isinstance(tcol, int) and tkind in ("seconds", "milliseconds"):
        t = arr[:, tcol]
        step = float(np.median(np.diff(t)))
        scale = 1.0 if tkind == "seconds" else 1e-3
        observed = 1.0 / (step * scale) if step > 0 else float("nan")
        if isinstance(declared_fs, (int, float)):
            err = abs(observed - declared_fs) / declared_fs * 100
            if err > 1.0:
                say(BAD, f"sample_rate_hz says {declared_fs} but the time column "
                         f"implies {observed:.2f} Hz ({err:.1f}% out). Every frequency "
                         f"you compute is wrong by that much")
            else:
                say(OK, f"sample rate {declared_fs} Hz agrees with the time column "
                        f"({observed:.2f} Hz)")
        else:
            say(WARN, f"sample_rate_hz not declared; the file implies {observed:.2f} Hz")
    elif tkind == "sample_index":
        say(WARN, "time column is a bare sample index: it carries no timing, so the "
                  "declared rate cannot be checked and a dropped sample is invisible")
    else:
        say(WARN, "no usable time column; the declared rate cannot be checked")

    # ── units, from the amplitude the file actually contains ─────────────────
    if data_cols:
        sig = arr[:, data_cols]
        p95 = float(np.nanpercentile(np.abs(sig), 95))
        units = str(fil.get("units", "unknown")).lower()
        print(f"  signal p95 |amplitude| = {p95:,.1f}")
        if units == "microvolts":
            if p95 > 5000:
                say(WARN, f"declared microvolts, but p95 is {p95:,.0f}. Scalp EEG is "
                          f"tens to hundreds of uV. Possible causes: a gain not divided "
                          f"out, values in counts, or a carrier riding on the signal")
            elif p95 < 0.5:
                say(WARN, f"declared microvolts, but p95 is {p95:.3f}. These may be "
                          f"volts")
            else:
                say(OK, f"amplitude {p95:,.1f} is plausible for microvolts")
        elif units in ("unknown", "none", ""):
            say(WARN, f"units not declared; p95 amplitude is {p95:,.1f}")

    # ── headers versus declared positions ────────────────────────────────────
    labels, positions = chan.get("labels") or [], chan.get("positions") or []
    if names and data_cols:
        in_file = [names[c] for c in data_cols if c < len(names)]
        if labels and [l.lower() for l in labels] != [n.lower() for n in in_file]:
            say(BAD, f"labels say {labels} but the header reads {in_file}")
        elif labels:
            say(OK, f"header matches declared labels: {in_file}")
    if labels and positions and labels != positions:
        say(WARN, f"labels and positions differ ({labels} vs {positions}). That is "
                  f"allowed and it is why they are separate lists -- select channels "
                  f"by POSITION, never by matching a name")
    if not labels and not names:
        say(WARN, "the file has no header and no labels are declared: nothing in or "
                  "beside this file says which column is which electrode")

    # ── markers ──────────────────────────────────────────────────────────────
    for c in fil.get("marker_columns") or []:
        if c >= arr.shape[1]:
            say(BAD, f"marker_columns references column {c}, beyond the file")
            continue
        col = arr[:, c]
        vals = np.unique(col[~np.isnan(col)])
        n_events = int(np.count_nonzero(col[~np.isnan(col)]))
        if n_events == 0:
            say(WARN, f"marker column {c} contains no events in this file")
        else:
            say(OK, f"marker column {c}: {n_events:,} events, values "
                    f"{vals[:6].tolist()}")

    # ── impedance carrier, if one is claimed ─────────────────────────────────
    imp = d.get("impedance", {})
    if imp.get("measured") is True and isinstance(declared_fs, (int, float)) and data_cols:
        rule = str(imp.get("carrier_rule", ""))
        try:
            expected = eval(rule.replace("sample_rate", str(declared_fs)),  # noqa: S307
                            {"__builtins__": {}}, {})
        except Exception:  # noqa: BLE001
            expected = None
        if expected:
            x = arr[: int(declared_fs) * 8, data_cols[0]]
            x = x[~np.isnan(x)]
            if len(x) > 64:
                f = np.fft.rfftfreq(len(x), 1 / declared_fs)
                P = np.abs(np.fft.rfft(x - x.mean()))
                near = P[(f > expected - 2) & (f < expected + 2)]
                ratio = near.max() / np.median(P) if len(near) else 0
                if ratio > 10:
                    say(OK, f"carrier found near {expected:.1f} Hz "
                            f"({ratio:.0f}x the median bin)")
                else:
                    say(BAD, f"impedance.measured is true and carrier_rule gives "
                             f"{expected:.1f} Hz, but nothing stands out there")

    # ── derived columns ──────────────────────────────────────────────────────
    if fil.get("derived_columns") is True:
        say(WARN, "this file carries columns someone else already computed. Their "
                  "filter choices are not recorded and cannot be undone -- use only "
                  "the raw columns for your own processing")

    bad = sum(1 for lvl, _ in findings if lvl == BAD)
    notes = sum(1 for lvl, _ in findings if lvl == WARN)
    print(f"\n{bad} mismatch(es), {notes} note(s).")
    if bad:
        print("A mismatch means the description and the file disagree. Decide which is "
              "wrong before you process anything -- do not adjust one to silence this.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
