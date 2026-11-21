#!/usr/bin/env python3
"""Interactively select per-video flow ROIs and save them in an editable JSON manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector

VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv"}


def select_roi(title: str, frame) -> list[int] | None:
    figure, axis = plt.subplots(figsize=(12, 7))
    axis.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    axis.set_title(f"{title}\nDrag a box; press Enter to accept or Esc/close to skip")
    axis.set_axis_off()
    selection: dict[str, tuple[float, float, float, float] | None] = {"bounds": None}

    def selected(start, end) -> None:
        if all(value is not None for value in (start.xdata, start.ydata, end.xdata, end.ydata)):
            selection["bounds"] = (start.xdata, start.ydata, end.xdata, end.ydata)

    selector = RectangleSelector(
        axis, selected, useblit=False, button=[1], minspanx=2, minspany=2,
        spancoords="pixels", interactive=True,
    )

    def finish(event) -> None:
        if event.key in {"enter", "escape"}:
            plt.close(figure)

    figure.canvas.mpl_connect("key_press_event", finish)
    plt.show(block=True)
    bounds = selection["bounds"]
    if bounds is None:
        return None
    x0, x1 = sorted((int(round(bounds[0])), int(round(bounds[2]))))
    y0, y1 = sorted((int(round(bounds[1])), int(round(bounds[3]))))
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
        return None
    return [x0, y0, x1, y1]


def select_dark_region(title: str, frame, tolerance: int = 25) -> dict[str, list[list[int]]] | None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    figure, axis = plt.subplots(figsize=(12, 7))
    axis.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    axis.set_axis_off()
    overlay = axis.imshow(
        np.zeros((*gray.shape, 4), dtype=np.float32),
        interpolation="nearest",
    )
    outline, = axis.plot([], [], color="cyan", linewidth=1.5)
    selection: dict[str, list[list[int]] | None] = {"polygon": None}
    settings = {"tolerance": tolerance}
    seed = {"x": None, "y": None}

    def update(seed_x: int, seed_y: int) -> None:
        threshold = min(255, int(gray[seed_y, seed_x]) + settings["tolerance"])
        dark = (gray <= threshold).astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
        label = int(labels[seed_y, seed_x])
        if label == 0 or count <= 1:
            selection["polygon"] = None
            overlay.set_data(np.zeros((*gray.shape, 4), dtype=np.float32))
            outline.set_data([], [])
            figure.canvas.draw_idle()
            return
        component = (labels == label).astype(np.uint8)
        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            selection["polygon"] = None
            return
        contour = max(contours, key=cv2.contourArea)
        polygon = cv2.approxPolyDP(contour, 1.0, True).reshape(-1, 2)
        if len(polygon) < 3:
            selection["polygon"] = None
            return
        selection["polygon"] = [[int(x), int(y)] for x, y in polygon]
        rgba = np.zeros((*gray.shape, 4), dtype=np.float32)
        rgba[component.astype(bool)] = (1.0, 0.1, 0.1, 0.4)
        overlay.set_data(rgba)
        outline.set_data(
            np.r_[polygon[:, 0], polygon[0, 0]],
            np.r_[polygon[:, 1], polygon[0, 1]],
        )
        area = int(stats[label, cv2.CC_STAT_AREA])
        axis.set_title(
            f"{title}\nSelected {area:,} dark pixels; tolerance +{settings['tolerance']} "
            "(click to reseed, +/- adjust, Enter accept, Esc skip)"
        )
        figure.canvas.draw_idle()

    def clicked(event) -> None:
        if event.inaxes is axis and event.xdata is not None and event.ydata is not None:
            x = int(np.clip(round(event.xdata), 0, gray.shape[1] - 1))
            y = int(np.clip(round(event.ydata), 0, gray.shape[0] - 1))
            seed["x"], seed["y"] = x, y
            update(x, y)

    def key_pressed(event) -> None:
        if event.key in {"enter", "escape"}:
            plt.close(figure)
        elif event.key in {"+", "="}:
            settings["tolerance"] = min(100, settings["tolerance"] + 5)
            if seed["x"] is not None and seed["y"] is not None:
                update(seed["x"], seed["y"])
        elif event.key in {"-", "_"}:
            settings["tolerance"] = max(0, settings["tolerance"] - 5)
            if seed["x"] is not None and seed["y"] is not None:
                update(seed["x"], seed["y"])

    axis.set_title(
        f"{title}\nClick inside the dark aerofoil; +/- adjust tolerance, "
        "Enter accept, Esc/close skip"
    )
    figure.canvas.mpl_connect("button_press_event", clicked)
    figure.canvas.mpl_connect("key_press_event", key_pressed)
    plt.show(block=True)
    polygon = selection["polygon"]
    return {"polygon": polygon} if polygon else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Recursively scan for videos")
    parser.add_argument("--output", type=Path, required=True, help="ROI manifest JSON to create/update")
    args = parser.parse_args()
    if not args.input_dir.is_dir():
        parser.error(f"Input directory not found: {args.input_dir}")
    if plt.get_backend().casefold() == "agg":
        parser.error("ROI selection needs a graphical Matplotlib backend; run this on a desktop session.")
    videos = sorted(
        path for path in args.input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    if not videos:
        parser.error(f"No supported videos found under {args.input_dir}")

    manifest = {"version": 1, "coordinate_system": "native_video_pixels", "videos": {}}
    if args.output.is_file():
        with args.output.open(encoding="utf-8") as handle:
            existing = json.load(handle)
        if not isinstance(existing, dict) or not isinstance(existing.get("videos"), dict):
            parser.error(f"Invalid existing manifest: {args.output}")
        manifest = existing

    labels = (
        ("shock", "Shock position ROI (draw rectangle; Esc/empty to skip)", False),
        ("separation_bubble", "Separation bubble ROI (draw rectangle; Esc/empty to skip)", False),
        ("boundary_layer", "Boundary-layer / light streamline ROI (required)", True),
    )
    for video in videos:
        key = video.relative_to(args.input_dir).as_posix()
        capture = cv2.VideoCapture(str(video))
        if not capture.isOpened():
            parser.error(f"Could not open video: {video}")
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_count // 2))
        ok, frame = capture.read()
        capture.release()
        if not ok:
            parser.error(f"Could not read a representative frame from {video}")
        print(f"\n{key}: select ROIs in native-resolution pixels.")
        rois: dict[str, list[int] | None] = {}
        for name, title, required in labels:
            rois[name] = select_roi(f"{key} — {title}", frame)
            if rois[name] is None and required:
                parser.error(f"Boundary-layer ROI was not selected for {key}")
        rois["exclude"] = select_dark_region(
            f"{key} — Optional aerofoil exclusion: click the dark aerofoil", frame
        )
        old_record = manifest["videos"].get(key, {})
        settings = old_record if isinstance(old_record, dict) else {}
        settings.update({
            "rois": rois,
            "regime": settings.get("regime", None),
            "wall_edge": settings.get("wall_edge", "bottom"),
            "attached_fraction": settings.get("attached_fraction", 0.35),
            "detached_fraction": settings.get("detached_fraction", 0.65),
        })
        manifest["videos"][key] = settings

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(f"Wrote {args.output}; edit regime/wall_edge and thresholds there if needed.")


if __name__ == "__main__":
    main()
