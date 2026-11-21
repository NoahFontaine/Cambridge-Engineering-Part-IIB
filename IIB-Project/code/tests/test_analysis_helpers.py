from pathlib import Path

import numpy as np

from analyze_shadowgraph import hysteresis_update, parse_roi, track_shock
from shadowgraph_pipeline import roi_mask, scaled_settings, video_settings
from track_flow import _overall_state, _region_state


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


def test_roi_mask_unions_flow_regions_and_excludes_aerofoil():
    mask = roi_mask(
        {
            "shock": (0, 0, 3, 2),
            "separation_bubble": None,
            "boundary_layer": (2, 1, 5, 3),
            "exclude": (2, 1, 3, 2),
        },
        (3, 5),
    )
    assert mask.sum() == 10
    assert not mask[1, 2]
    assert mask[0, 0]
    assert mask[2, 4]


def test_attachment_classification_supports_intermittent_states():
    assert _region_state(0.2, 0.35, 0.65) == "attached"
    assert _region_state(0.8, 0.35, 0.65) == "detached"
    assert _region_state(0.5, 0.35, 0.65) == "transition"
    assert _overall_state(["attached"] * 9 + ["detached"]) == "attached"
    assert _overall_state(["attached"] * 5 + ["detached"] * 5) == "intermittent"


def test_single_video_can_match_manifest_key_from_video_root():
    settings = {"rois": {"boundary_layer": [1, 2, 10, 12]}}
    result = video_settings(
        {"run14/run14.mp4": settings},
        Path("/data/videos/run14/run14.mp4"),
        None,
    )
    assert result is settings


def test_polygon_exclusion_masks_only_the_selected_shape():
    record = {
        "rois": {
            "shock": None,
            "separation_bubble": None,
            "boundary_layer": [0, 0, 8, 8],
            "exclude": {"polygon": [[1, 1], [6, 1], [1, 6]]},
        }
    }
    rois = scaled_settings(record, 8, 8, 1.0)
    mask = roi_mask(rois, (8, 8))
    assert not mask[2, 2]
    assert not mask[5, 1]
    assert mask[5, 5]
