from __future__ import annotations

import numpy as np
import pytest


def test_q3_block_bootstrap_is_seeded_and_preserves_constant_rate():
    from q3_validation import bootstrap_time_blocks

    rates = np.array([0.8, 0.8, 0.8])
    draws = bootstrap_time_blocks(rates, replicates=20, seed=5)
    assert draws == pytest.approx([0.8] * 20)


def test_q3_sensitivity_has_baseline_and_four_one_factor_rows(monkeypatch):
    from types import SimpleNamespace

    import q3_validation
    from q3_config import ConstellationParams, Q3Config, SimulationConfig

    def fake_evaluate(*_args, **_kwargs):
        return (
            SimpleNamespace(
                c1=1.0,
                c2=0.99,
                p30_all=0.85,
                p30_reachable=0.90,
                reachable_count=10,
                late_reachable_count=1,
                unreachable_count=1,
                max_delay_s=0.04,
            ),
            None,
        )

    monkeypatch.setattr(q3_validation, "evaluate_joint_candidate", fake_evaluate)
    rows = q3_validation.run_q3_sensitivity(
        ConstellationParams(planes=2, sats_per_plane=2, phase_factor=0, inclination_deg=50.0),
        object(),
        object(),
        Q3Config(),
        SimulationConfig(),
    )
    assert len(rows) == 5
    assert rows[0]["scenario"] == "baseline"
