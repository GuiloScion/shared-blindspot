"""adapters.py -- one adapter per quadrature implementation.

Each returns a dict with:
    value      the routine's answer
    claimed    the routine's own absolute error estimate, or None
    warned     True if the routine emitted a warning or non-OK status
    error      exception text, or None

No adapter is allowed to consult the reference. Adjudication happens in run.py.
"""

import warnings
import numpy as np

from probes import integrand, A, B


def _run(fn):
    """Capture warnings and exceptions uniformly, so that 'said something was
    wrong' is measured the same way for every implementation."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            value, claimed = fn()
            return dict(value=value, claimed=claimed,
                        warned=len(caught) > 0, error=None)
        except Exception as exc:                     # noqa: BLE001
            return dict(value=None, claimed=None,
                        warned=len(caught) > 0,
                        error=f"{type(exc).__name__}: {exc}")


# --------------------------------------------------------------- QUADPACK
def scipy_quad(family, w):
    from scipy.integrate import quad
    f = integrand(family, w)

    def go():
        value, abserr = quad(f, A, B)
        return value, abserr

    return _run(go)


# --------------------------------------------------------------- tanh-sinh
def mpmath_quad(family, w):
    import mpmath
    f = integrand(family, w)

    def go():
        value, err = mpmath.quad(f, [A, B], error=True)
        return float(value), float(err)

    return _run(go)


# --------------------------------------------------- adaptive Simpson, NumPy
def adaptive_simpson(family, w, tol=1e-10, max_depth=50):
    """Textbook adaptive Simpson with Richardson error control. NumPy only --
    no quadrature library, no shared code with QUADPACK or mpmath."""
    f = integrand(family, w)

    def go():
        def simpson(a, b):
            m = 0.5 * (a + b)
            return (b - a) / 6.0 * (f(a) + 4.0 * f(m) + f(b)), m

        def recurse(a, b, whole, fa, fm, fb, eps, depth):
            m = 0.5 * (a + b)
            lm, ln = 0.5 * (a + m), 0.5 * (m + b)
            flm, fln = f(lm), f(ln)
            left = (m - a) / 6.0 * (fa + 4.0 * flm + fm)
            right = (b - m) / 6.0 * (fm + 4.0 * fln + fb)
            delta = left + right - whole
            if depth <= 0 or abs(delta) <= 15.0 * eps:
                # Richardson-corrected value, and the error it implies
                return left + right + delta / 15.0, abs(delta) / 15.0
            lv, le = recurse(a, m, left, fa, flm, fm, eps / 2.0, depth - 1)
            rv, re = recurse(m, b, right, fm, fln, fb, eps / 2.0, depth - 1)
            return lv + rv, le + re

        fa, fb = f(A), f(B)
        whole, m = simpson(A, B)
        fm = f(m)
        return recurse(A, B, whole, fa, fm, fb, tol, max_depth)

    return _run(go)


# ------------------------------------------------ fixed-grid Simpson, NumPy
def fixed_simpson(family, w, n=1001):
    """Composite Simpson on a fixed grid. Has no error estimate at all, so it
    can never report anything but success -- included as the limiting case of
    a routine that cannot see its own blindness."""
    f = integrand(family, w)

    def go():
        xs = np.linspace(A, B, n)
        ys = np.array([f(x) for x in xs])
        h = (B - A) / (n - 1)
        value = h / 3.0 * (ys[0] + ys[-1]
                           + 4.0 * ys[1:-1:2].sum()
                           + 2.0 * ys[2:-1:2].sum())
        return float(value), None

    return _run(go)


ADAPTERS = {
    "scipy.quad (QUADPACK)":  scipy_quad,
    "mpmath.quad (tanh-sinh)": mpmath_quad,
    "adaptive Simpson (NumPy)": adaptive_simpson,
    "fixed Simpson (NumPy)":   fixed_simpson,
}
