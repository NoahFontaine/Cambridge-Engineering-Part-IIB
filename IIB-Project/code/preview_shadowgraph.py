#!/usr/bin/env python3
"""Create a contact sheet of selected frames to help choose analysis ROIs."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_frames(value: str) -> list[int]:
    try:
        frames = [int(item.strip()) for item in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Frame indices must be comma-separated integers") from exc
    if not frames or any(frame < 0 for frame in frames):
        raise argparse.ArgumentTypeError("Provide one or more non-negative frame indices")
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output PNG contact sheet")
    parser.add_argument("--frames", type=parse_frames, help="Comma-separated original frame indices; default: first, middle, last")
    args = parser.parse_args()

    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        parser.error(f"Could not open video: {args.video}")
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = args.frames or sorted(set((0, max(0, frame_count // 2), max(0, frame_count - 1))))
    if frame_count > 0 and any(index >= frame_count for index in indices):
        capture.release()
        parser.error(f"Frame index exceeds video frame count ({frame_count})")

    images = []
    for index in indices:
        capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = capture.read()
        if not ok:
            capture.release()
            parser.error(f"Could not decode frame {index}")
        images.append((index, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    capture.release()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, len(images), figsize=(6 * len(images), 5), squeeze=False)
    for axis, (index, image) in zip(axes[0], images):
        axis.imshow(image)
        axis.set_title(f"Frame {index}")
        axis.axis("off")
    figure.tight_layout()
    figure.savefig(args.output, dpi=160)
    plt.close(figure)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
