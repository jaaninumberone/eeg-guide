# 1. From the brain, to the EEG sensor

Neurons in the brain communicate with each other using electrochemical signals that spread to other neurons, increasing (with excitatory input) or decreasing (with inhibitory input) their probability and rate of firing. An **action potential** is binary: a neuron either fires (gets activated via its **receptors** and releases its output (often **neurotransmitters**)onto other neurons or cells) or it doesn’t. However, the threshold at which the neuron fires, **temporal summation** and **spatial summation** of inputs, and the relative physical and chemical **connectivity**[^c1] between neurons are highly variable. This allows neurons to cluster together and give rise to emergent properties that allows this analog firing to represent, store, manipulate, and act upon data, turning it into information and finally, knowledge. It is these emergent properties that power thoughts, feelings, and behaviours1[^c2].

Different regions, networks and layers have different structural and chemical properties, granting them unique functional roles. The most recent and unique development to the nervous system in mammalian evolution, therefore, remains the **neocortex**. Large neurons, that are also densely connected in a branching fashion, receive and send signals from many and distant neurons, and cover the outermost layer of the brain (cortex), integrating the organism’s stream of experience and will to act in a single, coherent space. This is why the **prefrontal cortex** is so important, it computes, decides, and acts, which are the highest-order functions. The large neurons in the cortex are called **pyramidal neurons**, and EEG picks up these large-scale, cortex-level, dispersed signals after being attenuated through layers of biological material before reaching the **electrode** on a person’s scalp and registering as a voltage point. 2[^c3]

## Sources

[^c1]: **Debargha Roy, 2026-09-04** — dendrites and axons, network effects.
[^c2]: **Debargha Roy, 2026-09-29** — master thesis link
[^c3]: **Debargha Roy, 2026-09-29** — https://www.learningeeg.com/montages

# 2. From the electrode, to the computer

Electrodes are conductive, and come in a variety of forms. While wet electrodes made of Ag/AgCl are the canonical and most widely used in EEG, portability pushes towards dry electrodes, which despite high **impedance** and low **SNR a**re capable of providing useful information when leveraged given favourable control over hardware, recording environment, and **digital signal processing**.

Electrical activity is picked up by the conductive “sensors”, i.e. they respond to voltage fluctuations, and this travels through the circuit of the EEG headband/cap to the analog-to-digital converter or ADC (also analog front end or AFE) which registers this and **quantizes** it. The chip we use for this is the ADS12993[^c4], which is a sigma-delta (also called delta-sigma) converter4[^c5]. The input voltage from the sensor is routed through the **driven-right leg circuit** and referenced to **site of choice**[^c6] to output a big-Endian data stream per channel (4-8 for portable) that in a wireless set up may use a BLE GATT + microcontroller, software-firmware system to communicate with the headband (via ESP32, for example)5[^c7]. This can be managed in a live data loop or offline, backend system of choice.

## Sources

[^c4]: **Debargha Roy, 2026-09-29** — https://www.ti.com/lit/ds/symlink/ads1299.pdf?ts=1786293166686&ref_url=https%253A%252F%252Fwww.google.com%252F
[^c5]: **Debargha Roy, 2026-09-29** — https://www.youtube.com/watch?v=M5Vx-X66seg
[^c6]: **Debargha Roy, 2026-09-29** — mastoid for dry consumer headbands with a frontal/temporal focus, Muse being the prototype.
[^c7]: **Debargha Roy, 2026-09-29** — https://github.com/Cerelog-ESP-EEG/ESP-EEG

# 3. Computer to Human

The previous section ended with a stream of numbers arriving somewhere, and with a
sentence that quietly did a great deal of work: *this can be managed in a live data loop
or offline, backend system of choice.* That sentence is the hinge of the whole guide, and
it hides two problems rather than one.

The first is that the stream does not describe itself. What arrives is a sequence of
integers or floats, and nothing in that sequence says how many arrive per second, what
voltage one unit represents, which column is which electrode, or where on the head those
electrodes sat. All of that was true of the hardware, was known to whoever built it, and
is simply **absent from the data**. Every stage after this point needs those facts, and
every stage will silently produce a plausible-looking wrong answer if given the wrong
ones. A 512 Hz recording analysed as though it were 256 Hz does not crash; it reports
alpha rhythm at 5 Hz and every band boundary lands in the wrong place.

So the first job on the computer side is not processing at all. It is **writing down what
the device is** — rate, units, channel order, positions, reference site, what the marker
columns mean — as a document that travels with the data and can be checked against it.
This guide keeps those in [`docs/30-adapting/`](30-adapting/), one file per device,
with a blank template to copy and a script that compares a description against a real
recording and reports where they disagree. It is deliberately dull. It is also the only
part of the chain that cannot be recovered later: if you do not know the sample rate of a
recording, no amount of analysis will tell you6[^s6].

## The fork

The second problem is that *live* and *offline* are not two ways of doing the same thing.
They are different problems that happen to share arithmetic, and the difference is not
speed.

Offline, you have the whole recording. You can look at the end before deciding what to do
with the beginning. You can run a filter forwards and then backwards over the same data so
that the phase shifts introduced by the first pass are cancelled exactly by the second —
**zero-phase filtering**, which leaves every feature at the time it actually occurred. You
can find the noisiest stretches and exclude them, having seen all the others to compare
against. You can try an approach, dislike it, and try another on identical data.

Live, you have only the past. A filter can look backwards and no further, so it is
**causal**, and every causal filter delays the thing it is filtering — sharper filters
delay more, and that delay is now part of your measurement. You cannot exclude a bad
stretch you have not yet seen, so you must decide whether the current stretch is usable
using only what came before it. You cannot re-run anything, because the moment has passed.
And you are committed: whatever the loop does, it does at the rate the data arrives, or
the buffer overruns and you lose samples.

The practical consequence is that **an offline result is not a promise of a live one**. A
classifier that separates two conditions at 85% accuracy on recorded data is not a
classifier that will do so in a headset, because offline it was allowed to see the future,
normalise against the whole session, and drop the bad trials. This is worth stating
plainly because the mistake is so easy to make and so hard to see: the code runs, the
number appears, and nothing signals that the number came from information the live system
will never have.

Neither mode is the serious one. Offline is where you find out whether an effect exists
at all, because it is the only place you can check honestly. Live is where the effect has
to survive contact with a person who is moving, blinking, and waiting for a response. Work
usually goes offline first and live second, and the second step is a real step, not a
port.

- **Live** — the loop, its buffer, and what causality costs: [`docs/10-live/`](10-live/)
- **Offline** — files, formats, epochs and reproducibility: [`docs/20-offline/`](20-offline/)
- **A worked example** you can run yourself, on a public dataset:
  [`examples/offline-bi2014a/`](../examples/offline-bi2014a/)

## What the processing actually does

Whichever fork you take, the arithmetic between the stream and the result is much the same
short list, and it is worth naming because each step defends against something specific.

**Referencing.** A voltage is always a difference between two points, so every EEG number
is really *this electrode minus that one*. Change the reference and every channel changes,
which means the reference is part of the measurement and not a detail. A **common average
reference** subtracts the mean across channels at each instant, which removes whatever is
shared by all of them — useful, because much of the worst interference is shared, and
risky, because with four electrodes clustered on the forehead, genuine frontal brain
activity is also shared and gets subtracted along with the noise7[^s7].

**Filtering.** A **high-pass** removes the slow drift that comes from the electrode–skin
interface rather than the brain, and that drift is often far larger than the signal. A
**low-pass** removes what is above the band of interest. A **notch** removes mains hum at
50 or 60 Hz and its harmonics. Each is a decision about what you are declaring to be not
the signal, and each one is capable of destroying the thing you were looking for if that
declaration is wrong.

**Rejecting.** Blinks, jaw clenches and a cable brushing a collar all produce excursions
tens of times larger than cortical activity. They must be excluded, by some rule stated in
advance, and the rule must be reported — because a threshold that drops 40% of the data is
a different experiment from one that drops 4%, even when both produce a clean-looking
average.

**Epoching**, for anything time-locked to an event. Cut a window around each marker, group
the windows by condition, and compare. This is where the marker columns stop being a
column of integers and become the experiment: they are the only record of what the person
was doing and when, and a marker offset by a fixed 20 ms shifts every result by 20 ms
without producing a single suspicious number anywhere.

**Estimating.** Band power in a frequency range, an average waveform across trials, a
classifier output. This is the first point at which anything resembling an answer appears,
and it is much later in the chain than people expect.

## The bridge to the human

Everything above produces a number. The section is called *computer to human* because a
number is not yet information, and the gap between them is where most of the honesty in
this field lives.

Suppose the pipeline reports alpha power of 14.2 µV² at one electrode. On its own this
means nothing whatsoever. It becomes meaningful only when three further things are known.

**Something to compare it against.** Fourteen is high or low only relative to a baseline —
the same person with their eyes open, the same person yesterday, a group of people the
same age. EEG amplitudes vary enormously between individuals for reasons that have nothing
to do with the brain: skull thickness, hair, how well the electrode sat. **Almost every
trustworthy EEG result is a within-person comparison**, because the between-person
variation is larger than most effects of interest8[^s8].

**How much it moves when nothing has changed.** Record the same person twice, ten minutes
apart, doing nothing different. The two numbers will differ. That difference is the
measurement's noise floor, and a change smaller than it is not a finding, however
interesting it would be. This is the single most commonly skipped step, and skipping it is
what allows a pipeline to produce a confident number that means nothing at all. It costs
one extra recording to establish and it determines whether anything you report afterwards
can be believed.

**A decision it informs.** If the number came out differently, would anyone do anything
differently? If not, the number is decoration. This is not a criticism of exploratory
work, which is how effects get found in the first place — it is a criticism of presenting
exploratory output as though it were a result.

To these, add two habits of presentation. Report the **uncertainty** alongside the
estimate: EEG is averaged over trials that vary, and an average without a spread invites
the reader to believe it is more precise than it is. And report the **signal quality** of
the recording it came from — impedances, how much data was rejected, whether the mains
line was visible — because a number computed from a bad recording looks exactly like a
number computed from a good one, and the reader cannot tell the difference unless told.

A last point specific to anything worn on a head rather than run in a lab. A consumer
headband with four dry electrodes on the forehead is not a worse version of a research cap
with sixty-four wet ones; it is a different instrument with a different reach. There are
questions it can answer well, because it is comfortable enough to be worn for hours at
home, and questions it simply cannot, because the relevant activity is generated somewhere
its electrodes do not sit. The worked example in this guide takes exactly this question
and measures it rather than arguing about it: the same dataset, the same analysis, run on
all sixteen channels and then on four frontal ones, with the difference in what can be
detected reported as a number9[^s9].

Knowing which questions your instrument can answer is the last conversion in the chain,
and the only one performed entirely by the human.

## Sources

[^s6]: On metadata that cannot be recovered after the fact, and the case for writing a device description before the first recording: see [`docs/30-adapting/README.md`](30-adapting/README.md) in this guide.
[^s7]: Common average referencing and its behaviour with small, clustered montages — https://www.learningeeg.com/montages
[^s8]: Within-subject versus between-subject variation in EEG amplitude measures.
[^s9]: The measurement itself: [`examples/offline-bi2014a/`](../examples/offline-bi2014a/), run on the BI2014a dataset, https://zenodo.org/records/3266223
