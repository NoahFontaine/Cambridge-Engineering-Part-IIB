import csv
from pathlib import Path

import numpy as np

from visualize_analysis import _find_peaks, visualize


def test_find_peaks_returns_prominent_peaks_in_power_order():
    frequencies = np.arange(1, 10, dtype=float)
    power = np.array([0.1, 1.0, 0.1, 0.1, 0.8, 0.1, 0.1, 0.1, 0.1])

    peaks = _find_peaks(frequencies, power, 0.1)

    assert [peak[0] for peak in peaks] == [2.0, 5.0]


def test_visualize_writes_psd_peaks_and_pod_diagnostics(tmp_path: Path):
    psd_dir = tmp_path / "psd"
    pod_run = tmp_path / "pod" / "run14" / "run14"
    output_dir = tmp_path / "visualizations"
    psd_run = psd_dir / "run14" / "run14"
    psd_run.mkdir(parents=True)
    pod_run.mkdir(parents=True)

    with (psd_run / "unsteadiness_rms_psd.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frequency_hz", "psd_signal"])
        writer.writerows(zip(range(1, 10), [0.1, 1, 0.1, 0.1, 0.8, 0.1, 0.1, 0.1, 0.1]))
    with (pod_run / "pod_energy.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["mode", "singular_value", "energy_fraction", "cumulative_energy_fraction"])
        writer.writerows([[1, 1, 0.7, 0.7], [2, 1, 0.3, 1.0]])
    sample_rate = 100.0
    times = np.arange(256) / sample_rate
    with (pod_run / "pod_coefficients.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame_index", "time_s", "mode_1", "mode_2"])
        writer.writerows(
            (i, time, np.sin(2 * np.pi * 8 * time), np.sin(2 * np.pi * 12 * time))
            for i, time in enumerate(times)
        )

    visualize(psd_dir, tmp_path / "pod", output_dir)

    with (output_dir / "psd_peak_summary.csv").open(newline="") as handle:
        psd_rows = list(csv.DictReader(handle))
    assert [float(row["frequency_hz"]) for row in psd_rows] == [2.0, 5.0]
    with (output_dir / "pod_mode_summary.csv").open(newline="") as handle:
        mode_rows = list(csv.DictReader(handle))
    mode_one = next(row for row in mode_rows if row["mode"] == "1")
    assert abs(float(mode_one["dominant_frequency_hz"]) - 8.0) < 0.3
    assert int(mode_one["coefficient_samples"]) == 256
    assert (output_dir / "psd_runs" / "run14_run14_unsteadiness_rms_psd.png").is_file()
    assert (output_dir / "pod_runs" / "run14_run14.png").is_file()
    assert (output_dir / "pod_energy_heatmap.png").is_file()
    assert (output_dir / "pod_frequency_heatmap.png").is_file()
