# A Shared Blind Spot in Numerical Quadrature

**Replication of the silent-failure study's central claim in a second domain**

Noah Parsons · 6 September 2026

---

## Result

The claim under replication is that differential testing detects the failures
independent implementations make *independently*, and is structurally blind to
the failures they **share**. In the dynamics study that rested on one instance
in one domain. It reproduces in numerical quadrature, and more sharply.

On the off-centre probe family at widths of `1e-3` and below — seven of the
eighteen cells in that family — **every one of five implementations returns a
wrong answer and reports success**. At the five narrowest widths every returned
value is *bit-identical*: all five return exactly `0.0` for an integral whose
exact value is nonzero, and four of the five report an estimated absolute error
of exactly `0.0`.

The routines do not merely agree. They agree bit-for-bit, and they actively
assert that their answer is exact.

| off-centre, `w = 1e-6` | returned | claimed abs. error | warned |
|---|---|---|---|
| `scipy.integrate.quad` (QUADPACK) | `0.0` | `0.0` | no |
| R `integrate()` (QUADPACK) | `0.0` | `0.0` | no |
| `mpmath.quad` (tanh–sinh) | `0.0` | `0.0` | no |
| adaptive Simpson (NumPy) | `0.0` | `0.0` | no |
| fixed-grid Simpson (NumPy) | `0.0` | — | no |
| **exact** | **`1.772454e-06`** | | |

Cross-implementation comparison across all five — spanning three genuinely
independent algorithm families — detects nothing whatsoever. Only the
closed-form reference detects it.

## What is and is not new

That adaptive quadrature can miss a narrow feature is textbook, and this study
claims no novelty for the phenomenon. The contribution is the **differential
testing framing**: measuring whether independent implementations fail *in
agreement*, and finding that they do, so that adding implementations is not a
remedy. The silent-failure study argued this structurally; this is a second
domain in which it is measured.

The falsification conditions were fixed in `SCOPE.md` before any number existed.
The one that mattered was the second:

> If the implementations disagree with each other where they are wrong, then
> differential testing **does** detect the failure, and the central claim fails
> even if individual routines are wrong.

They did not disagree. Maximum pairwise relative spread across the five
implementations is `0.000e+00` at every width from `1e-5` down.

## The pre-declared second family earned its keep

`SCOPE.md` declared an off-centre family in advance, to rule out the possibility
that any effect was an artefact of the bump sitting on a symmetry point. It was
not a formality. On the **centred** family the hand-rolled adaptive Simpson
routine passes at every width — because the bump sits exactly on the midpoint
abscissa that Simpson's rule always samples. Read alone, the centred family
would have supported the opposite conclusion: that one independent
implementation among five is robust, and that differential testing therefore
works.

It was not robust. It was lucky in where the probe was placed. Moving the bump
to `x = 1/3` collapses it to silent failure from `w = 1e-2` down.

Had the off-centre family been added *after* seeing the centred results, it
would have been indistinguishable from selection on the outcome. Declaring it
first is what makes the finding usable.

## Better driving recovers the answer only if you already know it

TR-2026-06 established that an apparent engine limit can measure how the engine
was driven rather than what it can do. That question must be asked here, and the
answer is a qualified no.

| off-centre `w` | default | `scipy` told where the mass is | `mpmath` split at the mass |
|---:|---:|---:|---:|
| `1e-3` | `0.0` | `1.772e-03` ✓ | `1.772e-03` ✓ |
| `1e-6` | `0.0` | `0.0` ✗ | `1.772e-06` ✓ |
| `1e-10` | `0.0` | `0.0` ✗ | `1.772e-10` ✓ |
| `1e-12` | `0.0` | `0.0` ✗ | `1.772e-12` ✓ |

Supplying the bump location recovers the answer for `mpmath` at every width and
for `scipy` only at the widest. But that information is the answer's location —
in any real application it is exactly what is unknown.

Driving the routine *harder* without that information never works:

| `scipy.quad`, off-centre `w = 1e-6` | result |
|---|---|
| `limit=50, eps=1e-10` | `0.0` — missed |
| `limit=200, eps=1e-14` | `0.0` — missed |
| `limit=2000, eps=1e-14` | `0.0` — missed |
| `limit=10000, eps=1e-16` | `0.0` — missed |

So the blindness is not a defect in any routine and is not reachable by
tightening tolerances. It follows from deciding convergence by sampling a
function at finitely many points, which every routine must do. This is the same
shape as the dynamics result, where the shared failure followed from binary64
representation plus an unstable equilibrium rather than from any code path.

## Independence that is not independence

`scipy.integrate.quad` and R's `integrate()` present as independent — different
languages, different projects, different authors, different documentation. Both
descend from QUADPACK. They were included as a declared pair to measure what
that costs.

They return the **identical verdict in all 18 cells**, with a worst-case
relative disagreement in value of `1.6e-07`. A practitioner who cross-checks a
Python result against R, and concludes from their agreement that the answer is
sound, has learned almost nothing. This parallels TR-2026-01's argument for
abandoning a SymPy oracle when SymPy is among the engines under test:
independence of authorship is not independence of algorithm.

## Full verdict counts

| Implementation | pass | silent | loud |
|---|---:|---:|---:|
| `scipy.quad` (QUADPACK) | 5 | 13 | 0 |
| R `integrate()` (QUADPACK) | 5 | 13 | 0 |
| `mpmath.quad` (tanh–sinh) | 2 | 7 | 9 |
| adaptive Simpson (NumPy) | 10 | 8 | 0 |
| fixed Simpson (NumPy) | 4 | 14 | 0 |

`mpmath` is the only routine that is ever honest about being wrong, and it is
honest in nine cells — all of them in the centred family, where it warns rather
than going silent. In the off-centre family it goes silent with the others.
Being the most careful implementation in the set does not confer immunity.

## Limitations

**One integrand shape.** Both families are Gaussian bumps differing only in
centre. A narrow bump is the most direct way to defeat sampling, and it is
therefore the easiest case; whether the same agreement-in-failure holds for
oscillatory integrands, endpoint singularities, or discontinuities is not tested
here.

**One axis.** Width alone was swept, as declared. Interval length, integrand
amplitude, and requested tolerance are all held fixed.

**Five implementations, three independent families.** More independent families
would strengthen the agreement statistic. Three is the same number the dynamics
study used, which is deliberate, but it is not many.

**Default settings.** Routines are driven at their defaults, which is the
realistic case and the one a practitioner meets, but it is a choice. The driving
section above bounds what changes when that choice is relaxed.

**The phenomenon is known.** The novelty claimed is the differential-testing
framing and the measured bit-identical agreement, not the existence of quadrature
failure.

## Disclosure

The author of this replication also authors the silent-failure study whose
central claim is under test, so a positive result supports the author's own prior
conclusion. The falsification conditions were fixed in `SCOPE.md` before
measurement and the raw per-cell results are published in `results.csv` rather
than summarised. AI assistance was used in this work.

## Reproducing

```
python run.py        # writes results.csv, 90 cells
python analyse.py    # every table in this report
```

Requires Python with `numpy`, `scipy`, `mpmath`, and R with `integrate()` for
the fifth implementation. The R adapter is skipped with a notice if R is absent.
Nothing is stochastic; the numbers are exactly reproducible.
