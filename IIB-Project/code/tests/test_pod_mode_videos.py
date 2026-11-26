import csv
from pathlib import Path

import cv2
import numpy as np

from pod_mode_videos import PALETTE, _fit_shm, create_videos


def test_diverging_palette_avoids_white():
    assert PALETTE.shape == (256, 3)
    assert np.all(np.max(PALETTE, axis=1) < 245)
    assert np.max(PALETTE[128]) < 150


def test_create_videos_uses_four_highest_energy_modes(tmp_path: Path):
    pod_run = tmp_path / "pod" / "run3" / "run3"
    output_dir = tmp_path / "videos"
    pod_run.mkdir(parents=True)

    with (pod_run / "pod_energy.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["mode", "energy_fraction"])
        writer.writerows([[1, 0.1], [2, 0.4], [3, 0.05], [4, 0.3], [5, 0.15]])

    mask = np.ones((16, 16), dtype=bool)
    modes = np.zeros((mask.sum(), 5), dtype=np.float32)
    modes[10, :] = 1
    np.savez_compressed(pod_run / "pod_modes.npz", modes=modes, analysis_mask=mask)

    with (pod_run / "pod_coefficients.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame_index", "time_s", *[f"mode_{i}" for i in range(1, 6)]])
        for frame in range(256):
            time_s = frame / 100
            coefficients = [
                np.sin(2 * np.pi * (5 + mode) * time_s) for mode in range(1, 6)
            ]
            writer.writerow([frame, time_s, *coefficients])

    summaries = create_videos(tmp_path / "pod", output_dir, 30.0, 1.0)

    video_path = output_dir / "run3" / "run3_pod_top4.mp4"
    assert summaries[0]["top_modes"] == "2,4,5,1"
    assert summaries[0]["frames"] == 90
    assert summaries[0]["video_fps"] == 30.0
    assert summaries[0]["playback_duration_s"] == 3.0
    assert summaries[0]["display_frequency_hz"] == 1.0
    assert "2:7.03125" in summaries[0]["physical_frequency_hz_by_mode"]
    assert video_path.is_file()
    capture = cv2.VideoCapture(str(video_path))
    try:
        assert capture.isOpened()
        assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 90
        assert capture.get(cv2.CAP_PROP_FPS) == 30.0
        assert int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 1280
        assert int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 900
        ok, frame = capture.read()
        assert ok
        assert frame.shape == (900, 1280, 3)
    finally:
        capture.release()


def test_fit_shm_extracts_dominant_frequency_and_amplitude():
    times = np.arange(500) / 100.0
    values = 2.5 * np.cos(2 * np.pi * 6 * times) - 1.25 * np.sin(2 * np.pi * 6 * times) + 4

    frequency, cosine_component, sine_component, offset = _fit_shm(values, times)

    assert abs(frequency - 6.0) < 1e-10
    assert abs(cosine_component - 2.5) < 1e-10
    assert abs(sine_component + 1.25) < 1e-10
    assert abs(offset - 4.0) < 1e-10


def test_fit_shm_uses_dominant_local_peak_over_low_frequency_drift():
    times = np.arange(1000) / 100.0
    values = (
        3 * np.sin(2 * np.pi * 0.1 * times)
        + np.sin(2 * np.pi * 6 * times)
    )

    frequency, *_ = _fit_shm(values, times)

    assert abs(frequency - 6.0) < 0.11
