"""Full-sidereal-day grid scan for Problem 2 minimum-satellite search.

Unlike the fast critical-point screen, this evaluates every candidate on the
authoritative grid-time coverage model over a FULL sidereal day, because the
fixed target region requires the full day (a 6 h window over-reports coverage;
see 18-...松弛与假设驱动加速方案.md §15.6 / Q2-R01).

For each total satellite count S it records the best candidate by
(c_min>=1, C1, -max_gap) and streams results, so a long run can be inspected or
resumed.  Uses relaxation Q2-R02 (fix Omega0=0, search only u0).
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

import q2_constellation as q2
from run_q2_fast_search import factor_pairs_for_search

ROOT = Path(__file__).resolve().parent


def scan_candidates(total, *, max_pairs, inclinations, u0_count, phase_factors):
    """Yield ConstellationParams for one total (Q2-R02: raan0 fixed to 0)."""
    pairs = factor_pairs_for_search(total)[:max_pairs]
    for planes, sats in pairs:
        u_width = 360.0 / sats
        u0_values = np.linspace(0.0, u_width, u0_count, endpoint=False)
        for inc in inclinations:
            for f in phase_factors:
                if not (0 <= f < planes):
                    continue
                for u0 in u0_values:
                    yield q2.ConstellationParams(
                        planes=planes, sats_per_plane=sats, phase_factor=int(f),
                        inclination_deg=float(inc), raan0_deg=0.0, u0_deg=float(u0),
                    )


def score(rec):
    return (1 if rec["c_min"] >= 1 else 0, rec["C1"], -rec["max_gap_s"])


def main():
    ap = argparse.ArgumentParser(description="Problem 2 full-day grid scan.")
    ap.add_argument("--totals", type=str, default="800,1000,1200,1400,1600")
    ap.add_argument("--grid-step", type=float, default=2.0)
    ap.add_argument("--time-step", type=float, default=300.0)
    ap.add_argument("--duration-hours", type=float, default=q2.SIDEREAL_DAY_S / 3600.0)
    ap.add_argument("--max-pairs", type=int, default=4)
    ap.add_argument("--inclinations", type=str, default="50,53")
    ap.add_argument("--u0-count", type=int, default=4)
    ap.add_argument("--phase-factors", type=str, default="0")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "q2_fullday_scan")
    args = ap.parse_args()

    totals = [int(x) for x in args.totals.split(",") if x.strip()]
    inclinations = [float(x) for x in args.inclinations.split(",") if x.strip()]
    phase_factors = [int(x) for x in args.phase_factors.split(",") if x.strip()]
    cfg = q2.CoverageConfig()
    lat, lon = q2.make_latlon_grid(step_deg=args.grid_step)
    times = q2.make_time_grid(args.duration_hours * 3600.0, args.time_step)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    stream = out / "scan_stream.csv"
    best_per_total = {}
    t_start = time.perf_counter()
    n_eval = 0

    for total in totals:
        best = None
        for p in scan_candidates(
            total, max_pairs=args.max_pairs, inclinations=inclinations,
            u0_count=args.u0_count, phase_factors=phase_factors,
        ):
            r = q2.evaluate_constellation(p, lat, lon, times, cfg)
            n_eval += 1
            rec = {
                "total_satellites": p.total_satellites, "planes": p.planes,
                "sats_per_plane": p.sats_per_plane, "phase_factor": p.phase_factor,
                "inclination_deg": p.inclination_deg, "u0_deg": round(p.u0_deg, 3),
                "C1": round(r.coverage_rate_q1, 6), "c_min": r.c_min,
                "max_gap_s": r.max_gap_s, "avg_mult": round(r.avg_multiplicity, 4),
                "C2_area": round(r.coverage_rate_q2, 6),
                "C2_strict": round(r.strict_double_time_rate, 6),
            }
            write_header = not stream.exists() or stream.stat().st_size == 0
            with stream.open("a", newline="", encoding="utf-8-sig") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rec.keys()))
                if write_header:
                    w.writeheader()
                w.writerow(rec)
            if best is None or score(rec) > score(best):
                best = rec
        best_per_total[total] = best
        print(f"[S={total}] best: M={best['planes']} N={best['sats_per_plane']} "
              f"i={best['inclination_deg']} C1={best['C1']:.5f} c_min={best['c_min']} "
              f"gap={best['max_gap_s']:.0f}s C2s={best['C2_strict']:.3f} "
              f"(elapsed {time.perf_counter()-t_start:.0f}s, {n_eval} evals)", flush=True)

    strict = [t for t, b in best_per_total.items() if b and b["c_min"] >= 1]
    relaxed = [t for t, b in best_per_total.items() if b and b["C1"] >= 0.999]
    summary = {
        "totals": totals, "grid_step_deg": args.grid_step, "time_step_s": args.time_step,
        "duration_hours": args.duration_hours, "num_evaluated": n_eval,
        "elapsed_s": round(time.perf_counter() - t_start, 1),
        "best_per_total": best_per_total,
        "min_strict_feasible_S": min(strict) if strict else None,
        "min_relaxed_C1_0999_S": min(relaxed) if relaxed else None,
    }
    (out / "scan_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SCAN DONE ->", out / "scan_summary.json", flush=True)


if __name__ == "__main__":
    main()
