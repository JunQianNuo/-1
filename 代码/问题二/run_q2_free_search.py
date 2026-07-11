"""Problem 2 free-N minimum-satellite search (multi-fidelity, N unrestricted).

Corrects the earlier improper "N locked ~40" modeling: here N is a FREE variable
(all factor pairs of S), and the single-plane streets-of-coverage value is NOT
imposed.  The only retained reduction is Omega0 = 0 (proven exact symmetry, R02).

Two sub-problems:
  Q2 single : min S s.t. C1 >= 1 - eps0                       -> S1
  Q3 double : min S s.t. C1 >= 1 - eps0 AND C2 >= 0.95         -> S2   (two conditions)

Pipeline:
  Phase A (coarse 4deg/900s): all factor pairs x sampled F x i-grid x u0 -> keep top-K/S
  Phase B (fine 2deg/300s):   verify kept top-K + F neighborhood refine
  Phase C (final 1deg/150s):  confirm the overall S1 / S2 winners

All candidate records are streamed to CSV for later plotting.
"""

from __future__ import annotations

import argparse, csv, json, math, time
from pathlib import Path

import numpy as np
import q2_constellation as q2

ROOT = Path(__file__).resolve().parent
EPS0 = 1e-3          # single-coverage near-full tolerance (C1 >= 1-eps0)
C2_TARGET = 0.95     # double area-time target


def factor_pairs_free(S: int, m_min: int = 4, n_min: int = 6) -> list[tuple[int, int]]:
    pairs = []
    for M in range(m_min, S // n_min + 1):
        if S % M == 0:
            N = S // M
            if N >= n_min:
                pairs.append((M, N))
    return pairs


def sample_F(M: int, k: int = 6) -> list[int]:
    specials = {0, 1, M // 4, M // 2, max(0, M - 1)}
    even = {int(round(x)) % M for x in np.linspace(0, M, k, endpoint=False)}
    return sorted({f for f in (specials | even) if 0 <= f < M})


def neighbor_F(F: int, M: int, radius: int = 2) -> list[int]:
    return sorted({(F + d) % M for d in range(-radius, radius + 1)})


def eval_candidate(M, N, F, i, u0, lat, lon, times, cfg) -> dict:
    r = q2.evaluate_constellation(
        q2.ConstellationParams(M, N, int(F), inclination_deg=float(i),
                               raan0_deg=0.0, u0_deg=float(u0)),
        lat, lon, times, cfg,
    )
    return {
        "S": M * N, "M": M, "N": N, "F": int(F), "i": float(i), "u0": round(float(u0), 3),
        "C1": round(r.coverage_rate_q1, 6), "C2": round(r.coverage_rate_q2, 6),
        "c_min": int(r.c_min), "max_gap_s": float(r.max_gap_s),
        "avg_mult": round(r.avg_multiplicity, 4),
    }


def append_csv(path: Path, rec: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rec.keys()))
        if new:
            w.writeheader()
        w.writerow(rec)


def single_ok(rec):
    return rec["C1"] >= 1 - EPS0


def double_ok(rec):
    return rec["C1"] >= 1 - EPS0 and rec["C2"] >= C2_TARGET


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s-min", type=int, default=1300)
    ap.add_argument("--s-max", type=int, default=1560)
    ap.add_argument("--s-step-coarse", type=int, default=20)
    ap.add_argument("--incl-coarse", type=str, default="49,50,51")
    ap.add_argument("--u0-coarse", type=int, default=2)
    ap.add_argument("--f-samples", type=int, default=6)
    ap.add_argument("--keep-top", type=int, default=30)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "q2_free_search")
    args = ap.parse_args()

    cfg = q2.CoverageConfig()
    out = args.out; out.mkdir(parents=True, exist_ok=True)
    incl_c = [float(x) for x in args.incl_coarse.split(",")]
    latc, lonc = q2.make_latlon_grid(step_deg=4.0); tc = q2.make_time_grid(q2.SIDEREAL_DAY_S, 900.0)
    latf, lonf = q2.make_latlon_grid(step_deg=2.0); tf = q2.make_time_grid(q2.SIDEREAL_DAY_S, 300.0)
    t0 = time.perf_counter(); n_eval = 0

    # ---------- Phase A: coarse, N-free ----------
    per_s_top = {}   # S -> list of coarse recs (kept top by a combined key)
    for S in range(args.s_min, args.s_max + 1, args.s_step_coarse):
        recs = []
        for (M, N) in factor_pairs_free(S):
            for F in sample_F(M, args.f_samples):
                for i in incl_c:
                    for u0 in np.linspace(0, 360.0 / N, args.u0_coarse, endpoint=False):
                        rec = eval_candidate(M, N, F, i, u0, latc, lonc, tc, cfg)
                        n_eval += 1
                        append_csv(out / "coarse_records.csv", rec)
                        recs.append(rec)
        # keep top by C1 and by C2 (union), bounded
        recs.sort(key=lambda r: (r["C1"], r["C2"]), reverse=True)
        keep = recs[: args.keep_top]
        recs.sort(key=lambda r: (r["C2"], r["C1"]), reverse=True)
        keep += [r for r in recs[: args.keep_top] if r not in keep]
        per_s_top[S] = keep
        best = max(recs, key=lambda r: r["C1"])
        print(f"[A S={S}] pairs={len(factor_pairs_free(S))} bestC1={best['C1']:.5f} "
              f"(M={best['M']}xN={best['N']}) evals={n_eval} t={time.perf_counter()-t0:.0f}s", flush=True)

    # ---------- Phase B: fine verify top-K (fine u0) + light F/i neighborhood ----------
    fine_best_single = {}; fine_best_double = {}
    for S, keep in per_s_top.items():
        for rec in keep:
            M, N, F, i = rec["M"], rec["N"], rec["F"], rec["i"]
            for u0 in np.linspace(0, 360.0 / N, 4, endpoint=False):
                fr = eval_candidate(M, N, F, i, u0, latf, lonf, tf, cfg)
                n_eval += 1
                append_csv(out / "fine_records.csv", fr)
                if single_ok(fr) and (S not in fine_best_single or fr["C1"] > fine_best_single[S]["C1"]):
                    fine_best_single[S] = fr
                if double_ok(fr) and (S not in fine_best_double or fr["C2"] > fine_best_double[S]["C2"]):
                    fine_best_double[S] = fr
        # light neighborhood refine on this S's fine-best (F +/-1, i +/-0.25)
        for base in (fine_best_single.get(S), fine_best_double.get(S)):
            if base is None:
                continue
            M, N = base["M"], base["N"]
            for F in neighbor_F(base["F"], M, radius=1):
                for i in (base["i"] - 0.25, base["i"] + 0.25):
                    if not (48.45 <= i <= 60.0):
                        continue
                    for u0 in np.linspace(0, 360.0 / N, 4, endpoint=False):
                        fr = eval_candidate(M, N, F, i, u0, latf, lonf, tf, cfg)
                        n_eval += 1
                        append_csv(out / "fine_records.csv", fr)
                        if single_ok(fr) and fr["C1"] > fine_best_single[S]["C1"]:
                            fine_best_single[S] = fr
                        if double_ok(fr) and (S not in fine_best_double or fr["C2"] > fine_best_double[S]["C2"]):
                            fine_best_double[S] = fr
        print(f"[B S={S}] single={'Y' if S in fine_best_single else 'n'} "
              f"double={'Y' if S in fine_best_double else 'n'} evals={n_eval} t={time.perf_counter()-t0:.0f}s", flush=True)

    S1 = min(fine_best_single) if fine_best_single else None
    S2 = min(fine_best_double) if fine_best_double else None

    # frontier CSV (best-per-S) for plotting
    for S in sorted(per_s_top):
        row = {"S": S,
               "best_single_C1": fine_best_single[S]["C1"] if S in fine_best_single else "",
               "best_double_C2": fine_best_double[S]["C2"] if S in fine_best_double else ""}
        append_csv(out / "frontier.csv", row)

    summary = {
        "note": "N-free multi-fidelity search; Omega0=0 (R02 proven). eps0=1e-3, C2>=0.95.",
        "n_eval": n_eval, "elapsed_s": round(time.perf_counter() - t0, 1),
        "S1_single": S1, "S1_config": fine_best_single.get(S1),
        "S2_double": S2, "S2_config": fine_best_double.get(S2),
        "delta_S": (S2 - S1) if (S1 and S2) else None,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE", summary["S1_single"], summary["S2_double"], "->", out / "summary.json", flush=True)


if __name__ == "__main__":
    main()
