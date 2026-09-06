# Shared Blind Spots in Numerical Quadrature

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22557771.svg)](https://doi.org/10.5281/zenodo.22557771)

Differential testing catches the mistakes that independent implementations make
*independently*. It cannot catch the mistakes they make *together*.

This repository tests that claim in numerical quadrature, and finds it holds in
the strongest available form.

## The result

Integrate a narrow Gaussian bump centred at `x = 1/3` over `[-1, 1]`. The exact
answer is elementary. Hand it to five quadrature routines spanning three
independent algorithm families:

| off-centre bump, width `1e-6` | returned | claimed error | warned |
|---|---|---|---|
| `scipy.integrate.quad` (QUADPACK) | `0.0` | `0.0` | no |
| R `integrate()` (QUADPACK) | `0.0` | `0.0` | no |
| `mpmath.quad` (tanh–sinh) | `0.0` | `0.0` | no |
| adaptive Simpson (NumPy) | `0.0` | `0.0` | no |
| fixed-grid Simpson (NumPy) | `0.0` | — | no |
| **exact** | **`1.772454e-06`** | | |

Every routine is wrong. Every routine reports success. Four of the five report
an estimated error of *exactly zero* — they assert the answer is exact.

At the five narrowest widths tested, every returned value is **bit-identical**.
Maximum pairwise spread across all five implementations: `0.000e+00`.

Comparing the implementations against each other detects nothing. Only the
closed-form reference detects it.

## Why this is not just "quadrature can fail"

That adaptive quadrature misses narrow features is textbook, and no novelty is
claimed for it. What is measured here is that the independent implementations
fail **in agreement**, which is what makes the failure invisible to differential
testing — so adding another implementation is not a remedy.

Two further results sharpen it:

**Tightening tolerances never finds it.** At `limit=10000, epsabs=1e-16`,
`scipy.quad` still returns exactly `0.0`. The blindness follows from deciding
convergence by sampling a function at finitely many points, which every routine
must do. It is not a defect in any implementation.

**Better driving works only if you already know the answer's location.** Told
where the mass is, `mpmath` recovers at every width. But that information is the
thing a real application does not have.

**Independence of authorship is not independence of algorithm.**
`scipy.integrate.quad` and R's `integrate()` present as independent — different
languages, projects, authors, documentation — and return identical verdicts in
all 18 cells, because both descend from QUADPACK. Cross-checking Python against
R teaches you almost nothing here.

## Method

`SCOPE.md` fixes the question, the two probe families, the width axis, and the
falsification conditions **before any measurement was taken**. The condition that
mattered: if the implementations disagreed where they were wrong, differential
testing would detect the failure and the claim would fail. They did not disagree.

The second probe family — the off-centre bump — was declared in advance and
earned it. On a *centred* bump the hand-rolled adaptive Simpson routine passes at
every width, because the bump sits on the midpoint abscissa Simpson always
samples. Read alone, that would have supported the opposite conclusion. It was
not robustness; it was where the probe happened to sit.

Full findings in [`REPORT.md`](REPORT.md).

## Reproducing

```bash
python run.py       # writes results.csv, 90 cells
python analyse.py   # every table in the report
```

Needs Python with `numpy`, `scipy`, `mpmath`; R with `integrate()` supplies the
fifth implementation and is skipped with a notice if absent. Nothing is
stochastic — the numbers are exactly reproducible.

## Relation to prior work

This replicates the central structural claim of the silent-failure study
(<https://doi.org/10.5281/zenodo.22458147>), which found three rigid-body
dynamics engines and an independent reference all reporting success while
returning roughly 20 radians of motion for a configuration whose exact solution
does not move. That was one instance in one domain. This is a second domain, with
a different mechanism — sampling rather than floating-point representation at an
unstable equilibrium — and the same structure.

## Disclosure

The author of this replication also authors the study whose claim is under test,
so a positive result supports his own prior conclusion. The falsification
conditions were fixed before measurement and the raw per-cell results are
published in `results.csv` rather than summarised. AI assistance was used in this
work.

## Citing

Archived at <https://doi.org/10.5281/zenodo.22557771>. See [`CITATION.cff`](CITATION.cff).

## Licence

MIT.
