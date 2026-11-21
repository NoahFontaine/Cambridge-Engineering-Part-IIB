"""Snapshot loading and mode-output helpers for POD and DMD."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from shadowgraph_pipeline import iter_frames, roi_mask, scaled_settings, video_dimensions


def load_snapshots(
    video: Path,
    record: dict[str, object],
    scale: float,
    frame_step: int,
    max_snapshots: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[int, int], int]:
    if not 0 < scale <= 1 or frame_step < 1 or max_snapshots < 3:
        raise ValueError("Scale must be in (0,1], frame step positive, and max snapshots >= 3")
    native_width, native_height, _ = video_dimensions(video)
    width = max(1, round(native_width * scale))
    height = max(1, round(native_height * scale))
    rois = scaled_settings(record, width, height, scale)
    mask = roi_mask(rois, (height, width))
    capture_frame_count = 0
    import cv2

    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise OSError(f"Could not open video: {video}")
    capture_frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    if capture_frame_count <= 0:
        raise ValueError(f"Video has no readable frame-count metadata: {video}")
    stride = frame_step * max(
        1, math.ceil(capture_frame_count / (frame_step * max_snapshots))
    )
    snapshots = []
    frame_indices = []
    for frame_index, gray in iter_frames(video, stride, scale):
        snapshots.append(gray[mask].astype(np.float32))
        frame_indices.append(frame_index)
    if len(snapshots) < 3:
        raise ValueError(f"At least three snapshots are required for decomposition: {video}")
    return (
        np.column_stack(snapshots),
        np.asarray(frame_indices, dtype=np.int64),
        mask,
        (height, width),
        stride,
    )


def save_modes(
    output: Path,
    modes: np.ndarray,
    mask: np.ndarray,
    shape: tuple[int, int],
    prefix: str,
    count: int,
) -> None:
    count = min(count, modes.shape[1])
    stored = modes[:, :count]
    np.savez_compressed(output / f"{prefix}_modes.npz", modes=stored, analysis_mask=mask)
    height, width = shape
    for index in range(count):
        field = np.full((height, width), np.nan, dtype=np.float32)
        field[mask] = np.real(stored[:, index])
        limit = float(np.nanmax(np.abs(field)))
        figure, axis = plt.subplots(figsize=(10, 5))
        image = axis.imshow(
            np.ma.masked_invalid(field), cmap="RdBu_r", origin="upper",
            aspect="auto", vmin=-limit if limit else -1, vmax=limit if limit else 1,
        )
        axis.set(title=f"{prefix.upper()} spatial mode {index + 1}", xlabel="x (analysis pixels)", ylabel="y (analysis pixels)")
        figure.colorbar(image, ax=axis, label="mode amplitude")
        figure.tight_layout()
        figure.savefig(output / f"{prefix}_mode_{index + 1:02d}.png", dpi=160)
        plt.close(figure)
