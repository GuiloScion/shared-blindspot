"""analyse.py -- adjudication tables from results.csv, plus the driving probe.

Run after run.py. Prints the verdict grid, the agreement-in-failure statistic
that the replication turns on, the QUADPACK provenance comparison, and the
test of whether better driving recovers the answer.
"""

import csv
import itertools
import warnings

WRONG_BUT_AGREEING = "the statistic the replication turns on"


def load(path="results.csv"):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def cell(rows, impl, fam, w):
    return next((r for r in rows
                 if r["implementation"] == impl and r["family"] == fam
                 and abs(float(r["width"]) - w) < 1e-30), None)


def grid(rows):
    impls = sorted({r["implementation"] for r in rows})
    widths = sorted({float(r["width"]) for r in rows}, reverse=True)
    for fam in ("centred", "offcentre"):
        print(f"\n=== verdict grid: {fam} ===")
        head = f"{'width':>7} | " + " | ".join(f"{i[:24]:>24}" for i in impls)
        print(head)
        print("-" * len(head))
        for w in widths:
            out = []
            for i in impls:
                r = cell(rows, i, fam, w)
                v = r["verdict"]
                tag = "pass" if v == "pass" else ("SILENT" if v == "SILENT" else "loud")
                rel = f"{float(r['rel_error']):.1e}" if r["rel_error"] else "--"
                out.append(f"{tag:>6} {rel:>9}")
            print(f"{w:7.0e} | " + " | ".join(f"{o:>24}" for o in out))


def agreement(rows):
    """Cells where every implementation is silently wrong, and how far apart
    their wrong answers are. Agreement here is what makes differential testing
    useless."""
    widths = sorted({float(r["width"]) for r in rows}, reverse=True)
    print(f"\n=== all-silent cells, and pairwise spread ({WRONG_BUT_AGREEING}) ===")
    print(f"{'family':10} {'width':>8} {'n':>3}  {'max pairwise rel spread':>24}  {'exact':>12}")
    n_all_silent = n_bit_identical = 0
    for fam in ("centred", "offcentre"):
        for w in widths:
            d = [r for r in rows if r["family"] == fam
                 and abs(float(r["width"]) - w) < 1e-30]
            if not d or not all(r["verdict"] == "SILENT" for r in d):
                continue
            vals = [float(r["value"]) for r in d]
            scale = max(abs(v) for v in vals) or 1.0
            spread = (max(abs(a - b) for a, b in itertools.combinations(vals, 2))
                      / scale) if len(vals) > 1 else 0.0
            n_all_silent += 1
            n_bit_identical += (spread == 0.0)
            print(f"{fam:10} {w:8.0e} {len(d):3}  {spread:24.3e}  "
                  f"{float(d[0]['exact']):12.3e}")
    print(f"\n  {n_all_silent} cells where every implementation is silently wrong")
    print(f"  {n_bit_identical} of those where every returned value is bit-identical")


def provenance(rows):
    """scipy.quad and R integrate() both descend from QUADPACK. Declared in
    SCOPE.md as a pair that presents as independent and is not."""
    print("\n=== scipy.quad vs R integrate(): shared QUADPACK provenance ===")
    widths = sorted({float(r["width"]) for r in rows}, reverse=True)
    worst = 0.0
    n = 0
    for fam in ("centred", "offcentre"):
        for w in widths:
            a = cell(rows, "scipy.quad (QUADPACK)", fam, w)
            b = cell(rows, "R integrate (QUADPACK)", fam, w)
            if not a or not b:
                continue
            av, bv = float(a["value"]), float(b["value"])
            rel = abs(av - bv) / max(abs(av), abs(bv), 1e-300)
            worst = max(worst, rel)
            n += 1
            assert a["verdict"] == b["verdict"], (fam, w)
    print(f"  identical verdict in all {n} cells; "
          f"worst relative disagreement in value {worst:.1e}")


def driving():
    """TR-2026-06 asks whether a limit is the engine or the driving. Here:
    can the routine find the mass if driven better, or if driven harder?"""
    from scipy.integrate import quad
    import mpmath
    from probes import integrand, exact, A, B, OFFSET

    print("\n=== can better driving recover the answer? (off-centre) ===")
    print(f"{'w':>8} {'default':>12} {'scipy +points':>14} {'mpmath +split':>14} {'exact':>12}")
    for w in (1e-3, 1e-6, 1e-10, 1e-12):
        f, ex = integrand("offcentre", w), exact("offcentre", w)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d, _ = quad(f, A, B)
            h, _ = quad(f, A, B, points=[OFFSET])
        m = float(mpmath.quad(f, [A, OFFSET, B]))
        print(f"{w:8.0e} {d:12.3e} {h:14.3e} {m:14.3e} {ex:12.3e}")

    print("\n=== can it be found by tightening tolerances, without knowing where? ===")
    w = 1e-6
    f, ex = integrand("offcentre", w), exact("offcentre", w)
    for lim, tol in ((50, 1e-10), (200, 1e-14), (2000, 1e-14), (10000, 1e-16)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v, _ = quad(f, A, B, limit=lim, epsabs=tol, epsrel=tol)
        ok = abs(v - ex) / ex < 1e-3
        print(f"  limit={lim:6} eps={tol:.0e} -> {v:.3e}  "
              f"(exact {ex:.3e})  {'found' if ok else 'MISSED'}")


if __name__ == "__main__":
    rows = load()
    grid(rows)
    agreement(rows)
    provenance(rows)
    driving()
