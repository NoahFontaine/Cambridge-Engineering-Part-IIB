#!/usr/bin/env python3
"""Extract shock and separation-unsteadiness metrics from a shadowgraph video."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterator

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage, signal

from run_metadata import infer_run_number, load_run_frame_rates


def parse_roi(value: str | None) -> tuple[int, int, int, int] | None:
    if value is None:
        return None
    try:
        coords = tuple(int(item.strip()) for item in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ROI must be four comma-separated integers") from exc
    if len(coords) != 4:
        raise argparse.ArgumentTypeError("ROI must be x0,y0,x1,y1")
    x0, y0, x1, y1 = coords
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
        raise argparse.ArgumentTypeError("ROI must have non-negative origin and positive width/height")
    return x0, y0, x1, y1


def scaled_roi(
    roi: tuple[int, int, int, int] | None,
    width: int,
    height: int,
    scale: float,
) -> tuple[int, int, int, int]:
    if roi is None:
        return 0, 0, width, height
    x0, y0, x1, y1 = (int(round(value * scale)) for value in roi)
    if x1 > width or y1 > height or x0 >= width or y0 >= height:
        raise ValueError(f"ROI {roi} exceeds analyzed frame dimensions {width}x{height}")
    x1, y1 = min(x1, width), min(y1, height)
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"ROI {roi} is empty at analysis scale {scale}")
    return x0, y0, x1, y1


def gray_frame(frame: np.ndarray, scale: float) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if scale != 1.0:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return gray


def mean_profile(
    gray: np.ndarray, roi: tuple[int, int, int, int]
) -> np.ndarray:
    x0, y0, x1, y1 = roi
    return gray[y0:y1, x0:x1].astype(np.float32).mean(axis=0)


def track_shock(
    profile: np.ndarray,
    x_origin: int,
    smooth_sigma: float,
    min_gradient: float,
) -> tuple[float, float]:
    """Return subpixel x and peak gradient; a weak edge is reported as NaN."""
    smoothed = ndimage.gaussian_filter1d(profile, smooth_sigma) if smooth_sigma > 0 else profile
    gradient = np.abs(np.gradient(smoothed))
    if gradient.size < 3:
        return math.nan, 0.0
    peak = int(np.argmax(gradient[1:-1])) + 1
    peak_value = float(gradient[peak])
    if peak_value < min_gradient:
        return math.nan, peak_value
    left, center, right = gradient[peak - 1 : peak + 2]
    denominator = left - 2.0 * center + right
    offset = 0.5 * (left - right) / denominator if denominator != 0 else 0.0
    offset = float(np.clip(offset, -1.0, 1.0))
    return x_origin + peak + offset, peak_value


def hysteresis_update(
    state: np.ndarray,
    profile: np.ndarray,
    low: float,
    high: float,
) -> np.ndarray:
    state[profile >= high] = True
    state[profile <= low] = False
    return state


def iter_video(
    path: Path, frame_step: int, scale: float
) -> Iterator[tuple[int, np.ndarray]]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise OSError(f"Could not open video: {path}")
    frame_index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % frame_step == 0:
                yield frame_index, gray_frame(frame, scale)
            frame_index += 1
    finally:
        capture.release()


def percentile_position(values: np.ndarray, probability: float) -> float | None:
    return float(np.quantile(values, probability)) if values.size else None


def save_map(path: Path, data: np.ndarray, title: str, colorbar_label: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    image = ax.imshow(data, cmap="inferno", origin="upper", aspect="auto")
    ax.set(title=title, xlabel="x (analysis pixels)", ylabel="y (analysis pixels)")
    fig.colorbar(image, ax=ax, label=colorbar_label)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--video", required=True, type=Path, help="Input video file")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for CSV, JSON, and plots")
    parser.add_argument("--fps", type=float, help="Original camera acquisition rate (not the 30 fps playback rate)")
    parser.add_argument("--run-matrix", type=Path, help="Excel run matrix; the original camera rate is read from its Run Log")
    parser.add_argument("--run-number", type=int, help="Run number in the Excel matrix; otherwise inferred from the video path")
    parser.add_argument("--frame-step", type=int, default=1, help="Analyze every Nth frame")
    parser.add_argument("--scale", type=float, default=1.0, help="Resize factor for analysis; coordinates are specified at native resolution")
    parser.add_argument("--stats-roi", type=parse_roi, help="ROI for scalar pixel-SD index at native resolution; defaults to full frame")
    parser.add_argument("--sd-threshold", type=float, default=15.0, help="Pixel-SD threshold in grayscale levels for the thresholded scalar index")
    parser.add_argument("--shock-roi", type=parse_roi, help="Expected shock search box at native resolution: x0,y0,x1,y1")
    parser.add_argument("--shock-smooth", type=float, default=1.5, help="Gaussian smoothing sigma in analysis pixels")
    parser.add_argument("--min-gradient", type=float, default=2.0, help="Reject shock detections weaker than this grayscale gradient per pixel")
    parser.add_argument("--gamma-roi", type=parse_roi, help="Wall-parallel strip for gamma(x): x0,y0,x1,y1 at native resolution")
    parser.add_argument("--gamma-low", type=float, help="Lower hysteresis threshold in grayscale levels, 0-255")
    parser.add_argument("--gamma-high", type=float, help="Upper hysteresis threshold in grayscale levels, 0-255")
    parser.add_argument("--gamma-invert", action="store_true", help="Invert grayscale before applying gamma thresholds")
    parser.add_argument("--bubble-roi", type=parse_roi, help="ROI behind the shock for a thresholded bubble-signature analysis")
    parser.add_argument("--bubble-reference-frame", type=int, help="Optional native video frame known to have no bubble signature")
    parser.add_argument("--bubble-diff-threshold", type=int, default=12, help="Minimum absolute difference from the temporal-mean image, 0-255")
    parser.add_argument("--min-component-area", type=int, default=8, help="Discard smaller connected components in analysis pixels")
    parser.add_argument("--bubble-step", type=int, default=1, help="Analyze bubble signature on every Nth analyzed frame")
    parser.add_argument("--mm-per-pixel", type=float, help="Spatial calibration in mm per native-resolution pixel")
    parser.add_argument("--length-scale-mm", type=float, help="Optional characteristic length for St=fL/U")
    parser.add_argument("--velocity-m-s", type=float, help="Optional reference velocity for Strouhal number")
    parser.add_argument("--max-interpolated-fraction", type=float, default=0.05, help="Maximum missing shock-position fraction allowed for PSD interpolation")
    return parser


def analyze(args: argparse.Namespace) -> dict[str, object]:
    if args.frame_step < 1 or args.bubble_step < 1:
        raise ValueError("--frame-step and --bubble-step must be at least 1")
    if not 0 < args.scale <= 1:
        raise ValueError("--scale must be in (0, 1]")
    if args.shock_smooth < 0 or args.min_gradient < 0:
        raise ValueError("Smoothing and minimum gradient cannot be negative")
    if (args.gamma_low is None) != (args.gamma_high is None):
        raise ValueError("Provide both --gamma-low and --gamma-high, or neither")
    if args.gamma_low is not None and not 0 <= args.gamma_low < args.gamma_high <= 255:
        raise ValueError("Gamma thresholds must satisfy 0 <= low < high <= 255")
    if args.bubble_diff_threshold < 0 or args.bubble_diff_threshold > 255:
        raise ValueError("--bubble-diff-threshold must be in [0, 255]")
    if args.bubble_reference_frame is not None and args.bubble_reference_frame < 0:
        raise ValueError("--bubble-reference-frame must be non-negative")
    if args.min_component_area < 1 or not 0 <= args.max_interpolated_fraction <= 1:
        raise ValueError("Area must be positive and interpolated fraction must be in [0, 1]")
    if args.mm_per_pixel is not None and args.mm_per_pixel <= 0:
        raise ValueError("--mm-per-pixel must be positive")
    if (args.length_scale_mm is None) != (args.velocity_m_s is None):
        raise ValueError("Provide both --length-scale-mm and --velocity-m-s for Strouhal number")
    if args.length_scale_mm is not None and args.length_scale_mm <= 0:
        raise ValueError("--length-scale-mm must be positive")
    if args.velocity_m_s is not None and args.velocity_m_s <= 0:
        raise ValueError("--velocity-m-s must be positive")

    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise OSError(f"Could not open video: {args.video}")
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    native_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    native_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()
    run_number = args.run_number
    if args.run_matrix is not None:
        run_number = run_number if run_number is not None else infer_run_number(args.video)
        rates = load_run_frame_rates(args.run_matrix)
        if run_number not in rates:
            raise ValueError(f"Run {run_number} has no frame rate in {args.run_matrix}")
        matrix_fps = rates[run_number]
        if args.fps is not None and not math.isclose(args.fps, matrix_fps):
            raise ValueError(
                f"--fps {args.fps} conflicts with run {run_number} matrix rate {matrix_fps}"
            )
        fps = matrix_fps
        fps_source = f"run_matrix:{args.run_matrix.resolve()}#run={run_number}"
    elif args.fps is not None:
        fps = args.fps
        fps_source = "command_line"
    else:
        raise ValueError(
            "Original camera acquisition rate is required. Pass --fps or --run-matrix "
            "(and optionally --run-number); container playback fps is not the sampling rate."
        )
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("Video frame rate is unavailable; pass --fps")
    effective_fps = fps / args.frame_step
    width = max(1, int(round(native_width * args.scale)))
    height = max(1, int(round(native_height * args.scale)))
    shock_roi = scaled_roi(args.shock_roi, width, height, args.scale)
    stats_roi = scaled_roi(args.stats_roi, width, height, args.scale)
    gamma_roi = scaled_roi(args.gamma_roi, width, height, args.scale) if args.gamma_low is not None else None
    bubble_roi = scaled_roi(args.bubble_roi, width, height, args.scale) if args.bubble_roi is not None else None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    shock_rows_roi = shock_roi
    sx0, _, sx1, _ = shock_rows_roi
    moments = [np.zeros((height, width), dtype=np.float64) for _ in range(4)]
    shock_positions: list[float] = []
    shock_gradients: list[float] = []
    times: list[float] = []
    xt_profiles: list[np.ndarray] = []
    gamma_state: np.ndarray | None = None
    gamma_counts: np.ndarray | None = None
    gamma_frame_count = 0
    first_frame: np.ndarray | None = None
    bubble_reference: np.ndarray | None = None
    if gamma_roi is not None:
        gx0, gy0, gx1, gy1 = gamma_roi
        gamma_state = np.zeros(gx1 - gx0, dtype=bool)
        gamma_counts = np.zeros(gx1 - gx0, dtype=np.uint64)

    count = 0
    for frame_index, gray in iter_video(args.video, args.frame_step, args.scale):
        if first_frame is None:
            first_frame = gray.copy()
        if frame_index == args.bubble_reference_frame:
            bubble_reference = gray.copy()
        image = gray.astype(np.float64)
        count += 1
        image2 = image * image
        moments[0] += image
        moments[1] += image2
        moments[2] += image2 * image
        moments[3] += image2 * image2
        profile = mean_profile(gray, shock_rows_roi)
        position, gradient = track_shock(profile, sx0, args.shock_smooth, args.min_gradient)
        shock_positions.append(position)
        shock_gradients.append(gradient)
        times.append(frame_index / fps)
        xt_profiles.append(profile.astype(np.uint8))

        if gamma_roi is not None and gamma_state is not None and gamma_counts is not None:
            gamma_profile = mean_profile(gray, gamma_roi)
            if args.gamma_invert:
                gamma_profile = 255.0 - gamma_profile
            hysteresis_update(gamma_state, gamma_profile, args.gamma_low, args.gamma_high)
            gamma_counts += gamma_state
            gamma_frame_count += 1

    if count == 0:
        raise ValueError(f"No frames were decoded from {args.video}")

    mean = moments[0] / count
    raw_variance = np.maximum(moments[1] / count - mean**2, 0.0)
    sample_sd = np.sqrt(raw_variance * count / (count - 1)) if count > 1 else np.zeros_like(mean)
    central3 = moments[2] / count - 3 * mean * (moments[1] / count) + 2 * mean**3
    central4 = (
        moments[3] / count
        - 4 * mean * (moments[2] / count)
        + 6 * mean**2 * (moments[1] / count)
        - 3 * mean**4
    )
    denom3 = np.power(raw_variance, 1.5)
    skewness = np.divide(central3, denom3, out=np.zeros_like(mean), where=denom3 > 1e-12)
    kurtosis = np.divide(central4, raw_variance**2, out=np.zeros_like(mean), where=raw_variance > 1e-12)
    np.savez_compressed(
        args.output_dir / "pixel_statistics.npz",
        mean=mean.astype(np.float32),
        sd=sample_sd.astype(np.float32),
        skewness=skewness.astype(np.float32),
        kurtosis=kurtosis.astype(np.float32),
    )
    save_map(args.output_dir / "mean.png", mean, "Mean shadowgraph intensity", "grayscale level")
    save_map(args.output_dir / "sd.png", sample_sd, "Pixel-wise intensity SD", "grayscale level")
    save_map(args.output_dir / "skewness.png", skewness, "Pixel-wise intensity skewness", "skewness")
    save_map(args.output_dir / "kurtosis.png", kurtosis, "Pixel-wise intensity kurtosis", "kurtosis (Gaussian = 3)")
    if first_frame is not None:
        preview = cv2.cvtColor(first_frame, cv2.COLOR_GRAY2BGR)
        for roi, color in (
            (shock_roi, (0, 0, 255)),
            (stats_roi, (0, 255, 0)),
            (gamma_roi, (255, 0, 0)),
            (bubble_roi, (255, 0, 255)),
        ):
            if roi is not None:
                cv2.rectangle(preview, roi[:2], (roi[2] - 1, roi[3] - 1), color, 2)
        cv2.imwrite(str(args.output_dir / "preview.png"), preview)

    positions = np.asarray(shock_positions, dtype=float)
    position_valid = np.isfinite(positions)
    valid_positions = positions[position_valid]
    shock_sd_px = float(np.std(valid_positions, ddof=1)) if valid_positions.size > 1 else None
    missing_fraction = 1.0 - float(position_valid.mean())
    position_mean_px = float(np.mean(valid_positions)) if valid_positions.size else None
    position_rms_px = (
        float(np.sqrt(np.mean((valid_positions - position_mean_px) ** 2)))
        if valid_positions.size else None
    )
    physical_scale = args.mm_per_pixel if args.mm_per_pixel is not None else None
    mm_per_analysis_pixel = (
        physical_scale / args.scale if physical_scale is not None else None
    )
    shock_sd_mm = (
        shock_sd_px * mm_per_analysis_pixel
        if mm_per_analysis_pixel is not None and shock_sd_px is not None else None
    )
    profile_stack = np.stack(xt_profiles, axis=0)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.imshow(
        profile_stack,
        cmap="gray",
        origin="upper",
        aspect="auto",
        extent=(sx0, sx1, times[-1] * 1000, times[0] * 1000),
    )
    ax.set(title="Space-time diagram (mean intensity across shock ROI rows)", xlabel="x (analysis pixels)", ylabel="time (ms)")
    fig.tight_layout()
    fig.savefig(args.output_dir / "xt_diagram.png", dpi=160)
    plt.close(fig)

    write_csv(
        args.output_dir / "shock_position.csv",
        ["time_s", "frame_index", "shock_x_px", "shock_x_mm", "shock_gradient"],
        [
            [
                time,
                int(round(time * fps)),
                position,
                position * mm_per_analysis_pixel
                if mm_per_analysis_pixel is not None and math.isfinite(position)
                else None,
                gradient,
            ]
            for time, position, gradient in zip(times, shock_positions, shock_gradients)
        ],
    )

    psd_peak_hz: float | None = None
    psd_calculated = False
    if valid_positions.size >= 16 and missing_fraction <= args.max_interpolated_fraction:
        sample_indices = np.arange(len(positions))
        clean_positions = np.interp(sample_indices, sample_indices[position_valid], positions[position_valid])
        nperseg = min(8192, max(256, len(clean_positions) // 20))
        nperseg = min(nperseg, len(clean_positions))
        frequencies, power = signal.welch(
            clean_positions,
            fs=effective_fps,
            window="hann",
            nperseg=nperseg,
            noverlap=nperseg // 2,
            detrend="constant",
            scaling="density",
        )
        psd_calculated = True
        write_csv(
            args.output_dir / "shock_psd.csv",
            ["frequency_hz", "psd_px2_per_hz"],
            list(zip(frequencies, power)),
        )
        positive_power = (frequencies > 0) & (power > 0)
        if np.any(positive_power):
            peak_index = int(np.argmax(power[1:]) + 1)
            psd_peak_hz = float(frequencies[peak_index])
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.loglog(frequencies[positive_power], power[positive_power])
            ax.set(title="Shock-position Welch PSD", xlabel="Frequency (Hz)", ylabel="PSD (analysis-pixel²/Hz)")
            ax.grid(True, which="both", alpha=0.25)
            fig.tight_layout()
            fig.savefig(args.output_dir / "shock_psd.png", dpi=160)
            plt.close(fig)

    gamma_mean: np.ndarray | None = None
    gamma_footprint_px: float | None = None
    gamma_footprint_mm: float | None = None
    if gamma_counts is not None and gamma_frame_count:
        gamma_mean = gamma_counts / gamma_frame_count
        gx0, _, _, _ = gamma_roi
        x_positions = np.arange(gx0, gx0 + len(gamma_mean), dtype=float)
        transition = np.flatnonzero((gamma_mean > 0.05) & (gamma_mean < 0.95))
        if transition.size:
            gamma_footprint_px = float(x_positions[transition[-1]] - x_positions[transition[0]] + 1)
            gamma_footprint_mm = gamma_footprint_px * args.mm_per_pixel / args.scale if args.mm_per_pixel else None
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(x_positions, gamma_mean)
        ax.axhline(0.05, color="grey", linestyle="--")
        ax.axhline(0.95, color="grey", linestyle="--")
        ax.set(title="Video-proxy intermittency profile", xlabel="x (analysis pixels)", ylabel="γ")
        ax.set_ylim(-0.02, 1.02)
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(args.output_dir / "gamma_profile.png", dpi=160)
        plt.close(fig)
        write_csv(args.output_dir / "gamma_profile.csv", ["x_px", "gamma"], list(zip(x_positions, gamma_mean)))

    bubble_rows: list[list[object]] = []
    bubble_summary: dict[str, object] = {}
    if bubble_roi is not None:
        # A second pass uses the final temporal-mean image as the reference field.
        bx0, by0, bx1, by1 = bubble_roi
        if args.bubble_reference_frame is not None and bubble_reference is None:
            raise ValueError(
                "Bubble reference frame was not sampled; choose a frame divisible by --frame-step"
            )
        reference = (
            bubble_reference
            if bubble_reference is not None
            else np.clip(np.rint(mean), 0, 255).astype(np.uint8)
        )
        kernel = np.ones((3, 3), dtype=np.uint8)
        frame_number = 0
        overlay_dir = args.output_dir / "bubble_overlays"
        overlay_dir.mkdir(exist_ok=True)
        bubble_count = math.ceil(count / args.bubble_step)
        overlay_indices = set(
            (
                np.linspace(0, bubble_count - 1, 10, dtype=int)
                * args.frame_step
                * args.bubble_step
            ).tolist()
        ) if bubble_count else set()
        for source_index, gray in iter_video(args.video, args.frame_step * args.bubble_step, args.scale):
            difference = cv2.absdiff(gray[by0:by1, bx0:bx1], reference[by0:by1, bx0:bx1])
            mask = cv2.threshold(difference, args.bubble_diff_threshold, 255, cv2.THRESH_BINARY)[1]
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            component_count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
            eligible = [
                i for i in range(1, component_count)
                if stats[i, cv2.CC_STAT_AREA] >= args.min_component_area
            ]
            selected = max(eligible, key=lambda i: stats[i, cv2.CC_STAT_AREA]) if eligible else None
            area = int(stats[selected, cv2.CC_STAT_AREA]) if selected is not None else 0
            if selected is None:
                x_left = x_right = y_top = y_bottom = math.nan
                signature_length_px = 0
            else:
                x_left = bx0 + int(stats[selected, cv2.CC_STAT_LEFT])
                y_top = by0 + int(stats[selected, cv2.CC_STAT_TOP])
                x_right = x_left + int(stats[selected, cv2.CC_STAT_WIDTH]) - 1
                y_bottom = y_top + int(stats[selected, cv2.CC_STAT_HEIGHT]) - 1
                signature_length_px = int(stats[selected, cv2.CC_STAT_WIDTH])
            bubble_time = source_index / fps
            bubble_rows.append([
                bubble_time,
                source_index,
                area,
                x_left,
                x_right,
                y_top,
                y_bottom,
                signature_length_px,
                int(area > 0),
            ])
            if source_index in overlay_indices:
                overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                if selected is not None:
                    overlay_roi = overlay[by0:by1, bx0:bx1]
                    overlay_roi[labels == selected] = (0, 0, 255)
                cv2.rectangle(overlay, (bx0, by0), (bx1 - 1, by1 - 1), (255, 0, 0), 1)
                cv2.imwrite(str(overlay_dir / f"frame_{source_index:07d}.jpg"), overlay)
            frame_number += 1
        if bubble_rows:
            bubble_values = np.asarray([row[2] for row in bubble_rows], dtype=float)
            states = np.asarray([row[8] for row in bubble_rows], dtype=np.int8)
            transitions = np.diff(np.r_[0, states, 0])
            starts = np.flatnonzero(transitions == 1)
            periods_s = np.diff(np.asarray([row[0] for row in bubble_rows])[starts]) if starts.size > 1 else np.array([])
            mean_area_px = float(np.mean(bubble_values))
            mean_period_s = float(np.mean(periods_s)) if periods_s.size else None
            bubble_summary = {
                "bubble_signature_presence_fraction": float(np.mean(states)),
                "mean_bubble_signature_area_px2": mean_area_px,
                "mean_bubble_signature_area_mm2": (
                    mean_area_px * (args.mm_per_pixel / args.scale) ** 2
                    if args.mm_per_pixel else None
                ),
                "mean_bubble_signature_extent_px": float(np.mean([row[7] for row in bubble_rows])),
                "mean_bubble_signature_extent_mm": (
                    float(np.mean([row[7] for row in bubble_rows]))
                    * args.mm_per_pixel / args.scale
                    if args.mm_per_pixel else None
                ),
                "mean_bubble_cycle_period_s": mean_period_s,
                "bubble_cycle_period_cv": (
                    float(np.std(periods_s, ddof=1) / mean_period_s)
                    if periods_s.size > 1 and mean_period_s else None
                ),
                "bubble_cycle_frequency_hz": (
                    float(1.0 / mean_period_s) if mean_period_s and mean_period_s > 0 else None
                ),
                "attached_dwell_mean_s": _mean_dwell(
                    states, effective_fps / args.bubble_step, False
                ),
                "separated_dwell_mean_s": _mean_dwell(
                    states, effective_fps / args.bubble_step, True
                ),
                "bubble_samples": frame_number,
            }
            write_csv(
                args.output_dir / "bubble_signature.csv",
                [
                    "time_s",
                    "frame_index",
                    "signature_area_px2",
                    "signature_x_min_px",
                    "signature_x_max_px",
                    "signature_y_min_px",
                    "signature_y_max_px",
                    "signature_extent_px",
                    "state",
                ],
                bubble_rows,
            )

    duration_s = (count - 1) / effective_fps if count > 1 else 0.0
    strouhal = (
        psd_peak_hz * (args.length_scale_mm / 1000.0) / args.velocity_m_s
        if psd_peak_hz is not None and args.length_scale_mm and args.velocity_m_s
        else None
    )
    summary: dict[str, object] = {
        "video": str(args.video.resolve()),
        "native_width_px": native_width,
        "native_height_px": native_height,
        "reported_video_fps": source_fps,
        "container_playback_fps": source_fps,
        "camera_acquisition_fps": fps,
        "fps_source": fps_source,
        "run_number": run_number,
        "analysis_fps": effective_fps,
        "frame_step": args.frame_step,
        "analysis_scale": args.scale,
        "frames_analyzed": count,
        "duration_s": duration_s,
        "shock_roi_analysis_px": list(shock_roi),
        "stats_roi_analysis_px": list(stats_roi),
        "shock_detections": int(valid_positions.size),
        "shock_missing_fraction": missing_fraction,
        "shock_mean_x_px": position_mean_px,
        "shock_mean_x_mm": (
            position_mean_px * mm_per_analysis_pixel
            if position_mean_px is not None and mm_per_analysis_pixel is not None else None
        ),
        "shock_sd_x_px": shock_sd_px,
        "shock_rms_about_mean_x_px": position_rms_px,
        "shock_sd_x_mm": shock_sd_mm,
        "shock_x_p05_px": percentile_position(valid_positions, 0.05),
        "shock_x_p95_px": percentile_position(valid_positions, 0.95),
        "shock_x_p05_mm": (
            percentile_position(valid_positions, 0.05) * mm_per_analysis_pixel
            if valid_positions.size and mm_per_analysis_pixel is not None else None
        ),
        "shock_x_p95_mm": (
            percentile_position(valid_positions, 0.95) * mm_per_analysis_pixel
            if valid_positions.size and mm_per_analysis_pixel is not None else None
        ),
        "mean_pixel_sd": float(np.mean(sample_sd[stats_roi[1]:stats_roi[3], stats_roi[0]:stats_roi[2]])),
        "sd_threshold_gray": args.sd_threshold,
        "fraction_pixels_sd_above_threshold": float(np.mean(
            sample_sd[stats_roi[1]:stats_roi[3], stats_roi[0]:stats_roi[2]] > args.sd_threshold
        )),
        "shock_psd_peak_hz": psd_peak_hz,
        "shock_psd_calculated": psd_calculated,
        "strouhal": strouhal,
        "gamma_footprint_px": gamma_footprint_px,
        "gamma_footprint_mm": gamma_footprint_mm,
        "gamma_state_B_definition": (
            f"grayscale{', inverted' if args.gamma_invert else ''} >= {args.gamma_high} to enter, "
            f"<= {args.gamma_low} to leave"
            if args.gamma_low is not None else None
        ),
        "bubble_reference_frame": args.bubble_reference_frame,
        **bubble_summary,
        "notes": [
            "Shadowgraph-derived separation and bubble values are image signatures, not direct measurements of reversed flow.",
            "Review bubble_overlays and tune ROI/thresholds before interpreting bubble-signature area or state.",
            "Shock PSD interpolates missing positions only when their fraction is within max_interpolated_fraction.",
        ],
    }
    with (args.output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, allow_nan=False)
    return summary


def _mean_dwell(states: np.ndarray, fps: float, state_value: bool) -> float | None:
    selected = states == int(state_value)
    transitions = np.diff(np.r_[False, selected, False].astype(np.int8))
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1)
    if starts.size == 0:
        return None
    return float(np.mean(ends - starts) / fps)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = analyze(args)
    except (OSError, ValueError, cv2.error) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
