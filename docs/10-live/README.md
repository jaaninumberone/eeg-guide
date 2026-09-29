---
title: "Live processing"
description: What a real-time EEG loop has to do, and what causality costs you. Device-agnostic; no worked example.
---

# Live processing

This is a recipe, not a worked example. A live loop is only meaningful with hardware
streaming into it, and this guide does not assume you have any. What follows is what any
live loop must handle, whatever device is at the other end — written so that you can
recognise each piece in whatever SDK you end up using, and so that you notice when one is
missing.

The offline half of the guide *does* have a worked example, because offline work needs
only a file: [`../20-offline/`](../20-offline/) and
[`examples/offline-bi2014a/`](../../examples/offline-bi2014a/).

## The shape of the loop

Samples arrive in **packets**, not files. A device sending 250 samples per second does not
deliver them one at a time; it fills a small buffer on the microcontroller and transmits
it, so what actually arrives is something like 12 samples every 48 ms. Nothing about your
processing should assume otherwise.

So the first structure in any live system is a **ring buffer**: a fixed-size array holding
the last N seconds, with a write position that wraps around. Packets are written in as
they arrive; analysis reads a window out whenever it wants one. The two run at different
rates and neither waits for the other.

```
packets in  ──▶ [ ring buffer: last N seconds ] ──▶ window out ──▶ processing
   irregular,        fixed size, wraps              regular,
   ~48 ms                                           e.g. every 250 ms
```

**The buffer length is the real parameter.** It must be at least as long as the longest
window any analysis needs, plus a margin for jitter in packet arrival. Too short and an
analysis occasionally reads across the wrap point into samples that have already been
overwritten — which produces not an error but a window containing a splice of the present
and four seconds ago, and a spectrum computed from it looks entirely reasonable. Too long
wastes memory, which on an embedded target may matter and on a laptop does not. When in
doubt, make it longer.

## Latency is structural, not a performance problem

A 4-second window cannot tell you anything about the last 4 seconds until those 4 seconds
have happened. If your analysis needs 4 seconds of data, your output is a statement about
a period that ended when the window closed, and the fastest possible response is one
window length behind the event that caused it. No amount of optimisation changes this. It
is a property of having asked for 4 seconds.

On top of that sits the delay of the filters themselves. Offline you can filter forwards
and backwards to cancel phase shift; live you cannot, because the backwards pass needs
data that has not arrived. So every live filter is **causal**, and a causal filter delays
what passes through it — a sharper cutoff delays more. A steep 50 Hz notch can easily
contribute tens of milliseconds on its own.

The total latency a person experiences is therefore roughly:

```
packet interval  +  window length  +  filter group delay  +  compute time
```

and the last term is usually the smallest. Optimising the code when the window is what
costs you is a common and expensive mistake. If you need lower latency, shorten the
window, and accept the frequency resolution you lose by doing so — a 1-second window
cannot resolve frequencies more finely than about 1 Hz, and no processing recovers that.

## Dropped packets

Wireless links drop packets. This is normal, it will happen during your recording, and
whether your system notices is a design decision you make once and live with.

The failure mode that matters is the silent one. If a packet is lost and the next one is
simply appended to the buffer, the gap closes and the data looks continuous. Every sample
after that point is now attributed to a time that is too early by the length of the gap.
Spectral estimates degrade gracefully and you may never notice. Anything time-locked to an
event — an evoked response, a reaction-time analysis, a stimulus-locked average — is
corrupted in a way that produces plausible output.

So: if the protocol offers sequence numbers or timestamps, **check them on every packet**,
and when one is missing insert the right number of samples marked as missing rather than
closing the gap. If it offers neither, compare arrival times against the nominal rate and
at minimum count the discrepancies, so that a session which lost 8% of its data is
distinguishable afterwards from one that lost none. A dropped-sample counter, reported at
the end of every session, costs almost nothing and is the difference between knowing and
guessing.

While you are at it, check the **actual rate**. Devices routinely run at a rate slightly
different from the one on the box, and the discrepancy accumulates: 0.4% over a
twenty-minute session is five seconds of drift. See the Muse device description in
[`../30-adapting/`](../30-adapting/) for a real example where the file and the
documentation disagree.

## Impedance during the recording

If the device can measure electrode impedance while recording — many ADS1299-based designs
can, by injecting a small known current and reading back the voltage it develops — use it
continuously rather than only at setup. Contact degrades: gel dries, the wearer moves, a
dry electrode works loose from hair. An impedance trace tells you *when* a channel went
bad, which lets you exclude that period specifically instead of discarding the channel or,
worse, keeping all of it.

The injected current appears in the signal as a **carrier** at a frequency set by the
chip's configuration, and the position of that carrier follows from the configuration
rather than being a fixed number — so it is something your device description states as a
rule, not a constant. Whatever it is, it must be filtered out before analysis, and it must
be *known* to be filtered out rather than assumed.

## Logging

This is the only place a file format enters a live system. The loop itself holds everything
in memory; the log exists so that today's session can be re-analysed tomorrow with better
ideas.

**Append-safety beats every other property.** A format that writes its structure at the
end of the file — which includes MATLAB `.mat` and most other single-shot binary formats —
gives you an unopenable file if the session dies at minute 40 of 45. Line-oriented text
flushed as it goes gives you 40 usable minutes. The loss you are protecting against is not
theoretical: batteries run out, Bluetooth stacks fall over, and laptops close.

Practical form:

- **write raw**, before your processing, so that a better pipeline next year gets the real
  data rather than your current filter's output;
- **flush regularly** — buffering a megabyte is exactly how you lose a megabyte;
- **log events into the same timebase as the samples**, not to wall-clock in a separate
  file. Correlating two clocks after the fact is guesswork;
- **write a small header or sidecar** naming the rate, the units, the channel order and the
  device, so the recording does not immediately become the anonymous matrix the rest of
  this guide is about. Copying the device description from
  [`../30-adapting/`](../30-adapting/) next to the data file is enough.

Convert to a compact binary format afterwards if you want. Afterwards is safe.

## What live costs you, in one list

| Offline | Live |
| --- | --- |
| zero-phase filtering (`filtfilt`) | causal only; every filter adds delay |
| reject artefacts having seen the whole session | decide from the past alone, or not at all |
| normalise against the whole recording | running estimate, or a baseline block up front |
| re-run with different parameters | one pass, at the rate the data arrives |
| a gap in the data is visible | a gap is silent unless you check for it |

The entries on the right are not workarounds for the entries on the left. They are a
different set of methods with their own literature, and a live system is designed against
them from the start rather than adapted towards them.

## Before you trust a live number

Run the same recording through both paths — your live loop, and an offline pipeline
applied to the log it produced — and compare. They will not agree exactly, and the size of
the disagreement is the cost of being live, measured rather than assumed. If they disagree
wildly, one of them has a bug, and you now know to look.

This is the one test that catches most live-processing errors, and it needs no extra
hardware: the log is already there.
