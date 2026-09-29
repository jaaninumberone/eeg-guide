# Full run — all 64 subjects

Produced by `03_channels_4_vs_16.py --subjects 64`, on a laptop, serially. Kept here so a
short run can be compared against it without anyone having to download 8 GB.

`results.csv` — one row per subject × channel set × pipeline (256 rows).
`summary.csv` — those rows aggregated.

| channel set | pipeline | mean AUC | sd | n |
| --- | --- | --- | --- | --- |
| 16ch_full | XdawnCov+LogReg | **0.846** | 0.101 | 64 |
| 16ch_full | ERPCov+LogReg | **0.831** | 0.105 | 64 |
| 4ch_frontal | ERPCov+LogReg | **0.659** | 0.099 | 64 |
| 4ch_frontal | XdawnCov+LogReg | **0.650** | 0.097 | 64 |

Chance is 0.500. Four frontal electrodes are well above chance and well below sixteen.

**Read the standard deviations.** They are around 0.10 — a tenth of the whole scale —
which means subjects differ from each other far more than the pipelines differ from each
other. Any single subject is a poor estimate of anything, and a run over 4 subjects can
easily land 0.05 away from these numbers without anything being wrong. The 16-vs-4 gap of
~0.18 is large compared with that spread; the ~0.015 gap between the two 16-channel
pipelines is not, and should not be read as one pipeline beating the other.

**The finding worth the effort** is not that fewer electrodes score lower, which is
unsurprising. It is that at 4 channels the two pipelines **converge** (0.659 and 0.650,
in either order within noise) while at 16 they **separate**, with the spatially-filtered
one ahead. xDAWN works by finding combinations of channels that maximise the evoked
response; with four clustered frontal electrodes there are few useful combinations to
find, so it has nothing to exploit and collapses onto the simpler method.

That is a statement about the ceiling. With four frontal electrodes the limit is the
electrodes, and a better algorithm will not move it much. With sixteen there is spatial
information available, and the choice of method starts to pay.

`cv_protocol` is `within_session` throughout: BI2014a records one session per subject, so
cross-session evaluation is not possible with this dataset.
