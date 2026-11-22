#!/usr/bin/env python3
"""Track optional shock/bubble signatures and boundary-layer streamline motion."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from analyze_shadowgraph import track_shock
from shadowgraph_pipeline import (
    acquisition_fps,
    iter_frames,
    json_summary,
    load_manifest,
    output_path,
    ROI_NAMES,
    save_spectrum,
    scaled_settings,
    video_dimensions,
    video_files,
    video_settings,
    write_csv,
)


def _region_state(
    distance_fraction: float,
    attached_limit: float,
    detached_limit: float,
) -> str:
    if distance_fraction <= attached_limit:
        return "attached"
    if distance_fraction >= detached_limit:
        return "detached"
    return "transition"


def _overall_state(states: list[str]) -> str:
    if not states:
        return "unavailable"
    fractions = {name: states.count(name) / len(states) for name in ("attached", "detached", "transition")}
    dominant = max(fractions, key=fractions.get)
    if fractions[dominant] >= 0.8:
        return dominant
    return "intermittent"


def write_shock_motion_video(
    video: Path,
    output: Path,
    positions: list[float],
    times: list[float],
    shock_roi: tuple[int, int, int, int],
    frame_step: int,
    scale: float,
    playback_fps: float,
) -> None:
    native_width, native_height, _ = video_dimensions(video)
    width = max(1, round(native_width * scale))
    height = max(1, round(native_height * scale))
    output_fps = playback_fps / frame_step
    if not math.isfinite(output_fps) or output_fps <= 0:
        raise ValueError("Video playback frame rate must be positive")
    padded_width, padded_height = width + width % 2, height + height % 2
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        (padded_width, padded_height),
    )
    if not writer.isOpened():
        writer.release()
        raise OSError(f"Could not create shock-motion video: {output}")

    frame_count = 0
    try:
        for frame_count, (_, gray) in enumerate(
            iter_frames(video, frame_step, scale), start=1
        ):
            if frame_count > len(positions) or frame_count > len(times):
                raise ValueError("Shock-motion video frames do not match tracked samples")
            annotated = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            x0, y0, x1, y1 = shock_roi
            cv2.rectangle(annotated, (x0, y0), (x1 - 1, y1 - 1), (0, 200, 0), 1)
            position = positions[frame_count - 1]
            if math.isfinite(position):
                shock_x = int(round(position))
                cv2.line(annotated, (shock_x, 0), (shock_x, height - 1), (0, 0, 255), 2)
                location = f"Shock x: {position:.1f} px"
            else:
                location = "Shock not detected"
            label = f"t = {times[frame_count - 1] * 1000:.2f} ms | {location}"
            cv2.rectangle(annotated, (0, 0), (min(width - 1, 430), 30), (0, 0, 0), -1)
            cv2.putText(
                annotated, label, (8, 21), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1, cv2.LINE_AA,
            )
            if padded_width != width or padded_height != height:
                annotated = cv2.copyMakeBorder(
                    annotated, 0, padded_height - height, 0, padded_width - width,
                    cv2.BORDER_REPLICATE,
                )
            writer.write(annotated)
        if frame_count != len(positions) or frame_count != len(times):
            raise ValueError("Shock-motion video frames do not match tracked samples")
    finally:
        writer.release()


def analyze(
    video: Path,
    output: Path,
    record: dict[str, object],
    fps: float,
    fps_source: str,
    frame_step: int,
    scale: float,
    shock_smooth: float,
    min_gradient: float,
    bubble_threshold: int,
    min_component_area: int,
    max_interpolated_fraction: float,
) -> dict[str, object]:
    if frame_step < 1:
        raise ValueError("--frame-step must be at least 1")
    if not 0 < scale <= 1:
        raise ValueError("--scale must be in (0, 1]")
    if shock_smooth < 0 or min_gradient < 0:
        raise ValueError("Shock smoothing and minimum gradient cannot be negative")
    if not 0 <= bubble_threshold <= 255 or min_component_area < 1:
        raise ValueError("Bubble threshold must be in [0,255] and component area must be positive")
    if not 0 <= max_interpolated_fraction <= 1:
        raise ValueError("--max-interpolated-fraction must be in [0,1]")
    width0, height0, container_fps = video_dimensions(video)
    width, height = max(1, round(width0 * scale)), max(1, round(height0 * scale))
    rois = scaled_settings(record, width, height, scale)
    boundary_roi = rois["boundary_layer"]
    wall_edge = record.get("wall_edge", "bottom")
    if wall_edge not in {"top", "bottom"}:
        raise ValueError("ROI manifest wall_edge must be 'top' or 'bottom'")
    attached_limit = float(record.get("attached_fraction", 0.35))
    detached_limit = float(record.get("detached_fraction", 0.65))
    if not 0 <= attached_limit < detached_limit <= 1:
        raise ValueError("ROI manifest requires 0 <= attached_fraction < detached_fraction <= 1")
    regime = record.get("regime")
    if regime is not None:
        regime = str(regime).casefold()
        if regime not in {"subsonic", "sbli"}:
            raise ValueError("ROI manifest regime must be 'subsonic', 'sbli', or null")

    shock_roi = rois["shock"]
    bubble_roi = rois["separation_bubble"]
    if shock_roi is None and bubble_roi is None and boundary_roi is None:
        raise ValueError("No shock, bubble, or boundary-layer ROI is configured")

    # Build the temporal mean only when the optional bubble signature is requested.
    temporal_mean = None
    count = 0
    if bubble_roi is not None:
        accumulation = np.zeros((height, width), dtype=np.float64)
        for _, gray in iter_frames(video, frame_step, scale):
            accumulation += gray
            count += 1
        if count == 0:
            raise ValueError(f"No frames were decoded from {video}")
        temporal_mean = np.rint(accumulation / count).clip(0, 255).astype(np.uint8)

    output.mkdir(parents=True, exist_ok=True)
    shock_positions: list[float] = []
    shock_strengths: list[float] = []
    line_y: list[float] = []
    line_distance: list[float] = []
    line_spread: list[float] = []
    line_states: list[str] = []
    bubble_rows: list[list[object]] = []
    time_values: list[float] = []
    for frame_index, gray in iter_frames(video, frame_step, scale):
        time_s = frame_index / fps
        time_values.append(time_s)
        if shock_roi is not None:
            sx0, sy0, sx1, sy1 = shock_roi
            shock_region = gray[sy0:sy1, sx0:sx1].astype(np.float32)
            excluded = rois["exclude_mask"][sy0:sy1, sx0:sx1]
            shock_region[excluded] = np.nan
            finite_columns = np.isfinite(shock_region).any(axis=0)
            profile = np.full(shock_region.shape[1], np.nan, dtype=np.float32)
            profile[finite_columns] = np.nanmean(shock_region[:, finite_columns], axis=0)
            if finite_columns.any():
                x = np.arange(profile.size)
                profile = np.interp(x, x[finite_columns], profile[finite_columns])
                position, strength = track_shock(profile, sx0, shock_smooth, min_gradient)
            else:
                position, strength = math.nan, 0.0
            shock_positions.append(position)
            shock_strengths.append(strength)
        if boundary_roi is not None:
            bx0, by0, bx1, by1 = boundary_roi
            region = cv2.GaussianBlur(gray[by0:by1, bx0:bx1], (3, 3), 0)
            valid_pixels = ~rois["exclude_mask"][by0:by1, bx0:bx1]
            # The selected ROI isolates the bright streamline; the robust median
            # across its columns suppresses isolated reflections and missing segments.
            response = region.astype(np.float32)
            response[~valid_pixels] = -np.inf
            y_local = np.argmax(response, axis=0).astype(float)
            contrast = np.zeros(region.shape[1], dtype=np.float32)
            for column in range(region.shape[1]):
                values = region[:, column][valid_pixels[:, column]]
                if values.size:
                    contrast[column] = float(np.ptp(values))
            usable = (contrast >= 2.0) & valid_pixels.any(axis=0)
            if not np.any(usable):
                position_y = math.nan
            else:
                position_y = float(np.median(y_local[usable]) + by0)
            line_y.append(position_y)
            if math.isfinite(position_y):
                distance = (
                    position_y - by0 if wall_edge == "top"
                    else (by1 - 1) - position_y
                )
                fraction = float(np.clip(distance / max(1, by1 - by0 - 1), 0, 1))
                state = _region_state(fraction, attached_limit, detached_limit)
                column_y = y_local[usable] + by0
                spread = float(np.quantile(column_y, 0.9) - np.quantile(column_y, 0.1))
            else:
                fraction, state, spread = math.nan, "unavailable", math.nan
            line_distance.append(fraction)
            line_states.append(state)
            line_spread.append(spread)
        if bubble_roi is not None and temporal_mean is not None:
            x0, y0, x1, y1 = bubble_roi
            difference = cv2.absdiff(gray[y0:y1, x0:x1], temporal_mean[y0:y1, x0:x1])
            excluded = rois["exclude_mask"][y0:y1, x0:x1]
            difference[excluded] = 0
            _, binary = cv2.threshold(difference, bubble_threshold, 255, cv2.THRESH_BINARY)
            binary = cv2.morphologyEx(
                binary, cv2.MORPH_CLOSE, np.ones((3, 3), dtype=np.uint8)
            )
            component_count, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
            areas = stats[1:component_count, cv2.CC_STAT_AREA]
            eligible = areas[areas >= min_component_area]
            area = int(np.max(eligible)) if eligible.size else 0
            bubble_rows.append([time_s, frame_index, area, int(area > 0)])

    if not time_values:
        raise ValueError(f"No frames were decoded from {video}")
    effective_fps = fps / frame_step
    shock_peak = None
    shock_motion_video = None
    if shock_roi is not None:
        shock_motion_video = output / "shock_motion.mp4"
        write_shock_motion_video(
            video, shock_motion_video, shock_positions, time_values, shock_roi,
            frame_step, scale, container_fps,
        )
        shock_array = np.asarray(shock_positions, dtype=float)
        shock_valid = np.isfinite(shock_array)
        write_csv(
            output / "shock_position.csv",
            ["time_s", "frame_index", "shock_x_px", "shock_gradient"],
            [
                [time, int(round(time * fps)), position, strength]
                for time, position, strength in zip(time_values, shock_positions, shock_strengths)
            ],
        )
        if shock_valid.any() and shock_valid.sum() >= 16 and (1 - shock_valid.mean()) <= max_interpolated_fraction:
            shock_peak = save_spectrum(
                np.interp(np.arange(shock_array.size), np.flatnonzero(shock_valid), shock_array[shock_valid]),
                effective_fps, output, "shock_position", "Shock position",
            )
        shock_missing = float(1 - np.mean(shock_valid))
        shock_mean = float(np.mean(shock_array[shock_valid])) if shock_valid.any() else None
    else:
        shock_missing, shock_mean = None, None

    motion_peak = None
    mean_line_y = None
    line_state = "unavailable"
    if boundary_roi is not None:
        y_values = np.asarray(line_y, dtype=float)
        finite = np.isfinite(y_values)
        line_states_valid = [state for state in line_states if state != "unavailable"]
        line_state = _overall_state(line_states_valid)
        mean_line_y = float(np.mean(y_values[finite])) if finite.any() else None
        # A continuous distance-to-wall signal reveals motion frequency even if
        # the thresholded state alternates between attached and detached.
        motion = np.asarray(line_distance, dtype=float)
        valid = np.isfinite(motion)
        if valid.sum() >= 16:
            motion_peak = save_spectrum(
                np.interp(np.arange(motion.size), np.flatnonzero(valid), motion[valid]),
                effective_fps, output, "streamline_distance", "Boundary-layer streamline distance",
            )
        write_csv(
            output / "boundary_layer_motion.csv",
            ["time_s", "frame_index", "streamline_y_px", "distance_from_wall_fraction", "line_spread_px", "state"],
            [
                [time, int(round(time * fps)), y, distance, spread, state]
                for time, y, distance, spread, state in zip(
                    time_values, line_y, line_distance, line_spread, line_states
                )
            ],
        )
        figure, axis = plt.subplots(figsize=(10, 4))
        axis.plot(time_values, line_distance, linewidth=0.8)
        axis.set(title="Tracked light streamline motion", xlabel="Time (s)", ylabel="Distance from wall / ROI height")
        axis.set_ylim(-0.02, 1.02)
        axis.grid(True, alpha=0.25)
        figure.tight_layout()
        figure.savefig(output / "boundary_layer_motion.png", dpi=160)
        plt.close(figure)
    bubble_fraction = None
    bubble_status = "unavailable"
    if bubble_roi is not None:
        write_csv(
            output / "bubble_signature.csv",
            ["time_s", "frame_index", "largest_component_area_px2", "signature_present"],
            bubble_rows,
        )
        bubble_fraction = float(np.mean([row[3] for row in bubble_rows]))
        bubble_status = "present" if bubble_fraction > 0 else "absent"
    flow_state = f"{regime}_{line_state}" if regime else line_state
    summary: dict[str, object] = {
        "video": str(video.resolve()),
        "camera_acquisition_fps": fps,
        "fps_source": fps_source,
        "container_playback_fps": container_fps,
        "analysis_fps": effective_fps,
        "frame_step": frame_step,
        "frames_analyzed": len(time_values),
        "duration_s": time_values[-1] - time_values[0] if len(time_values) > 1 else 0.0,
        "regime": regime,
        "flow_state": flow_state,
        "attachment_state": line_state,
        "shock_status": (
            "not_requested" if shock_roi is None
            else "present" if shock_missing is not None and shock_missing < 1
            else "not_detected"
        ),
        "shock_motion_video": (
            str(shock_motion_video.resolve()) if shock_motion_video is not None else None
        ),
        "shock_missing_fraction": shock_missing,
        "shock_mean_x_px": shock_mean,
        "shock_position_peak_hz": shock_peak,
        "shock_psd_calculated": shock_peak is not None,
        "shock_psd_max_interpolated_fraction": max_interpolated_fraction,
        "bubble_status": bubble_status,
        "bubble_signature_presence_fraction": bubble_fraction,
        "mean_streamline_y_px": mean_line_y,
        "streamline_distance_peak_hz": motion_peak,
        "streamline_distance_peak_hz_source": "continuous distance-to-wall signal",
        "wall_edge": wall_edge,
        "attached_fraction_threshold": attached_limit,
        "detached_fraction_threshold": detached_limit,
        "analysis_rois_px": {
            name: list(rois[name]) if rois[name] is not None else None
            for name in ROI_NAMES
        },
        "notes": [
            "Shock and bubble regions are optional; their absence does not prevent boundary-layer tracking.",
            "A detached/attached label is an image-based streamline-distance proxy, not a direct flow-reversal measurement.",
            "Set regime to subsonic or sbli in the ROI manifest; it is not inferred from shadowgraph images.",
        ],
    }
    json_summary(output / "tracking_summary.json", summary)
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
    parser.add_argument("--frame-step", type=int, default=1)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--shock-smooth", type=float, default=1.5)
    parser.add_argument("--min-gradient", type=float, default=2.0)
    parser.add_argument("--bubble-diff-threshold", type=int, default=12)
    parser.add_argument("--min-component-area", type=int, default=8)
    parser.add_argument("--max-interpolated-fraction", type=float, default=0.05)
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
                record, fps, source_label, args.frame_step, args.scale,
                args.shock_smooth, args.min_gradient, args.bubble_diff_threshold,
                args.min_component_area, args.max_interpolated_fraction,
            )
            result["video_key"] = video.relative_to(args.input_dir).as_posix() if args.input_dir else video.name
            results.append(result)
            print(f"Tracked {video}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        columns = sorted({key for result in results for key, value in result.items() if not isinstance(value, (dict, list))})
        with (args.output_dir / "tracking_batch_summary.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"Wrote {args.output_dir / 'tracking_batch_summary.csv'}")
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
