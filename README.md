
# Welcome to EEG-Guide!

The idea of this repository is to provide practical tools + documentation for :
	researching, 
	building/testing, 
	and analyzing EEG, 
Catering to **beginners and experts.**

This is a very initial build, a personal project of the author to generalize from years of knowledge and skills acquired, and is going to keep getting updated! Feedback can be emailed to debargha65@gmail.com, researchers/developers can request write access after familiarizing themselves with the [house conventions for raising PRs](CONTRIBUTING.md). 

# If you are a beginner, 

Please go through [Overview](docs/Overview.md) to familiarize yourself with the different, moving parts of EEG hardware and software building.

# If you are familiar with the basics

Try the modules yourself using CLI:

No download, no dataset — what is actually inside an EEG file:

```bash
python3 examples/offline-bi2014a/01_read_formats.py
```

It shows that the same recording shipped as `.csv` and `.mat` contains **different  
numbers**, measures whether that matters, reads both marker columns (standard tooling uses  
only one), and shows what a file gives you when the processing has already been done and  
cannot be undone.

## The worked example

**How much do you lose with four frontal electrodes instead of sixteen?** The question every consumer headband raises, answered by measurement on [BI2014a](https://zenodo.org/records/3266223) — 64 subjects, 16 dry electrodes, a P300  speller. MOABB downloads it per subject, so the default 4-subject run costs about 215 MB  rather than the full 8 GB.

|Channels|Pipeline|AUC|sd|
|---|---|---|---|
|16|XdawnCov + LogReg|**0.846**|0.101|
|16|ERPCov + LogReg|**0.831**|0.105|
|4 frontal|ERPCov + LogReg|**0.659**|0.099|
|4 frontal|XdawnCov + LogReg|**0.650**|0.097|

Chance is 0.500, so four frontal electrodes are neither useless nor equivalent to sixteen.  
The interesting part is that at 16 channels the two pipelines **separate** and at 4 they  
**converge** — with four clustered electrodes a spatial filter has nothing left to exploit,  
so the limit there is the electrodes, not the algorithm.

Full results, method and caveats: [`examples/offline-bi2014a/README.md`](examples/offline-bi2014a/README.md).

## Requirements

`01_read_formats.py` needs only numpy, scipy and pandas. The rest needs  
`examples/offline-bi2014a/requirements.txt` (MOABB, MNE, pyRiemann, scikit-learn) and  
`src/check_device.py` also needs PyYAML.

Everything is single-process and thread-capped by default. Scale up with `--subjects`.

## Index

Everything in the repository, and what each thing is for:

| | |
|---|---|
| [`docs/Overview.md`](docs/Overview.md) | the written guide, sections 1–3: brain → sensor, electrode → computer, computer → human |
| [`docs/10-live/`](docs/10-live/README.md) | the real-time recipe: ring buffers, latency, dropped packets, append-safe logging. Deliberately has no worked example — a live loop needs hardware you may not have |
| [`docs/20-offline/`](docs/20-offline/README.md) | the offline recipe: text vs binary, how much precision matters, the metadata problem, epochs |
| [`docs/30-adapting/`](docs/30-adapting/README.md) | how to describe *your* device so the description can be checked against a real recording |
| &nbsp;&nbsp;↳ [`_template.md`](docs/30-adapting/_template.md) | blank device description — copy this to start yours |
| &nbsp;&nbsp;↳ [`bi2014a-16ch-dry.md`](docs/30-adapting/bi2014a-16ch-dry.md) | worked description of a research cap: 16 dry channels, 512 Hz, headerless files |
| &nbsp;&nbsp;↳ [`muse-4ch-consumer.md`](docs/30-adapting/muse-4ch-consumer.md) | worked description of a consumer headband — including a rate that disagrees with its own documentation, left unresolved on purpose |
| [`src/check_device.py`](src/check_device.py) | compares a device description against a `.csv`/`.mat` recording and prints where they disagree. It reports; it never gates |
| [`examples/offline-bi2014a/`](examples/offline-bi2014a/README.md) | the worked example: 4 frontal electrodes vs 16, measured |
| &nbsp;&nbsp;↳ [`01_read_formats.py`](examples/offline-bi2014a/01_read_formats.py) | what is actually inside an EEG file — runs on the committed excerpts, no download |
| &nbsp;&nbsp;↳ [`02_epoch_and_score.py`](examples/offline-bi2014a/02_epoch_and_score.py) | markers → epochs → a P300 classifier, downloading 2 subjects by default |
| &nbsp;&nbsp;↳ [`03_channels_4_vs_16.py`](examples/offline-bi2014a/03_channels_4_vs_16.py) | the channel-count experiment itself, `--subjects` to scale |
| &nbsp;&nbsp;↳ [`sample/`](examples/offline-bi2014a/sample/SOURCES.md) | small committed excerpts of three public recordings, with their provenance in `SOURCES.md` |
| &nbsp;&nbsp;↳ [`results/`](examples/offline-bi2014a/results/README.md) | the full 64-subject run, committed so a short run can be compared without an 8 GB download |
| &nbsp;&nbsp;↳ [`requirements.txt`](examples/offline-bi2014a/requirements.txt) | pinned versions the committed results were produced with |

## Contributing

The short version: fork, branch, open a PR against `main`. CI runs a fast suite (the
no-download script, the device checker, a link check) and must pass; the owner reviews and
merges. Direct pushes to `main` are disabled for everyone.

The full house conventions — what a good PR looks like, and the rules every change must
keep (runnable by a stranger, every number measured, every command actually run) — are in
[CONTRIBUTING.md](CONTRIBUTING.md).

