from __future__ import annotations


def test_q4_annual_event_simulation_is_nonnegative_and_seeded():
    from q4_validation import simulate_annual_events

    rows_a = simulate_annual_events(10, 2.0, 0.5, 1.0, 0.1, 5, 19)
    rows_b = simulate_annual_events(10, 2.0, 0.5, 1.0, 0.1, 5, 19)
    assert rows_a == rows_b
    assert all(row["avoidances"] >= 0 and row["failures"] >= 0 for row in rows_a)


def test_q4_higher_debris_density_increases_conjunction_rate():
    from q4_config import AvoidanceParameters, DebrisEnvironment, MissionParameters
    from q4_validation import run_q4_sensitivity

    rows = run_q4_sensitivity(1480, DebrisEnvironment(), AvoidanceParameters(), MissionParameters(1480))
    low = next(row for row in rows if row["scenario"] == "density_x0.5")
    high = next(row for row in rows if row["scenario"] == "density_x2")
    assert high["annual_conjunction_rate"] > low["annual_conjunction_rate"]
