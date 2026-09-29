---
device: "16-channel dry-electrode research cap (Brain Invaders, bi2014a)"
source: "https://zenodo.org/records/3266223"

acquisition:
  sample_rate_hz: 512          # confirmed: time column steps by 0.0019531 s
  n_channels: 16
  adc_bits: unknown
  uv_per_count: 1.0            # the file is already in microvolts
  pga_gain: unknown            # not recoverable from the data
  reference_site: unknown      # the paper states it; the file does not

channels:
  labels: []                   # the file has NO header. this is not an oversight
                               # in the description -- there is nothing to record
  positions: [Fp1, Fp2, F3, AFz, F4, T7, Cz, T8,
              P7, P3, Pz, P4, P8, O1, Oz, O2]

impedance:
  measured: false
  injected_current_na: null
  series_resistor_ohm: null
  carrier_rule: null

interference:
  mains_hz: unknown            # recorded in Europe, so probably 50, but the
                               # data does not say and neither will I
  instrumental_lines_hz: []

transport:
  link: "file only"
  packet_notes: "not applicable; this is an archived recording"

file:
  format: "mat and csv, both provided"
  header_rows: 0
  time_column: 0
  time_kind: seconds
  data_columns: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
  marker_columns: [17, 18]
  units: microvolts
  derived_columns: false
---

# 16-channel dry cap — Brain Invaders `bi2014a`

71 subjects in the published dataset, playing a P300 speller: a grid of 36 symbols
flashes, and the flash containing the symbol you are attending produces a voltage
deflection about 300 ms later. Up to three sessions each.

## What the file is

One array per subject. **491,942 rows × 19 columns of float64** for the subject
inspected here — roughly 16 minutes at 512 Hz.

```
col 0       time, seconds        0, 0.0019531, 0.0039062, ...
cols 1-16   the electrodes, uV
cols 17-18  triggers, values 0/1/2
```

There is no header, no channel name, no sample rate and no units anywhere in the file.
**Every one of the positions above comes from outside it** — from the paper, and from
the reader library that wraps it. That is the single most important thing this device
description records, and it is why the `labels` list is empty rather than invented.

## Two triggers, one of which is used

There are two marker columns. The standard reader takes the **last** one, and its values
are `0` for nothing, `1` and `2` for the two flash types. Those two integers are what
turn a 16-minute wall of numbers into an experiment: without them there is nothing to
average against and no question being asked.

## `.mat` and `.csv` are not the same file

Both are supplied, and they are not identical. The CSV is a **rounded copy at 5
significant figures**:

| | |
| --- | --- |
| `.mat` | `169.08673096` — full float64, 49 MB |
| `.csv` | `169.09` — 6 characters, 65 MB |

The relative error is a constant ~7×10⁻⁶. Against typical EEG here of ~520 µV that is a
median absolute error of **0.0004 µV** — four orders of magnitude below the signal, and
irrelevant to any result. The triggers, being integers, survive exactly.

So the CSV is readable by anything and slightly lossy; the `.mat` is exact, 25% smaller,
and needs a reader. Neither carries a single word about what its columns mean.
