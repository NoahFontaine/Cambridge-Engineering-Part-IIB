#!/usr/bin/env python3
"""Create smooth, slowed SHM animations of the leading POD modes for each run."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import cv2
import numpy as np
from scipy import signal

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 900
PANEL_WIDTH = VIDEO_WIDTH // 2
PANEL_HEIGHT = VIDEO_HEIGHT // 2
PANEL_BACKGROUND = (255, 255, 255)
TEXT_COLOR = (35, 35, 35)


def _diverging_palette() -> np.ndarray:
    stops = np.array([
        (120, 35, 8),
        (200, 125, 25),
        (120, 75, 92),
        (45, 180, 240),
        (35, 35, 155),
    ], dtype=np.float64)
    positions = np.linspace(0, 255, len(stops))
    return np.column_stack([
        np.interp(np.arange(256), positions, stops[:, channel])
        for channel in range(3)
    ]).round().astype(np.uint8)


PALETTE = _diverging_palette()


def _read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV has no header: {path}") from exc
        return headers, list(reader)


def _run_label(path: Path, base: Path) -> str:
    relative = path.relative_to(base)
    for part in relative.parts:
        if re.fullmatch(r"run[_-]?\d+", part, flags=re.IGNORECASE):
            return part
    return relative.parent.name or relative.stem


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "run"


def _colorbar(height: int, width: int = 18) -> np.ndarray:
    gradient = np.linspace(255, 0, height, dtype=np.uint8)[:, None]
    return PALETTE[np.repeat(gradient, width, axis=1)]


def _draw_panel(
    canvas: np.ndarray,
    panel_index: int,
    mode_number: int,
    energy_fraction: float,
    coefficient: float,
    measured_frequency_hz: float,
    display_frequency_hz: float,
    field: np.ndarray,
    mask: np.ndarray,
    color_limit: float,
    animation_time_s: float,
) -> None:
    column, row = panel_index % 2, panel_index // 2
    x0, y0 = column * PANEL_WIDTH, row * PANEL_HEIGHT
    panel = canvas[y0 : y0 + PANEL_HEIGHT, x0 : x0 + PANEL_WIDTH]
    panel[:] = PANEL_BACKGROUND
    cv2.rectangle(panel, (0, 0), (PANEL_WIDTH - 1, PANEL_HEIGHT - 1), (185, 185, 185), 1)

    cv2.putText(
        panel,
        f"Mode {mode_number}  |  energy {energy_fraction:.2%}",
        (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.72, TEXT_COLOR, 2, cv2.LINE_AA,
    )
    cv2.putText(
        panel,
        f"SHM coefficient: {coefficient:.4g}",
        (18, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.58, TEXT_COLOR, 1, cv2.LINE_AA,
    )
    cv2.putText(
        panel,
        f"POD peak: {measured_frequency_hz:.3g} Hz  |  shown: {display_frequency_hz:.3g} Hz",
        (18, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.46, TEXT_COLOR, 1, cv2.LINE_AA,
    )

    normalized = np.clip(field / color_limit, -1.0, 1.0)
    grayscale = np.rint((normalized + 1.0) * 127.5).astype(np.uint8)
    image = PALETTE[grayscale]
    image[~mask] = (255, 255, 255)
    image_height, image_width = field.shape
    available_width, available_height = PANEL_WIDTH - 92, PANEL_HEIGHT - 134
    scale = min(available_width / image_width, available_height / image_height)
    resized_width = max(1, round(image_width * scale))
    resized_height = max(1, round(image_height * scale))
    image = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
    image_x = 18 + (available_width - resized_width) // 2
    image_y = 92 + (available_height - resized_height) // 2
    panel[image_y : image_y + resized_height, image_x : image_x + resized_width] = image

    bar = _colorbar(resized_height)
    bar_x = min(PANEL_WIDTH - 40, image_x + resized_width + 12)
    panel[image_y : image_y + resized_height, bar_x : bar_x + bar.shape[1]] = bar
    cv2.putText(
        panel, f"+{color_limit:.3g}",
        (bar_x - 8, max(82, image_y - 6)), cv2.FONT_HERSHEY_SIMPLEX,
        0.38, TEXT_COLOR, 1, cv2.LINE_AA,
    )
    cv2.putText(
        panel, f"-{color_limit:.3g}",
        (bar_x - 8, min(PANEL_HEIGHT - 48, image_y + resized_height + 16)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.38, TEXT_COLOR, 1, cv2.LINE_AA,
    )
    cv2.putText(
        panel,
        f"Animation time: {animation_time_s:.3f} s  |  fixed color scale",
        (18, PANEL_HEIGHT - 14), cv2.FONT_HERSHEY_SIMPLEX,
        0.48, TEXT_COLOR, 1, cv2.LINE_AA,
    )


def _fit_shm(values: np.ndarray, times: np.ndarray) -> tuple[float, float, float, float]:
    sample_rate = 1.0 / float(np.median(np.diff(times)))
    frequencies, power = signal.periodogram(
        values, fs=sample_rate, window="hann",
        detrend="constant", scaling="density",
    )
    positive = frequencies > 0
    if not positive.any() or not np.isfinite(power[positive]).all():
        raise ValueError("POD coefficient has no finite non-zero frequency content")
    positive_frequencies, positive_power = frequencies[positive], power[positive]
    peak_indices, _ = signal.find_peaks(
        positive_power, prominence=float(np.max(positive_power)) * 0.05
    )
    if peak_indices.size:
        peak_indices = peak_indices[np.argsort(positive_power[peak_indices])]
        peak_index = int(peak_indices[-1])
    else:
        peak_index = int(np.argmax(positive_power))
    frequency = float(positive_frequencies[peak_index])
    phase = 2 * np.pi * frequency * (times - times[0])
    design = np.column_stack((np.cos(phase), np.sin(phase), np.ones(times.size)))
    fit, *_ = np.linalg.lstsq(design, values, rcond=None)
    if not np.isfinite(fit).all():
        raise ValueError("Could not fit a finite harmonic to POD coefficient")
    return frequency, float(fit[0]), float(fit[1]), float(fit[2])


def _write_run_video(
    energy_path: Path,
    output_path: Path,
    video_fps: float,
    display_frequency_hz: float,
    cycles: int,
) -> dict[str, object]:
    run_directory = energy_path.parent
    mode_path = run_directory / "pod_modes.npz"
    coefficient_path = run_directory / "pod_coefficients.csv"
    if not mode_path.is_file() or not coefficient_path.is_file():
        raise FileNotFoundError(f"Missing POD modes or coefficients in {run_directory}")

    energy_headers, energy_rows = _read_csv(energy_path)
    mode_column = energy_headers.index("mode")
    energy_column = energy_headers.index("energy_fraction")
    energy = {
        int(row[mode_column]): float(row[energy_column]) for row in energy_rows
    }
    if len(energy) < 4:
        raise ValueError(f"At least four POD modes are required in {energy_path}")
    if not np.isfinite(list(energy.values())).all():
        raise ValueError(f"POD energy fractions must be finite in {energy_path}")
    top_modes = sorted(energy, key=energy.get, reverse=True)[:4]

    with np.load(mode_path) as data:
        modes = data["modes"]
        mask = data["analysis_mask"].astype(bool)
    if modes.ndim != 2 or mask.ndim != 2 or modes.shape[0] != int(mask.sum()):
        raise ValueError(f"Incompatible mode array and analysis mask in {mode_path}")
    if any(mode < 1 or mode > modes.shape[1] for mode in top_modes):
        raise ValueError(f"Energy table refers to missing spatial modes in {energy_path}")

    coefficient_headers, coefficient_rows = _read_csv(coefficient_path)
    time_column = coefficient_headers.index("time_s")
    times = np.asarray([float(row[time_column]) for row in coefficient_rows])
    if times.size < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError(f"POD timestamps must be finite and increasing in {coefficient_path}")
    spatial_modes = np.empty((len(top_modes), int(mask.sum())), dtype=np.float32)
    shm_fits = []
    for index, mode in enumerate(top_modes):
        column = coefficient_headers.index(f"mode_{mode}")
        coefficients = np.asarray([float(row[column]) for row in coefficient_rows])
        spatial_modes[index] = modes[:, mode - 1]
        if not np.isfinite(coefficients).all():
            raise ValueError(f"POD coefficients must be finite in {coefficient_path}")
        shm_fits.append(_fit_shm(coefficients, times))
    if not np.isfinite(spatial_modes).all():
        raise ValueError(f"POD modes and coefficients must be finite in {run_directory}")

    spatial_fields = np.zeros((4, *mask.shape), dtype=np.float32)
    for index in range(4):
        spatial_fields[index][mask] = spatial_modes[index]
    fitted_amplitudes = np.asarray([
        float(np.hypot(fit[1], fit[2])) for fit in shm_fits
    ])
    color_limits = np.asarray([
        max(fitted_amplitudes[index] * float(np.max(np.abs(spatial_fields[index]))), 1e-12)
        for index in range(4)
    ])
    animation_duration_s = cycles / display_frequency_hz
    frame_count = max(2, int(round(animation_duration_s * video_fps)))
    animation_times = np.arange(frame_count, dtype=float) / video_fps
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), video_fps,
        (VIDEO_WIDTH, VIDEO_HEIGHT),
    )
    if not writer.isOpened():
        raise OSError(f"Could not open MP4 writer for {output_path}")
    try:
        for animation_time_s in animation_times:
            canvas = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
            for index, mode in enumerate(top_modes):
                frequency, cosine_component, sine_component, _ = shm_fits[index]
                phase = 2 * np.pi * display_frequency_hz * animation_time_s
                coefficient = (
                    cosine_component * np.cos(phase) + sine_component * np.sin(phase)
                )
                contribution = spatial_fields[index] * coefficient
                _draw_panel(
                    canvas, index, mode, energy[mode],
                    float(coefficient), frequency, display_frequency_hz, contribution,
                    mask, float(color_limits[index]), float(animation_time_s),
                )
            writer.write(canvas)
    finally:
        writer.release()

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise OSError(f"MP4 output was not written: {output_path}")
    return {
        "run": _run_label(energy_path, energy_path.parents[2]),
        "video": str(output_path),
        "top_modes": ",".join(str(mode) for mode in top_modes),
        "physical_frequency_hz_by_mode": ",".join(
            f"{mode}:{fit[0]:.12g}" for mode, fit in zip(top_modes, shm_fits)
        ),
        "display_frequency_hz": display_frequency_hz,
        "effective_slowdown_by_mode": ",".join(
            f"{mode}:{fit[0] / display_frequency_hz:.6g}"
            for mode, fit in zip(top_modes, shm_fits)
        ),
        "shm_fit_amplitude_by_mode": ",".join(
            f"{mode}:{amplitude:.6g}" for mode, amplitude in zip(top_modes, fitted_amplitudes)
        ),
        "frames": frame_count,
        "video_fps": video_fps,
        "cycles": cycles,
        "playback_duration_s": float(frame_count / video_fps),
        "data_start_time_s": float(times[0]),
        "data_end_time_s": float(times[-1]),
    }


def create_videos(
    pod_dir: Path,
    output_dir: Path,
    video_fps: float = 30.0,
    display_frequency_hz: float = 0.25,
    cycles: int = 3,
) -> list[dict[str, object]]:
    if not np.isfinite(video_fps) or video_fps <= 0:
        raise ValueError("--video-fps must be finite and positive")
    if not np.isfinite(display_frequency_hz) or display_frequency_hz <= 0:
        raise ValueError("--display-frequency-hz must be finite and positive")
    if cycles < 1:
        raise ValueError("--cycles must be positive")
    energy_files = sorted(pod_dir.rglob("pod_energy.csv"))
    if not energy_files:
        raise ValueError(f"No POD results found under {pod_dir}")
    summaries = []
    for energy_path in energy_files:
        relative = energy_path.parent.relative_to(pod_dir)
        output_path = output_dir / relative.parent / f"{relative.name}_pod_top4.mp4"
        result = _write_run_video(
            energy_path, output_path, video_fps, display_frequency_hz, cycles
        )
        summaries.append(result)
        print(f"Wrote {output_path}")
    summary_path = output_dir / "pod_mode_videos.csv"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pod-dir", type=Path, default=Path("results/pod"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/pod_mode_videos_slow_color")
    )
    parser.add_argument(
        "--video-fps", type=float, default=30.0,
        help="Playback frame rate; use 30 or higher for smooth motion",
    )
    parser.add_argument(
        "--display-frequency-hz", type=float, default=0.25,
        help="Harmonic visualization frequency, independent of the measured POD frequency",
    )
    parser.add_argument(
        "--cycles", type=int, default=3,
        help="Number of smooth SHM cycles to show for each mode",
    )
    args = parser.parse_args()
    try:
        summaries = create_videos(
            args.pod_dir, args.output_dir, args.video_fps,
            args.display_frequency_hz, args.cycles,
        )
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    print(f"Wrote {len(summaries)} POD videos and {args.output_dir / 'pod_mode_videos.csv'}")


if __name__ == "__main__":
    main()
