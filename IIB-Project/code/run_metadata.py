"""Read per-run acquisition metadata from the Michaelmas Excel run log."""

from __future__ import annotations

import math
import re
import warnings
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


def infer_run_number(path: Path) -> int:
    for part in reversed(path.parts):
        match = re.fullmatch(r"run[\s_-]*0*(\d+)", Path(part).stem, re.IGNORECASE)
        if match:
            return int(match.group(1))
    raise ValueError(f"Cannot infer run number from path: {path}")


def _column_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _positive_number(value: Any, label: str, run_number: int) -> float:
    if isinstance(value, str):
        cleaned = value.strip().casefold().replace(",", "")
        match = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*([k]?)\s*(?:hz|fps)?", cleaned)
        if match:
            value = float(match.group(1)) * (1000 if match.group(2) == "k" else 1)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Run {run_number} has no numeric {label}: {value!r}")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"Run {run_number} has invalid {label}: {value!r}")
    return number


def load_run_frame_rates(workbook_path: Path) -> dict[int, float]:
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Run matrix not found: {workbook_path}")
    warnings.filterwarnings(
        "ignore",
        message="Data Validation extension is not supported and will be removed",
        category=UserWarning,
        module=r"openpyxl\.worksheet\._reader",
    )
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        if "Run Log" not in workbook.sheetnames:
            raise ValueError(f"Workbook has no 'Run Log' sheet: {workbook_path}")
        sheet = workbook["Run Log"]
        header_row = None
        run_column = fps_column = None
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            names = [_column_name(value) for value in row]
            for index, name in enumerate(names):
                if name in {"run no", "run number"}:
                    run_column = index
                if name.startswith("frame rate"):
                    fps_column = index
            if run_column is not None and fps_column is not None:
                header_row = row_number
                break
        if header_row is None or run_column is None or fps_column is None:
            raise ValueError("Could not find 'Run No.' and 'Frame rate (fps)' columns in Run Log")

        frame_rates: dict[int, float] = {}
        for row in sheet.iter_rows(min_row=header_row + 1, values_only=True):
            run_value = row[run_column] if run_column < len(row) else None
            if run_value is None:
                continue
            if isinstance(run_value, bool) or not isinstance(run_value, (int, float)):
                raise ValueError(f"Invalid run number in workbook: {run_value!r}")
            run_number = int(run_value)
            if run_number != run_value:
                raise ValueError(f"Invalid non-integer run number in workbook: {run_value!r}")
            fps_value = row[fps_column] if fps_column < len(row) else None
            if fps_value is None or (isinstance(fps_value, str) and not fps_value.strip()):
                continue
            frame_rate = _positive_number(fps_value, "frame rate", run_number)
            if run_number in frame_rates:
                raise ValueError(f"Duplicate run number {run_number} in {workbook_path}")
            frame_rates[run_number] = frame_rate
        return frame_rates
    finally:
        workbook.close()
