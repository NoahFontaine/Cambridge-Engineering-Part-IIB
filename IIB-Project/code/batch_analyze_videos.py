#!/usr/bin/env python3
"""Run analyze_shadowgraph.py on each video under a directory and collate summaries."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

from run_metadata import infer_run_number, load_run_frame_rates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory recursively searched for videos")
    parser.add_argument("--output-dir", type=Path, required=True, help="Root output directory")
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "michaelmas_runs.xlsx",
        help="Excel run matrix containing each run's original camera frame rate",
    )
    parser.add_argument(
        "analysis_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to analyze_shadowgraph.py (put them after --)",
    )
    args = parser.parse_args()
    analysis_args = args.analysis_args[1:] if args.analysis_args[:1] == ["--"] else args.analysis_args
    videos = sorted(
        path for path in args.input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"}
    )
    if not videos:
        parser.error(f"No supported videos found under {args.input_dir}")
    if any(argument == "--fps" or argument.startswith("--fps=") for argument in analysis_args):
        parser.error("Batch fps is read per run from --workbook; do not forward --fps")
    try:
        frame_rates = load_run_frame_rates(args.workbook)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    analyzer = Path(__file__).with_name("analyze_shadowgraph.py")
    summaries: list[dict[str, object]] = []
    for video in videos:
        try:
            run_number = infer_run_number(video.relative_to(args.input_dir))
        except ValueError as exc:
            parser.error(str(exc))
        if run_number not in frame_rates:
            parser.error(f"Run {run_number} has no frame rate in {args.workbook}")
        output = args.output_dir / video.relative_to(args.input_dir).with_suffix("")
        command = [
            sys.executable,
            str(analyzer),
            "--video",
            str(video),
            "--output-dir",
            str(output),
            "--run-matrix",
            str(args.workbook.resolve()),
            "--run-number",
            str(run_number),
            *analysis_args,
        ]
        print(f"Analyzing {video}", flush=True)
        subprocess.run(command, check=True)
        with (output / "summary.json").open(encoding="utf-8") as handle:
            summaries.append(json.load(handle))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "batch_summary.csv"
    columns = [
        "video",
        "run_number",
        "camera_acquisition_fps",
        "container_playback_fps",
        "fps_source",
        "analysis_fps",
        "frames_analyzed",
        "duration_s",
        "shock_mean_x_mm",
        "shock_sd_x_px",
        "shock_sd_x_mm",
        "mean_pixel_sd",
        "fraction_pixels_sd_above_threshold",
        "shock_missing_fraction",
        "shock_psd_peak_hz",
        "strouhal",
        "gamma_footprint_px",
        "gamma_footprint_mm",
        "bubble_signature_presence_fraction",
        "mean_bubble_signature_area_mm2",
        "mean_bubble_signature_extent_mm",
        "bubble_cycle_period_cv",
        "bubble_cycle_frequency_hz",
    ]
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
