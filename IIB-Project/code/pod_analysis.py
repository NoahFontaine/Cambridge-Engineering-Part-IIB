#!/usr/bin/env python3
"""Compute Proper Orthogonal Decomposition (POD) modes for ROI-selected runs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.linalg import svd

from modal_common import load_snapshots, save_modes
from shadowgraph_pipeline import (
    acquisition_fps,
    json_summary,
    load_manifest,
    output_path,
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
    scale: float,
    frame_step: int,
    max_snapshots: int,
    rank: int,
) -> dict[str, object]:
    requested_rank = rank
    snapshots, indices, mask, shape, stride = load_snapshots(
        video, record, scale, frame_step, max_snapshots
    )
    if rank < 1:
        raise ValueError("--rank must be positive")
    centered = snapshots - snapshots.mean(axis=1, keepdims=True)
    u, singular_values, _ = svd(centered, full_matrices=False, check_finite=False)
    rank = min(rank, u.shape[1])
    modes = u[:, :rank]
    energy = singular_values**2
    total_energy = float(np.sum(energy))
    fractions = energy / total_energy if total_energy > 0 else np.zeros_like(energy)
    cumulative = np.cumsum(fractions)
    output.mkdir(parents=True, exist_ok=True)
    save_modes(output, modes, mask, shape, "pod", rank)
    write_csv(
        output / "pod_energy.csv",
        ["mode", "singular_value", "energy_fraction", "cumulative_energy_fraction"],
        [
            [i + 1, float(singular_values[i]), float(fractions[i]), float(cumulative[i])]
            for i in range(rank)
        ],
    )
    coefficients = modes.T @ centered
    with (output / "pod_coefficients.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["frame_index", "time_s", *[f"mode_{i + 1}" for i in range(rank)]])
        for column, frame in enumerate(indices):
            writer.writerow([int(frame), frame / fps, *coefficients[:, column].tolist()])
    summary: dict[str, object] = {
        "video": str(video.resolve()),
        "camera_acquisition_fps": fps,
        "fps_source": fps_source,
        "frames_in_decomposition": int(indices.size),
        "snapshot_stride_frames": stride,
        "analysis_pixels": int(mask.sum()),
        "requested_rank": requested_rank,
        "computed_rank": rank,
        "leading_mode_energy_fraction": float(fractions[0]),
        "cumulative_energy_fraction": float(cumulative[-1]),
        "analysis_method": "SVD of mean-subtracted ROI snapshots",
    }
    json_summary(output / "pod_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path)
    source.add_argument("--input-dir", type=Path)
    parser.add_argument("--roi-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--frame-step", type=int, default=1)
    parser.add_argument("--max-snapshots", type=int, default=300)
    parser.add_argument("--rank", type=int, default=20)
    args = parser.parse_args()
    if args.input_dir is not None and args.fps is not None and args.workbook is None:
        parser.error("Batch processing needs --workbook so acquisition rates are read per run")
    try:
        manifest = load_manifest(args.roi_config)
        results = []
        for video in video_files(args.video, args.input_dir):
            record = video_settings(manifest, video, args.input_dir)
            run_number = record.get("run_number")
            fps, source_label = acquisition_fps(
                video, args.fps, args.workbook,
                int(run_number) if run_number is not None else None,
            )
            result = analyze(
                video, output_path(video, args.input_dir, args.output_dir),
                record, fps, source_label, args.scale, args.frame_step,
                args.max_snapshots, args.rank,
            )
            result["video_key"] = video.relative_to(args.input_dir).as_posix() if args.input_dir else video.name
            results.append(result)
            print(f"Computed POD for {video}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        columns = sorted({key for result in results for key in result})
        with (args.output_dir / "pod_batch_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"Wrote {args.output_dir / 'pod_batch_summary.csv'}")
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
