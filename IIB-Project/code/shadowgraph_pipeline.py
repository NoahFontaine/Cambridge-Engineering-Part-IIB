"""Shared input, ROI-manifest, and plotting helpers for the split analyses."""

from __future__ import annotations

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
from scipy import signal

from analyze_shadowgraph import gray_frame, scaled_roi
from run_metadata import infer_run_number, load_run_frame_rates

VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv"}
ROI_NAMES = ("shock", "separation_bubble", "boundary_layer", "exclude")


def video_files(video: Path | None, input_dir: Path | None) -> list[Path]:
    if (video is None) == (input_dir is None):
        raise ValueError("Provide exactly one of --video or --input-dir")
    if video is not None:
        if not video.is_file():
            raise FileNotFoundError(f"Video not found: {video}")
        return [video]
    assert input_dir is not None
    files = sorted(
        path for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    if not files:
        raise ValueError(f"No supported videos found under {input_dir}")
    return files


def video_key(path: Path, input_dir: Path | None) -> str:
    if input_dir is not None:
        return path.relative_to(input_dir).as_posix()
    return path.name


def load_manifest(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("videos"), dict):
        raise ValueError(f"ROI manifest must contain a 'videos' object: {path}")
    return data["videos"]


def video_settings(
    manifest: dict[str, object], path: Path, input_dir: Path | None
) -> dict[str, object]:
    key = video_key(path, input_dir)
    record = manifest.get(key)
    if record is None and input_dir is None:
        resolved = path.resolve()
        matching_keys = [
            manifest_key for manifest_key in manifest
            if resolved.as_posix().endswith("/" + Path(manifest_key).as_posix())
            or Path(manifest_key).name == path.name
        ]
        if len(matching_keys) == 1:
            record = manifest[matching_keys[0]]
        elif len(matching_keys) > 1:
            raise ValueError(
                f"Multiple ROI entries match {path}; run from the video root with --input-dir"
            )
        else:
            record = manifest.get(str(resolved))
    if not isinstance(record, dict):
        raise ValueError(f"No ROI settings for {key}; run select_rois.py first")
    rois = record.get("rois")
    if not isinstance(rois, dict):
        raise ValueError(f"ROI settings for {key} must contain a 'rois' object")
    for name in ROI_NAMES[:-1]:
        value = rois.get(name)
        if value is not None and (
            not isinstance(value, list) or len(value) != 4
            or any(not isinstance(item, int) for item in value)
        ):
            raise ValueError(f"Invalid {name} ROI for {key}: {value!r}")
        if value is not None and (
            value[0] < 0 or value[1] < 0 or value[2] <= value[0] or value[3] <= value[1]
        ):
            raise ValueError(f"Invalid {name} ROI bounds for {key}: {value!r}")
    excluded = rois.get("exclude")
    if excluded is not None:
        if isinstance(excluded, list):
            if (
                len(excluded) != 4
                or any(not isinstance(item, int) for item in excluded)
                or excluded[0] < 0 or excluded[1] < 0
                or excluded[2] <= excluded[0] or excluded[3] <= excluded[1]
            ):
                raise ValueError(f"Invalid exclude ROI bounds for {key}: {excluded!r}")
        elif isinstance(excluded, dict):
            polygon = excluded.get("polygon")
            if (
                not isinstance(polygon, list) or len(polygon) < 3
                or any(
                    not isinstance(point, list) or len(point) != 2
                    or any(not isinstance(value, int) or value < 0 for value in point)
                    for point in polygon
                )
            ):
                raise ValueError(f"Invalid exclude polygon for {key}: {polygon!r}")
        else:
            raise ValueError(f"Invalid exclude ROI for {key}: {excluded!r}")
    return record


def acquisition_fps(
    path: Path,
    fps: float | None,
    workbook: Path | None,
    run_number: int | None = None,
) -> tuple[float, str]:
    if workbook is not None:
        number = run_number if run_number is not None else infer_run_number(path)
        rates = load_run_frame_rates(workbook)
        if number not in rates:
            raise ValueError(f"Run {number} has no frame rate in {workbook}")
        matrix_rate = rates[number]
        if fps is not None and not math.isclose(fps, matrix_rate):
            raise ValueError(f"--fps {fps} conflicts with run {number} rate {matrix_rate}")
        return matrix_rate, f"run_matrix:{workbook.resolve()}#run={number}"
    if fps is None or not math.isfinite(fps) or fps <= 0:
        raise ValueError("Camera acquisition rate is required: provide --fps or --workbook")
    return fps, "command_line"


def scaled_settings(
    record: dict[str, object], width: int, height: int, scale: float
) -> dict[str, object]:
    roi_values = record["rois"]
    assert isinstance(roi_values, dict)
    result: dict[str, object] = {
        name: (
            scaled_roi(roi_values.get(name), width, height, scale)
            if roi_values.get(name) is not None else None
        )
        for name in ROI_NAMES[:-1]
    }
    excluded = roi_values.get("exclude")
    exclusion_mask = np.zeros((height, width), dtype=np.uint8)
    if isinstance(excluded, dict):
        polygon = np.asarray(excluded["polygon"], dtype=np.float32)
        polygon = np.rint(polygon * scale).astype(np.int32)
        if (
            np.any(polygon[:, 0] >= width) or np.any(polygon[:, 1] >= height)
        ):
            raise ValueError("Exclusion polygon exceeds analyzed frame dimensions")
        cv2.fillPoly(exclusion_mask, [polygon], 1)
        x0, y0 = np.min(polygon, axis=0)
        x1, y1 = np.max(polygon, axis=0) + 1
        result["exclude"] = (int(x0), int(y0), int(x1), int(y1))
    elif excluded is not None:
        exclude_roi = scaled_roi(excluded, width, height, scale)
        x0, y0, x1, y1 = exclude_roi
        exclusion_mask[y0:y1, x0:x1] = 1
        result["exclude"] = exclude_roi
    else:
        result["exclude"] = None
    result["exclude_mask"] = exclusion_mask.astype(bool)
    return result


def roi_mask(
    rois: dict[str, object],
    shape: tuple[int, int],
    include: tuple[str, ...] = ("shock", "separation_bubble", "boundary_layer"),
) -> np.ndarray:
    height, width = shape
    mask = np.zeros((height, width), dtype=bool)
    for name in include:
        roi = rois[name]
        if roi is not None:
            assert isinstance(roi, tuple)
            x0, y0, x1, y1 = roi
            mask[y0:y1, x0:x1] = True
    excluded_mask = rois.get("exclude_mask")
    if excluded_mask is not None:
        assert isinstance(excluded_mask, np.ndarray)
        mask[excluded_mask] = False
    else:
        excluded = rois["exclude"]
        if excluded is not None:
            assert isinstance(excluded, tuple)
            x0, y0, x1, y1 = excluded
            mask[y0:y1, x0:x1] = False
    if not mask.any():
        raise ValueError("No analysis ROI is configured; select at least one flow ROI")
    return mask


def iter_frames(path: Path, frame_step: int, scale: float) -> Iterator[tuple[int, np.ndarray]]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise OSError(f"Could not open video: {path}")
    index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if index % frame_step == 0:
                yield index, gray_frame(frame, scale)
            index += 1
    finally:
        capture.release()


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def save_map(path: Path, values: np.ndarray, title: str, label: str) -> None:
    fig, axis = plt.subplots(figsize=(10, 5))
    image = axis.imshow(np.ma.masked_invalid(values), cmap="inferno", origin="upper", aspect="auto")
    axis.set(title=title, xlabel="x (analysis pixels)", ylabel="y (analysis pixels)")
    fig.colorbar(image, ax=axis, label=label)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def save_spectrum(
    values: np.ndarray, fps: float, output_dir: Path, stem: str, label: str
) -> float | None:
    if values.size < 16 or not np.isfinite(values).all():
        return None
    centered = values.astype(float) - float(np.mean(values))
    if np.allclose(centered, 0):
        return None
    nperseg = min(8192, max(16, values.size // 4), values.size)
    frequencies, power = signal.welch(
        centered, fs=fps, window="hann", nperseg=nperseg,
        noverlap=nperseg // 2, detrend="constant", scaling="density",
    )
    write_csv(
        output_dir / f"{stem}_psd.csv",
        ["frequency_hz", f"psd_{stem}2_per_hz"],
        [[float(f), float(p)] for f, p in zip(frequencies, power)],
    )
    positive = frequencies > 0
    peak = float(frequencies[positive][int(np.argmax(power[positive]))]) if positive.any() else None
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.loglog(frequencies[positive], power[positive])
    axis.set(title=f"{label} Welch PSD", xlabel="Frequency (Hz)", ylabel="PSD")
    axis.grid(True, which="both", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / f"{stem}_psd.png", dpi=160)
    plt.close(figure)
    return peak


def output_path(path: Path, input_dir: Path | None, output_dir: Path) -> Path:
    relative = path.relative_to(input_dir) if input_dir is not None else Path(path.stem)
    return output_dir / relative.with_suffix("")


def json_summary(path: Path, summary: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, allow_nan=False)


def video_dimensions(path: Path) -> tuple[int, int, float]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise OSError(f"Could not open video: {path}")
    dimensions = (
        int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        float(capture.get(cv2.CAP_PROP_FPS)),
    )
    capture.release()
    return dimensions
