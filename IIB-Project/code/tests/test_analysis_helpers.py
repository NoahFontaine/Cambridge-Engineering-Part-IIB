from pathlib import Path

import cv2
import numpy as np

from analyze_shadowgraph import hysteresis_update, parse_roi, track_shock
from shadowgraph_pipeline import roi_mask, scaled_settings, video_settings
from track_flow import _overall_state, _region_state, write_shock_motion_video


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


def test_shock_motion_video_marks_tracked_position_and_time(tmp_path: Path):
    source = tmp_path / "source.avi"
    writer = cv2.VideoWriter(
        str(source), cv2.VideoWriter_fourcc(*"MJPG"), 30, (64, 48)
    )
    assert writer.isOpened()
    try:
        for _ in range(3):
            writer.write(np.full((48, 64, 3), 100, dtype=np.uint8))
    finally:
        writer.release()

    output = tmp_path / "shock_motion.mp4"
    write_shock_motion_video(
        source, output, [20.0, float("nan"), 24.0], [0.0, 0.1, 0.2],
        (10, 5, 40, 35), 1, 1.0, 30.0,
    )

    capture = cv2.VideoCapture(str(output))
    try:
        assert capture.isOpened()
        assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 3
        ok, frame = capture.read()
        assert ok
        assert frame[40, 20, 2] > frame[40, 20, 1] + 30
        ok, frame = capture.read()
        assert ok
        ok, frame = capture.read()
        assert ok
        assert frame[40, 24, 2] > frame[40, 24, 1] + 30
    finally:
        capture.release()


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


def test_full_frame_analysis_mask_includes_aerofoil_polygon():
    record = {
        "rois": {
            "shock": [0, 0, 2, 2],
            "separation_bubble": None,
            "boundary_layer": [0, 0, 2, 2],
            "exclude": {"polygon": [[1, 1], [3, 1], [1, 3]]},
        }
    }
    rois = scaled_settings(record, 5, 5, 1.0)
    mask = roi_mask(rois, (5, 5), full_frame=True)
    assert mask.sum() == 25
    assert mask[1, 1]
    assert mask[2, 1]
    assert mask[4, 4]
    assert mask[4, 0]
