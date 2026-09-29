---
title: "Offline processing"
description: Files, formats, precision, metadata and epochs — the recipe behind the worked example.
---

# Offline processing

Offline you have a file and all the time in the world. That changes what is hard: not
latency, but **knowing what the file actually contains** and being able to get the same
answer again next month.

This page explains. The worked example demonstrates, on a public dataset you can download
yourself: [`examples/offline-bi2014a/`](../../examples/offline-bi2014a/).

## Text or binary

The two formats you will meet most are CSV and MATLAB `.mat`. They are not interchangeable
in the way people assume, and the BI2014a dataset is a good place to see why, because it
ships **the same recording in both**.

Subject 01, measured rather than quoted:

| | `.csv` | `.mat` |
| --- | --- | --- |
| size | 53.8 MB | 38.5 MB |
| contents | 417,925 × 19 | 417,925 × 19 |
| numbers | text, rounded | float64, exact |
| readable without tools | yes | no |
| appendable | yes | no |

The CSV is **40% larger and less exact**. That is the normal trade: text costs space and
precision, and buys you the ability to open it in anything, append to it while recording,
and read it in ten years without the library that wrote it.

One caveat on the size, because it is easy to over-learn. That `.mat` is *compressed*; the
same array written uncompressed is 63.5 MB, which is **larger** than the text file. Binary
is not inherently smaller — compression is doing the work, and a compressed text file
would claw most of it back. What binary reliably buys is exactness and fast structured
reads, not bytes.

## Precision, and how much of it matters

The CSV in that dataset is a copy of the `.mat` rounded to five significant figures. So
the two files disagree, and the interesting question is by how much:

```
median relative error   6.6e-06
median absolute error   0.0034 µV
largest absolute error  0.497 µV   (at a 10,232 µV excursion)
trigger columns         bit-identical
```

Against EEG whose 95th-percentile amplitude in this raw, unfiltered recording is about
3,800 µV, an error of 0.003 µV is **six orders of magnitude down**. It cannot affect any
result. Note also that the largest absolute error occurs at the largest sample — rounding
to *significant figures* keeps relative error constant, so absolute error scales with
amplitude, and the worst case lands on an artefact you would reject anyway.

The honest conclusion is narrow: **the rounding is harmless here**, which is a different
statement from *rounding is harmless*. The margin is enormous, so you do not need to think
about it — but you got that reassurance by measuring it on this data, not by assuming it.
[`01_read_formats.py`](../../examples/offline-bi2014a/01_read_formats.py) in the example
computes exactly this table so you can see it happen.

The practical advice, then, is not "always use binary". It is: know which of your files is
the original. A rounded copy is fine to analyse and wrong to treat as the archive.

## The real problem: the file does not describe itself

Open the BI2014a CSV and you get 19 columns of numbers and **no header at all**. Nothing
in it tells you:

- that the rate is 512 Hz;
- that column 0 is time in seconds and columns 1–16 are EEG in microvolts;
- that the channel order is `Fp1, Fp2, F3, AFz, F4, T7, Cz, T8, P7, P3, Pz, P4, P8, O1,
  Oz, O2`;
- that there are **two** marker columns rather than one, carrying different information.
  In subject 01, column 18 holds 1 for a non-target flash (990 of them) and 2 for a target
  (198) — the 1:5 ratio that makes this an oddball experiment. Column 17 holds a richer
  code in structured bands (20–25, 40–45, 60–65, 80–85, 100–106; 1,418 events), which
  identifies *which* item flashed, not merely whether it was the target. Standard tooling
  reads only column 18, so most analyses of this dataset silently discard column 17.

Every one of those facts lives in a paper, a README, or somebody's memory. This is not a
flaw in this dataset in particular; it is the normal condition of EEG data.

The answer is not to be careful. It is to write the facts down in a form that can be
**checked against the file**, which is what [`../30-adapting/`](../30-adapting/) is for:
one description per device, and a script that reads a description and a recording and
reports where they disagree.

```bash
python3 src/check_device.py docs/30-adapting/muse-4ch-consumer.md path/to/recording.csv
```

It derives the sample rate from the time column and compares it to the declared one,
checks column counts, sanity-checks the amplitude scale against the declared units, and
counts events in each marker column. It **reports; it does not gate** — a mismatch is
often the description being wrong, and you want to see it, not have your script refuse to
run.

Then **convert once, on ingest**. Read the raw file, attach everything you know, and save
that. Every later stage reads the converted form and none of them re-derives the rate from
the filename. In practice this means an `MNE` `Raw` object, an `xarray`, or a directory
with a JSON sidecar — the format matters much less than the fact that the conversion
happens exactly once, in one place you can check.

## Epochs, and why the marker columns are the experiment

Most offline EEG analysis is a comparison between conditions, and the markers are the only
record of which condition was which and when. Cut a window around each marker, group the
windows, compare the groups.

The parameters are few and each is a real choice. **Window bounds** — the example uses
−0.2 s to +0.8 s, where the pre-stimulus stretch is the baseline each epoch is measured
against. **Baseline correction** — subtract the mean of that pre-stimulus period, which
removes slow drift that would otherwise differ arbitrarily between epochs. **Rejection** —
a threshold above which an epoch is discarded, which must be decided by a rule and
reported as a count, because dropping 40% of epochs and dropping 4% are different
experiments that produce equally clean-looking averages.

The failure to watch for is a **constant timing offset**. If markers are written one
packet late, every epoch shifts by the same amount, every average shifts with it, and
nothing anywhere looks wrong. Nothing in the data will tell you. Only a known-latency test
at recording time will.

## Reproducibility

Offline work's one real advantage is that it can be re-run exactly. Keeping that is cheap
and is mostly four habits:

- **pin versions.** `moabb`, `mne` and `scikit-learn` change defaults between releases. A
  `requirements.txt` is the difference between a result and an anecdote.
- **never edit the raw data.** Read it, write derivatives elsewhere. If a script's first
  action can overwrite its input, it eventually will.
- **script it end to end**, including the download. If a step happened once in a notebook
  and nobody remembers the parameters, it did not happen.
- **write down the numbers you got**, in the repository, next to the code that produced
  them — so that a year later you can re-run and see whether anything moved.

The example does all four, which is most of why it is there.

## Then compute something

Only at this point does anything resembling analysis begin: band power, an averaged evoked
response, a classifier. That is the shortest part of the pipeline and the only part most
tutorials cover.

The worked example takes it as far as a real question — *how much do you lose with four
frontal electrodes instead of sixteen?* — and answers it with a number rather than an
opinion: [`examples/offline-bi2014a/`](../../examples/offline-bi2014a/).
