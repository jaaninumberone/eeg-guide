---
title: "Adapting this to your device"
description: Write down what your device is, in a form that can be checked against a real recording.
---

# Adapting this to your device

An EEG file is a matrix of numbers that does not say what it is. Everything downstream —
filters, epochs, band powers, classifiers — needs facts that live outside it: the sample
rate, what one unit means in microvolts, which column is which electrode and where on the
head it sat, what the markers encode. Get one wrong and nothing crashes; you get a
plausible wrong answer. A 512 Hz recording analysed as 256 Hz reports alpha at 5 Hz, and
every number after that is confidently incorrect.

So this directory holds **one description per device**, written by hand, and a script that
checks a description against a real recording.

## Files

| | |
| --- | --- |
| [`_template.md`](_template.md) | blank description to copy, with prose on why each field is there |
| [`bi2014a-16ch-dry.md`](bi2014a-16ch-dry.md) | a research dataset: 16 dry channels, 512 Hz, headerless files |
| [`muse-4ch-consumer.md`](muse-4ch-consumer.md) | a consumer headband: 4 channels, named columns, and a rate that disagrees with its own documentation |
| [`../../src/check_device.py`](../../src/check_device.py) | compares a description against a data file |

## Writing one

Copy `_template.md`, name it after the device, and fill it in. The front matter is YAML so
it can be read by a script; the prose below it is for whoever inherits the file.

Two rules make this useful rather than decorative:

**Leave a field as `unknown` rather than guessing.** An `unknown` is a question someone can
answer. A plausible guess is indistinguishable from a fact and will be treated as one. If
you do not know the reference site, say so — it is much better than writing `mastoid`
because most headbands use it.

**State rules as rules, not as the number they currently produce.** An impedance carrier at
a quarter of the sample rate is `fs/4`, not `128`, because the moment someone runs the
device at a different rate the number is wrong and the rule is still right. Hard-coded
numbers derived from configuration are the most common way a description goes quietly
stale.

Each field also carries where it came from — measured, taken from documentation, or
assumed — because *512 Hz because we counted the timestamps* and *512 Hz because the
website says so* are different degrees of confidence, and the second one is how the Muse
discrepancy below arose.

## Checking one

```bash
python3 src/check_device.py docs/30-adapting/muse-4ch-consumer.md path/to/recording.csv
```

```
  [ok  ] 4 channels, 4 data columns
  [ok  ] sample rate 250 Hz agrees with the time column (250.00 Hz)
  [ok  ] amplitude 68.4 is plausible for microvolts
  [ok  ] header matches declared labels: ['TP9', 'AF7', 'AF8', 'TP10']
  [note] marker column 5 contains no events in this file

0 mismatch(es), 1 note(s).
```

It derives the sample rate from the time column and compares it with the declared one,
checks the column count, sanity-checks amplitude against the declared units, compares
header names with declared labels, counts events in each marker column, and looks for an
impedance carrier if the description gives a rule for one. It reads `.csv` and `.mat`.

**It reports; it does not gate.** A mismatch is as likely to be the description being wrong
as the file, and a tool that refused to run would just teach you to stop running it. The
note above is a good example: the marker column exists and is empty in that excerpt, which
is worth knowing before you wonder why you got zero epochs, and is not an error.

## A real disagreement, left unresolved

`muse-4ch-consumer.md` declares 250 Hz. The Zenodo description of the recording it was
written from says 256 Hz. The timestamps in the file give 250.00 Hz, consistently.

The description records 250, with a note saying where the other number came from. This
guide does not claim the dataset is wrong: one file is not evidence about a published
dataset, the difference could be a device setting, a resampling step, or an error in either
place. What matters is that the disagreement is **written down where the next person will
see it** instead of being silently resolved by whoever happened to look first.

Change the file to 256 and re-run the checker to watch it catch the mismatch — which is
also the quickest way to see what the tool is for.
