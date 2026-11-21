#!/usr/bin/env python3
"""Compute exact Dynamic Mode Decomposition (DMD) for ROI-selected runs."""

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
    delta_t = float(np.median(np.diff(indices)) / fps)
    x1, x2 = snapshots[:, :-1], snapshots[:, 1:]
    u, singular_values, vh = svd(x1, full_matrices=False, check_finite=False)
    rank = min(rank, int(np.count_nonzero(singular_values > np.finfo(float).eps * singular_values[0])))
    if rank < 1:
        raise ValueError("Snapshot sequence has zero numerical rank")
    ur = u[:, :rank]
    sr = singular_values[:rank]
    vr = vh[:rank, :].conj().T
    reduced = ur.conj().T @ x2 @ vr @ np.diag(1.0 / sr)
    eigenvalues, eigenvectors = np.linalg.eig(reduced)
    modes = x2 @ vr @ np.diag(1.0 / sr) @ eigenvectors
    continuous = np.full(eigenvalues.shape, np.nan + 1j * np.nan, dtype=np.complex128)
    nonzero_eigenvalues = np.abs(eigenvalues) > np.finfo(float).tiny
    continuous[nonzero_eigenvalues] = (
        np.log(eigenvalues[nonzero_eigenvalues].astype(np.complex128)) / delta_t
    )
    frequencies = np.imag(continuous) / (2 * np.pi)
    growth_rates = np.real(continuous)
    amplitudes = np.linalg.lstsq(modes, snapshots[:, 0], rcond=None)[0]
    oscillatory = np.flatnonzero(np.abs(frequencies) > 1e-12)
    dominant_frequency = (
        float(frequencies[oscillatory[np.argmax(np.abs(frequencies[oscillatory]))]])
        if oscillatory.size else None
    )
    output.mkdir(parents=True, exist_ok=True)
    save_modes(output, modes, mask, shape, "dmd", rank)
    with (output / "dmd_eigenvalues.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "mode", "eigenvalue_real", "eigenvalue_imag", "frequency_hz",
            "growth_rate_per_s", "initial_amplitude",
        ])
        for index, value in enumerate(eigenvalues):
            writer.writerow([
                index + 1, float(value.real), float(value.imag),
                float(frequencies[index]) if np.isfinite(frequencies[index]) else None,
                float(growth_rates[index]) if np.isfinite(growth_rates[index]) else None,
                float(abs(amplitudes[index])),
            ])
    summary: dict[str, object] = {
        "video": str(video.resolve()),
        "camera_acquisition_fps": fps,
        "fps_source": fps_source,
        "frames_in_decomposition": int(indices.size),
        "snapshot_stride_frames": stride,
        "sample_interval_s": delta_t,
        "analysis_pixels": int(mask.sum()),
        "requested_rank": requested_rank,
        "computed_rank": rank,
        "dominant_nonzero_frequency_hz": dominant_frequency,
        "analysis_method": "exact DMD on consecutive mean-unsubtracted ROI snapshots",
    }
    json_summary(output / "dmd_summary.json", summary)
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
            print(f"Computed DMD for {video}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        columns = sorted({key for result in results for key in result})
        with (args.output_dir / "dmd_batch_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"Wrote {args.output_dir / 'dmd_batch_summary.csv'}")
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
