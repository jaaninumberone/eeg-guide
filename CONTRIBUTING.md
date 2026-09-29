# Contributing

Thanks for wanting to improve the guide. The bar for a change here is the same bar the
repository sets for itself: a stranger must be able to run everything, and every claim must
be backed by something that runs.

## The flow

1. **Fork** the repository (or branch, if you have write access) and make your change on a
   branch — never on `main`.
2. **Open a pull request** against `main`. Small and single-concern beats large and mixed:
   a PR that fixes one recipe, adds one device description, or corrects one measured number
   is easy to review; a PR that does all three is not.
3. **CI must pass.** Every PR runs the fast suite (about a minute, no dataset download):
   - `examples/offline-bi2014a/01_read_formats.py` on the committed sample excerpts
   - `src/check_device.py` against both worked device descriptions
   - a negative test — the checker must still *catch* a deliberately wrong sample rate
   - a link check over every relative markdown link
4. **Review.** The owner is the required reviewer on every path (see
   `.github/CODEOWNERS`); one approval is required and a new push dismisses a stale one.
5. **Merge.** Squash merge, so `main` reads as one change per PR. Direct pushes to `main`
   are disabled for everyone, force pushes and branch deletion are blocked.

## House rules — what every change must keep true

- **Runnable by a stranger.** Nothing may depend on private data, particular hardware, or
  anything beyond this repository plus an internet connection. Public datasets are fetched
  by the scripts, per subject, never committed.
- **Every number in the prose is measured.** If a figure appears in a doc, a script in this
  repository produces it. No numbers from memory, no numbers from someone else's README.
- **Every fenced command has been run.** If you write a command into a doc, run it first,
  exactly as written.
- **Nothing heavy in `sample/`.** The committed excerpts exist so the first script runs with
  no download; keep them small, and record provenance and licence of anything new in
  `sample/SOURCES.md`.
- **Compute stays serial and thread-capped.** `n_jobs=1`, and the OpenBLAS/OMP caps at the
  top of the example scripts stay above the numpy imports — they are load-bearing (see the
  comment there for why). Defaults stay small; `--subjects` is how a run scales up.
- **The checker reports; it never gates.** `check_device.py` prints disagreements and exits
  0 — a mismatch is as often the description being wrong as the file. Do not turn it into
  a validator.
- **Unresolved disagreements stay written down, not resolved by fiat.** The Muse
  250-vs-256 Hz discrepancy is documented as a disagreement on purpose. If you can actually
  resolve one — with a measurement or a primary source — do, and show the work in the PR.

## What a good PR says

Three things, briefly: what changed, why, and **what you ran** to know it works — with the
output if it is short. "Updated the doc" is not reviewable; "re-ran `01_read_formats.py`,
table below" is.

## Reporting problems

Open an issue. A good issue for a factual error names the file and line and, ideally, the
command whose output disagrees with the text — the same standard the prose holds itself to.
