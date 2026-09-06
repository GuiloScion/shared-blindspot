"""run.py -- the harness. Runs every implementation over the frozen probe grid,
adjudicates each cell against the closed-form reference, and writes results.csv.

Adjudication thresholds are fixed in SCOPE.md:
    silent failure  = relative error > 1e-3, no warning, no exception, and any
                      self-reported error estimate implying rel err < 1e-6
    loud failure    = wrong, and said so
"""

import csv
import os
import subprocess
import sys

from probes import cases, exact
from adapters import ADAPTERS

REL_WRONG = 1e-3      # wrong by more than this counts as wrong
REL_CLAIM = 1e-6      # a claim tighter than this counts as claiming convergence

R_BIN = r"C:\Program Files\R\R-4.6.1\bin\x64\Rscript.exe"


def classify(value, claimed, warned, error, truth):
    """Returns (verdict, relative error, claimed relative error)."""
    if error:
        return "loud (exception)", None, None
    if value is None or value != value:          # None or NaN
        return "loud (non-finite)", None, None

    denom = abs(truth) if truth != 0 else 1.0
    rel = abs(value - truth) / denom
    claim_rel = (abs(claimed) / denom) if claimed is not None else None

    if rel <= REL_WRONG:
        return "pass", rel, claim_rel
    # wrong -- did it say so?
    if warned:
        return "loud (warned)", rel, claim_rel
    if claim_rel is not None and claim_rel >= REL_CLAIM:
        return "loud (honest error estimate)", rel, claim_rel
    return "SILENT", rel, claim_rel


def run_r():
    """R adapter, out of process. Returns raw rows or [] if R is unavailable."""
    if not os.path.exists(R_BIN):
        print("  (R not found; skipping R integrate)", file=sys.stderr)
        return []
    out = subprocess.run([R_BIN, "adapter_r.R"], capture_output=True, text=True)
    if out.returncode != 0:
        print("  (R adapter failed)\n", out.stderr[-600:], file=sys.stderr)
        return []
    rows = []
    for rec in csv.DictReader(out.stdout.splitlines()):
        def num(s):
            try:
                return float(s)
            except (TypeError, ValueError):
                return None
        rows.append(dict(
            implementation=rec["implementation"],
            family=rec["family"],
            w=float(rec["width"]),
            value=num(rec["value"]),
            claimed=num(rec["claimed"]),
            warned=rec["warned"] == "true",
            error=rec["error"] or None,
        ))
    return rows


def main():
    raw = []
    for name, fn in ADAPTERS.items():
        print(f"running {name} ...")
        for family, w in cases():
            r = fn(family, w)
            raw.append(dict(implementation=name, family=family, w=w, **r))

    print("running R integrate (QUADPACK) ...")
    raw.extend(run_r())

    rows = []
    for r in raw:
        truth = exact(r["family"], r["w"])
        verdict, rel, claim_rel = classify(
            r["value"], r["claimed"], r["warned"], r["error"], truth)
        rows.append(dict(
            implementation=r["implementation"], family=r["family"], width=r["w"],
            exact=truth, value=r["value"], rel_error=rel,
            claimed_abs=r["claimed"], claimed_rel=claim_rel,
            warned=r["warned"], error=r["error"], verdict=verdict))

    with open("results.csv", "w", newline="", encoding="utf-8") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)
    print(f"\nwrote results.csv ({len(rows)} cells)")
    return rows


if __name__ == "__main__":
    main()
