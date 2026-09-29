# Where these excerpts came from

Short cuts from three public recordings, committed so that
[`../01_read_formats.py`](../01_read_formats.py) runs immediately with no download. They
are excerpts for teaching, not data to analyse — for that, fetch the originals.

| file | rows | source record | licence |
| --- | --- | --- | --- |
| `bi2014a_subject01_excerpt.csv` / `.mat` | 10,240 (20 s @ 512 Hz) | *Brain Invaders calibration-less P300-based BCI using dry EEG electrodes Dataset (bi2014a)* — https://zenodo.org/records/3266223, subject 01, rows 65,024–75,263 | CC BY 4.0 |
| `muse_raw_excerpt.csv` | 5,000 (20 s @ 250 Hz) | *EEG Dataset for Nonlinear Dynamics-Based Characterization of Cognitive States in Engineering Students* — https://zenodo.org/records/20089290, file `EEG_09_H_EXP_2024-11-19-11_22_36.csv` | CC BY 4.0 |
| `mindmonitor_excerpt.csv` | 1,000 | *EEG and Motion Signals Pilot Dataset* — https://zenodo.org/records/22093536, Mind Monitor export | CC BY 4.0 |

All three records are published under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
(verified on the Zenodo record pages, 2026-09-29), which permits redistributing modified
copies with credit. Credit is given by the table above; the modification, in every case, is
**truncation only** — a contiguous block of rows copied out of one original file, bytes
unchanged.

The two BI2014a excerpts are the **same 10,240 rows** taken from the two files the dataset
ships, each read from its own original — so the CSV carries the dataset's real
five-significant-figure rounding rather than a rounding introduced here. That is what makes
the precision comparison in `01_read_formats.py` meaningful.

If you add an excerpt, keep it small, record its provenance and licence in this table, and
make sure the licence actually permits redistribution — openly downloadable and openly
licensed are not the same thing.
