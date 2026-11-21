import numpy as np

from analyze_shadowgraph import hysteresis_update, parse_roi, track_shock


def test_parse_roi_returns_native_pixel_bounds():
    assert parse_roi("10, 20, 90, 120") == (10, 20, 90, 120)


def test_track_shock_finds_subpixel_step():
    profile = np.zeros(80, dtype=np.float32)
    profile[38:] = 200
    x, strength = track_shock(profile, 25, 0, 2)
    assert abs(x - 62.5) < 0.1
    assert strength >= 100


def test_hysteresis_retains_state_between_thresholds():
    state = np.array([False, True, False])
    result = hysteresis_update(state, np.array([120, 100, 80]), 90, 110)
    np.testing.assert_array_equal(result, [True, True, False])
