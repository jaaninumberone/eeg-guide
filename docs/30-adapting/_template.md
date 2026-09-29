---
# ─────────────────────────────────────────────────────────────────────────────
# Device description — copy this file, rename it, fill it in.
#
# Everything here is something the guide's sections 1 and 2 leave open on
# purpose, because it differs between devices. Write it down once and the
# processing above this layer can be shared.
#
# Leave a field as `unknown` rather than guessing. `unknown` is information;
# a guess that turns out wrong is the expensive kind of mistake, because
# nothing downstream will contradict it.
# ─────────────────────────────────────────────────────────────────────────────

device: unknown                 # what it is called
source: unknown                 # where the data or hardware came from

acquisition:
  sample_rate_hz: unknown       # samples per second, per channel
  n_channels: unknown
  adc_bits: unknown             # 24 for most biopotential front ends
  uv_per_count: unknown         # microvolts per ADC count, AFTER gain.
                                # if the file is already in uV, write 1.0
  pga_gain: unknown             # amplifier gain. NOT the same question as
                                # uv_per_count -- see the prose below
  reference_site: unknown       # mastoid, earlobe, Cz, average, ...

channels:
  # Two separate lists, same order, on purpose.
  labels: []                    # exactly as written in the file's header
  positions: []                 # the TRUE 10-20 positions, in column order
  # If these two disagree, the file is lying and readers must select by
  # POSITION. That has happened; it is not hypothetical.

impedance:
  measured: unknown             # true / false
  injected_current_na: unknown  # if the device injects a test current
  series_resistor_ohm: unknown  # protection resistor in each electrode line
  carrier_rule: unknown         # e.g. "sample_rate / 4" -- a RULE, not a fixed
                                # frequency, if the carrier tracks the rate

interference:
  mains_hz: unknown             # 50 or 60, wherever it was recorded
  instrumental_lines_hz: []     # explicit Hz. do NOT derive these from the
                                # sample rate; a clock-locked comb sits at
                                # fixed frequencies

transport:
  link: unknown                 # BLE, USB, serial, file only
  packet_notes: unknown         # byte order, samples per packet, sequencing

file:
  format: unknown               # csv / mat / edf / npz / ...
  header_rows: unknown          # 0 if the file starts straight at the data
  time_column: unknown          # index, or "none"
  time_kind: unknown            # seconds | milliseconds | sample_index | none
  data_columns: []              # column indices holding signal, in order
  marker_columns: []            # column indices holding triggers or events
  units: unknown                # microvolts | volts | counts | mixed
  derived_columns: unknown      # true if the file also carries band powers or
                                # anything else already computed
---

# Device description — <name>

## Why each field is here

**`sample_rate_hz`** decides everything downstream: the Nyquist limit, the filter
corners, the length of a window, and — on devices that inject an impedance carrier —
where that carrier sits. Guessing it is the single most consequential error available.

**`uv_per_count` and `pga_gain` are two different questions.** The gain describes the
amplifier. Whether the firmware already divided by it before writing the file is a
separate fact, and only a known input settles it: feed the device a signal of known
amplitude and see what number comes out. A file can be in counts, in volts, in
microvolts, or in microvolts-times-the-gain, and nothing in the file says which.

**`labels` and `positions` are separate lists** because a header is not evidence about
physical wiring. Where they disagree, a reader that selects a channel by matching its
name silently transposes the montage and produces plausible output indefinitely.

**`carrier_rule` is a rule, not a number.** Where a front end derives its impedance
carrier from the data rate, the carrier moves when the rate moves. Recording it as a
fixed frequency is correct for one configuration and wrong for the next.

**`instrumental_lines_hz` is an explicit list.** Mains is environmental and goes in
`mains_hz`. A comb from a switching regulator or a clock sits at fixed frequencies, and
expressing it as a fraction of the sample rate is a coincidence that holds once.

**`derived_columns`** matters more than it looks. Some exports carry band powers
alongside the raw signal, computed with filter choices and window lengths that are not
recorded anywhere. You cannot undo them, so you cannot compare them against your own.

## Checking it

```bash
python3 src/check_device.py docs/30-adapting/<this-file>.md <a data file>
```

It compares what you declared against what the file actually contains and prints the
disagreements. It reports; it does not stop you.
