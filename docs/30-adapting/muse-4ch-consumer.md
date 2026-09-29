---
device: "Muse 2, 4-channel dry consumer headband"
source: "https://zenodo.org/records/20089290"

acquisition:
  sample_rate_hz: 250          # from the file's own time column. NOTE the dataset
                               # description says 256 -- see below
  n_channels: 4
  adc_bits: unknown
  uv_per_count: 1.0            # values are consistent with microvolts
  pga_gain: unknown
  reference_site: unknown      # Muse references to FPz in its own firmware

channels:
  labels: [TP9, AF7, AF8, TP10]
  positions: [TP9, AF7, AF8, TP10]   # here they agree. do not assume that

impedance:
  measured: false
  injected_current_na: null
  series_resistor_ohm: null
  carrier_rule: null

interference:
  mains_hz: unknown
  instrumental_lines_hz: []

transport:
  link: "BLE, in the original recording"
  packet_notes: "the archived file is post-transport; packet structure is not visible"

file:
  format: csv
  header_rows: 1
  time_column: 0
  time_kind: seconds
  data_columns: [1, 2, 3, 4]
  marker_columns: [5]
  units: microvolts
  derived_columns: false
---

# Muse 2 — 4-channel dry consumer headband

Two electrodes on the forehead and two behind the ears, which is as few as a usable EEG
montage gets. It is the closest widely-available hardware to a portable dry headband, so
it is the most honest public stand-in for one.

## What the file is

```
timestamps, TP9,     AF7,     AF8,     TP10,    Marker0
0.000,      -26.855, -27.832, -19.531, -32.715, NaN
```

Six columns, 92,748 rows. A header naming the channels, relative time in seconds, and one
marker column that is `NaN` except where an event occurred.

Compared to the headerless matrix of the previous device this is a considerable
improvement: the file says what its columns are. It still does not say the sample rate,
the units, or the reference.

## The sample rate disagrees with the documentation

The dataset description, and Muse's own specification, say **256 Hz**. The file's time
column steps by **exactly 0.004000 s**, which is **250 Hz**.

I have not resolved which is right, and that is deliberate — the point is that **the file
and its documentation disagree, and only one of them is in front of you when you load
it.** Declaring the rate and checking it against the data is how that surfaces in seconds
rather than after a day of confusing spectra. A 2.4% rate error shifts every frequency
you compute by 2.4%.

This is what `src/check_device.py` is for.

## A warning about the same device in other archives

Recordings from this headband are also distributed as **Mind Monitor** app exports, which
look superficially similar and are not. Those carry 40 columns, of which **20 are band
powers already computed** — delta through gamma for each channel — and only **four are
raw**. The filter choices, window length and reference behind those band powers are not
recorded anywhere and cannot be undone.

If you intend to do your own processing, the `derived_columns` field is the one to check
first.
