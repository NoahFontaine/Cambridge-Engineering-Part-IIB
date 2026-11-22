#!/usr/bin/env python3
"""Compute ROI-masked pixel-statistics maps and time-resolved unsteadiness indices."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

from shadowgraph_pipeline import (
    acquisition_fps,
    iter_frames,
    json_summary,
    load_manifest,
    output_path,
    ROI_NAMES,
    roi_mask,
    save_map,
    save_spectrum,
    scaled_settings,
    video_dimensions,
    video_files,
    video_settings,
    write_csv,
)


def analyze(
    video: Path,
    output: Path,
    record: dict[str, object],
    fps: float,
    fps_source: str,
    frame_step: int,
    scale: float,
    sd_threshold: float,
) -> dict[str, object]:
    if frame_step < 1:
        raise ValueError("--frame-step must be at least 1")
    if not 0 < scale <= 1:
        raise ValueError("--scale must be in (0, 1]")
    if not math.isfinite(sd_threshold) or sd_threshold < 0:
        raise ValueError("--sd-threshold must be finite and non-negative")
    native_width, native_height, container_fps = video_dimensions(video)
    width = max(1, int(round(native_width * scale)))
    height = max(1, int(round(native_height * scale)))
    rois = scaled_settings(record, width, height, scale)
    mask = roi_mask(rois, (height, width), full_frame=True)
    count = 0
    sums = [np.zeros((height, width), dtype=np.float64) for _ in range(4)]
    for _, gray in iter_frames(video, frame_step, scale):
        image = gray.astype(np.float64)
        square = image * image
        sums[0] += image
        sums[1] += square
        sums[2] += square * image
        sums[3] += square * square
        count += 1
    if count == 0:
        raise ValueError(f"No frames were decoded from {video}")

    mean = sums[0] / count
    variance = np.maximum(sums[1] / count - mean**2, 0)
    sd = np.sqrt(variance * count / (count - 1)) if count > 1 else np.zeros_like(mean)
    central3 = sums[2] / count - 3 * mean * (sums[1] / count) + 2 * mean**3
    central4 = (
        sums[3] / count - 4 * mean * (sums[2] / count)
        + 6 * mean**2 * (sums[1] / count) - 3 * mean**4
    )
    skewness = np.divide(
        central3, variance**1.5, out=np.zeros_like(mean), where=variance > 1e-12
    )
    kurtosis = np.divide(
        central4, variance**2, out=np.zeros_like(mean), where=variance > 1e-12
    )
    output.mkdir(parents=True, exist_ok=True)
    maps = {
        "mean": mean,
        "sd": sd,
        "skewness": skewness,
        "kurtosis": kurtosis,
    }
    masked_maps = {name: np.where(mask, values, np.nan) for name, values in maps.items()}
    np.savez_compressed(
        output / "pixel_statistics.npz",
        **{name: values.astype(np.float32) for name, values in masked_maps.items()},
        analysis_mask=mask,
    )
    titles = {
        "mean": ("Mean shadowgraph intensity", "grayscale level"),
        "sd": ("Pixel-wise intensity SD", "grayscale level"),
        "skewness": ("Pixel-wise intensity skewness", "skewness"),
        "kurtosis": ("Pixel-wise intensity kurtosis", "kurtosis (Gaussian = 3)"),
    }
    for name, (title, label) in titles.items():
        save_map(output / f"{name}.png", masked_maps[name], title, label)

    # The first pass establishes the temporal mean; this pass forms an ROI-only
    # instantaneous signal suitable for scalar unsteadiness and frequency work.
    selected_mean = mean[mask]
    signal_rows: list[list[object]] = []
    scalar_rms: list[float] = []
    scalar_mean_abs: list[float] = []
    fraction_above: list[float] = []
    for frame_index, gray in iter_frames(video, frame_step, scale):
        deviation = gray.astype(np.float64)[mask] - selected_mean
        rms = float(np.sqrt(np.mean(deviation**2)))
        mean_abs = float(np.mean(np.abs(deviation)))
        fraction = float(np.mean(np.abs(deviation) > sd_threshold))
        time_s = frame_index / fps
        signal_rows.append([time_s, frame_index, mean_abs, rms, fraction])
        scalar_rms.append(rms)
        scalar_mean_abs.append(mean_abs)
        fraction_above.append(fraction)
    effective_fps = fps / frame_step
    rms_peak = save_spectrum(
        np.asarray(scalar_rms), effective_fps, output, "unsteadiness_rms",
        "ROI RMS intensity deviation",
    )
    abs_peak = save_spectrum(
        np.asarray(scalar_mean_abs), effective_fps, output, "unsteadiness_mean_abs",
        "ROI mean absolute intensity deviation",
    )
    write_csv(
        output / "unsteadiness.csv",
        [
            "time_s", "frame_index", "roi_mean_absolute_deviation",
            "roi_rms_deviation", "fraction_pixels_above_deviation_threshold",
        ],
        signal_rows,
    )
    valid_sd = sd[mask]
    summary: dict[str, object] = {
        "video": str(video.resolve()),
        "camera_acquisition_fps": fps,
        "fps_source": fps_source,
        "container_playback_fps": container_fps,
        "analysis_fps": effective_fps,
        "frame_step": frame_step,
        "frames_analyzed": count,
        "duration_s": (count - 1) / effective_fps if count > 1 else 0.0,
        "analysis_pixels": int(mask.sum()),
        "analysis_roi_pixels_sd_mean": float(np.mean(valid_sd)),
        "sd_threshold_gray": sd_threshold,
        "fraction_analysis_pixels_sd_above_threshold": float(np.mean(valid_sd > sd_threshold)),
        "mean_instantaneous_roi_rms_deviation": float(np.mean(scalar_rms)),
        "mean_instantaneous_roi_absolute_deviation": float(np.mean(scalar_mean_abs)),
        "mean_instantaneous_fraction_above_deviation_threshold": float(np.mean(fraction_above)),
        "roi_rms_deviation_peak_hz": rms_peak,
        "roi_mean_absolute_deviation_peak_hz": abs_peak,
        "masked_pixels_excluded": int(mask.size - mask.sum()),
        "analysis_rois_px": {
            name: list(rois[name]) if rois[name] is not None else None
            for name in ROI_NAMES
        },
    }
    json_summary(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path)
    source.add_argument("--input-dir", type=Path)
    parser.add_argument("--roi-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fps", type=float, help="Camera acquisition rate for a single video")
    parser.add_argument("--workbook", type=Path, help="Run matrix with camera acquisition rates")
    parser.add_argument("--frame-step", type=int, default=1)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--sd-threshold", type=float, default=15.0)
    args = parser.parse_args()
    if args.input_dir is not None and args.fps is not None and args.workbook is None:
        parser.error("Batch processing needs --workbook so acquisition rates are read per run")
    try:
        manifest = load_manifest(args.roi_config)
        videos = video_files(args.video, args.input_dir)
        results = []
        for video in videos:
            record = video_settings(manifest, video, args.input_dir)
            run_number = record.get("run_number")
            run_number = int(run_number) if run_number is not None else None
            fps, source_label = acquisition_fps(video, args.fps, args.workbook, run_number)
            result = analyze(
                video, output_path(video, args.input_dir, args.output_dir),
                record, fps, source_label, args.frame_step, args.scale, args.sd_threshold,
            )
            result["video_key"] = video.relative_to(args.input_dir).as_posix() if args.input_dir else video.name
            results.append(result)
            print(f"Analyzed {video}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        columns = sorted({key for result in results for key, value in result.items() if not isinstance(value, dict)})
        with (args.output_dir / "statistics_batch_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"Wrote {args.output_dir / 'statistics_batch_summary.csv'}")
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
