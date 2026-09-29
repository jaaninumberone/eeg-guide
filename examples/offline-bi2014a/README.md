# A worked example you can run yourself

Three scripts on a public dataset, answering a real question: **how much do you lose with
four frontal electrodes instead of sixteen?** That is the question every consumer EEG
headband raises, and this answers it by measurement rather than opinion.

Nothing here is specific to any particular hardware. The data is on Zenodo, the code is in
this directory, and the results of the full run are committed so you can check your own
against them.

## The dataset

**BI2014a** — "Brain Invaders", a P300 speller experiment: 64 subjects, 16 dry electrodes,
512 Hz. Items flash on a screen, the subject counts flashes of their chosen target, and
each rare target flash evokes a **P300** — a positive deflection about 300 ms later. The
analysis is a two-class problem: target flash or not.

<https://zenodo.org/records/3266223>

**You do not need to download it manually.** MOABB fetches it per subject on first use,
into `~/mne_data`, and reuses it afterwards. That matters: the whole dataset is ~8 GB, but
the default run here uses 4 subjects, which is about **215 MB**. Subject archives vary a
lot (subject 01 is 60 MB, subject 02 is 30 MB), so treat that as an estimate.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## The three steps

### 1. What is actually in the file — *no download needed*

```bash
python3 01_read_formats.py
```

Runs on the excerpts committed in [`sample/`](sample/), in a couple of seconds. It shows
that the dataset's `.csv` and `.mat` are **not** the same numbers (the CSV is rounded to
five significant figures), measures how much that matters, and reads the marker columns —
including the second one that standard tooling ignores. Then it looks at two Muse files to
show what a header does and does not buy you, and what happens when a file ships
already-computed band powers you cannot undo.

The point of the step: **none of these files states its own sample rate, units or channel
positions.** That is normal, and it is why [`docs/30-adapting/`](../../docs/30-adapting/)
exists.

### 2. Markers to epochs to a classifier

```bash
python3 02_epoch_and_score.py                # 2 subjects, ~110 MB
python3 02_epoch_and_score.py --subjects 8
```

Cuts epochs around the markers, prints the class balance (about 1 target to 5 non-targets
— the imbalance *is* the paradigm, and it is why the score below is ROC AUC and not
accuracy), locates the evoked difference, and cross-validates a classifier.

On 1 subject it finds the target/non-target difference peaking at **+6.99 µV, 257 ms, at
F4** — the right size, the right latency, the right sign. That is a sanity check on the
markers: if their timing were wrong, the average would smear and this would vanish.

Note that the channel *name* comes from
[`docs/30-adapting/bi2014a-16ch-dry.md`](../../docs/30-adapting/bi2014a-16ch-dry.md), not
from the data. The array is sixteen anonymous rows.

This step deliberately pools all subjects into one cross-validation, which **inflates the
score** — a fold can train and test on the same person. It reports ~0.90 AUC for that
reason. Step 3 does it honestly and gets less.

### 3. Four channels against sixteen

```bash
python3 03_channels_4_vs_16.py                # 4 subjects, ~215 MB download
python3 03_channels_4_vs_16.py --subjects 64  # the full run
```

The same epochs and the same two classifiers, run on all 16 channels and then on the four
frontal ones (`Fp1, F3, F4, Fp2`) that a forehead-only device would have. Evaluation is
within-session per subject, so training and test never share a session.

Results go to `my_results/`. The full 64-subject run is committed in
[`results/`](results/) for comparison.

**Timing, measured:** with the data already downloaded, the 4-subject run takes **2m19s**
(24 s for the 4-channel condition, 111 s for the 16-channel one) on a laptop with threads
capped at 2. The download dominates the first run. The 64-subject run is roughly sixteen
times that.

The scripts cap `OMP_NUM_THREADS` and friends at 2 **before importing numpy**, because
`n_jobs=1` only limits scikit-learn's processes — OpenBLAS still spawns one thread per core
inside every matrix operation, which on a 16-core machine means a load average of ~14 from
a script that looks single-threaded. Raise them if your machine is happy being loaded; the
results do not change.

## What the full run found

| channel set | pipeline | mean AUC | sd | n |
| --- | --- | --- | --- | --- |
| 16ch_full | XdawnCov+LogReg | **0.846** | 0.101 | 64 |
| 16ch_full | ERPCov+LogReg | **0.831** | 0.105 | 64 |
| 4ch_frontal | ERPCov+LogReg | **0.659** | 0.099 | 64 |
| 4ch_frontal | XdawnCov+LogReg | **0.650** | 0.097 | 64 |

Chance is 0.500. So four frontal electrodes are clearly **not useless** — and clearly not
equivalent to sixteen.

The more interesting result is the *pattern*. At 16 channels the two pipelines separate,
with the spatially-filtered one (xDAWN) ahead. At 4 they **converge**. xDAWN works by
finding combinations of channels that maximise the evoked response; with four clustered
frontal electrodes there are almost no useful combinations available, so it has nothing to
exploit and collapses onto the simpler method.

That is a statement about a ceiling. **With four frontal electrodes the limit is the
electrodes, not the algorithm** — a better classifier buys you little. With sixteen there
is spatial information to exploit and the choice of method starts to pay.

Read the standard deviations too: around 0.10, meaning subjects differ from one another
far more than the pipelines differ from one another. The 16-vs-4 gap of ~0.18 is large
against that spread. The ~0.015 gap between the two 16-channel pipelines is not, and
should not be read as one method beating the other.

## If your numbers differ

A 4-subject run gives 8 scores per cell against 64, so expect it to be noisy. Here is an
actual `--subjects 4` run against the committed full run:

| | 4 subjects | 64 subjects | diff |
| --- | --- | --- | --- |
| 16ch XdawnCov | 0.865 | 0.846 | +0.019 |
| 16ch ERPCov | 0.859 | 0.831 | +0.028 |
| 4ch ERPCov | 0.683 | 0.659 | +0.024 |
| 4ch XdawnCov | 0.670 | 0.650 | +0.020 |

Everything within 0.03, and the 16-vs-4 gap reproduces at 0.186 against 0.184. That is the
level of agreement to expect.

Notice what does **not** reproduce: over 4 subjects the two 16-channel pipelines come out
0.859 and 0.865, which is indistinguishable, whereas over 64 they separate. A short run can
see the big effect and cannot resolve the small one — which is the general lesson, not a
detail about this dataset.

If you are much further out, the likely causes in order: a different library version (see
`requirements.txt`), a different channel subset, or a change to `tmin`/`tmax`/`resample`.

## Honest limits

- **One dataset, one paradigm.** This is a P300 speller with dry electrodes. It does not
  license a general claim that four channels get you 78% of the way for *any* question.
- **Frontal is the hard case for P300.** The response is largest centro-parietal, so a
  forehead montage is poorly placed for it. Another measure — frontal alpha asymmetry, say
  — might favour the four-channel set. The method here is the transferable part, not the
  number.
- **Offline, with all the advantages.** Whole-session normalisation, no dropped packets, no
  latency budget. A live system would do worse. See [`docs/10-live/`](../../docs/10-live/).
- **`cv_protocol` is `within_session` throughout**, because BI2014a records one session per
  subject and cross-session evaluation is therefore impossible with it.

## Credit

Adapted from `res/eeg-benchmark/03_benchmark.py`; the pipelines, paradigm and parameters
are unchanged so the numbers remain comparable. The heavy lifting is
[MOABB](https://github.com/NeuroTechX/moabb), [MNE](https://mne.tools) and
[pyRiemann](https://pyriemann.readthedocs.io).
