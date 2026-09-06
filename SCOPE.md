# SCOPE — Shared Blind Spots Outside Rigid-Body Dynamics

**Declared 6 September 2026, before any measurement was taken.**
This file is the authority on what this study asks and what would count as an
answer. It follows the governance rule of the silent-failure study: the probe
family and the axis are fixed here, before the numbers exist; extension is
permitted where it adds adjudication without revising an existing verdict;
removing a probe after seeing its result is selection on the outcome and is
forbidden.

## The claim under replication

The silent-failure study
(<https://doi.org/10.5281/zenodo.22458147>) argues that differential testing
detects the failures independent implementations make *independently*, and is
structurally blind to the failures they **share**. Its evidence is one instance
in one domain: at the inverted equilibrium of a pendulum chain, three rigid-body
dynamics engines and an independent closed-form reference all report success
while returning roughly 20 radians of motion for a configuration whose exact
solution does not move.

One instance in one domain is an anecdote. This study asks whether the
phenomenon reproduces in a **second, unrelated domain**, and whether the
mechanism is the same.

## Question

> In adaptive numerical quadrature, does there exist a family of integrands on
> which every independently implemented routine returns the same wrong answer
> while reporting convergence — so that no amount of cross-implementation
> comparison detects the error, and only a closed-form reference does?

## Why quadrature

The mechanism proposed in the dynamics case is that the failure is a property of
the **shared representation and the shared strategy**, not of any code path.
Adaptive quadrature has that structure exposed in the open: every routine decides
convergence by comparing estimates built from a finite set of sampled abscissae.
If the integrand's mass lies entirely between the points a routine happens to
sample, it sees a smooth near-zero function, converges, and reports a small error
estimate. Adding an independently written routine does not help, because the
blindness follows from sampling a function at finitely many points, which every
routine must do.

This makes quadrature a strong test: if the phenomenon is real and general, it
must appear here. If it does not, the dynamics result is more likely specific to
unstable equilibria than to differential testing as a method.

## The probe family (frozen)

A narrow Gaussian bump on a fixed interval, with the exact integral in closed
form:

```
f_w(x) = exp(-(x/w)^2)          on [-1, 1]
∫ f_w = w * sqrt(pi) * erf(1/w)
```

The exact value is elementary, is not obtained from any quadrature routine, and
shares no code with any implementation under test. For `w << 1` it approaches
`w*sqrt(pi)`, but the `erf` form is used throughout so the reference is exact at
every width.

A second family is declared now so that it cannot be added later to rescue a
result — an off-centre bump, to rule out the possibility that any effect is an
artefact of the bump sitting exactly on a symmetry point or on an abscissa:

```
g_w(x) = exp(-((x - 1/3)/w)^2)  on [-1, 1]
∫ g_w = w * sqrt(pi)/2 * (erf((1 - 1/3)/w) + erf((1 + 1/3)/w))
```

## The axis (declared before measurement)

**Bump width `w`**, swept over
`1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8, 1e-10, 1e-12`.

This is the analogue of the amplitude axis in the dynamics study: a single knob,
declared in advance, along which the integrand becomes progressively harder to
find by sampling while the exact answer stays known and non-zero.

## Implementations under test

Independence is judged by the criterion the dynamics study used — *shares no
library* — which is stronger than independent authorship.

| Implementation | Basis | Independent of |
|---|---|---|
| `scipy.integrate.quad` | QUADPACK (Fortran) | mpmath, the NumPy routines |
| R `integrate()` | QUADPACK (C translation) | mpmath, the NumPy routines |
| `mpmath.quad` | tanh–sinh, pure Python | all others |
| adaptive Simpson | NumPy only, written here | all others |
| fixed-grid Simpson | NumPy only, written here | all others |

**Declared in advance:** `scipy.integrate.quad` and R's `integrate()` are *not*
independent of one another. Both descend from QUADPACK. They are included as a
pair precisely because they present as independent — different languages,
different projects, different authors, different documentation — while sharing
the algorithm and its adaptive subdivision strategy. Whether they fail together
is recorded as a separate result from whether the genuinely independent routines
fail together.

## Adjudication

For each (implementation, family, width) the harness records the returned value,
the routine's own error estimate where it provides one, any warning or status
flag, and the relative error against the closed-form reference.

A cell is a **silent failure** when all three hold:

1. relative error against the closed-form value exceeds `1e-3`;
2. the routine reports convergence — no exception, no warning, and where an
   error estimate is returned, that estimate implies a relative error below
   `1e-6`;
3. the routine returns a finite number.

A cell is a **loud failure** when the routine is wrong and says so, by exception,
warning, or an honest error estimate. Loud failures are acceptable behaviour and
are counted separately, exactly as in the dynamics study.

## What would falsify the replication

- If no width produces a silent failure in any implementation, the phenomenon
  does not reproduce here.
- If the implementations disagree with each other where they are wrong, then
  differential testing **does** detect the failure, and the central claim — that
  the blindness is shared — fails even if individual routines are wrong.

The second is the one that matters. The claim is not that quadrature can be
made to fail; that is textbook. The claim is that the independent
implementations fail **in agreement**, so that comparing them detects nothing.

## Disclosure

The author of this study also authors the silent-failure study whose central
claim is under replication here. That is a conflict of interest: a positive
result supports the author's own prior conclusion. It is disclosed here, the
falsification conditions are fixed above before measurement, and the raw
per-cell results are reported in full rather than summarised.

AI assistance was used in this work.
