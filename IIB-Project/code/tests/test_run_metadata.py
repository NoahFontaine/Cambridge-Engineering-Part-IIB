from pathlib import Path

import pytest
from openpyxl import Workbook

from run_metadata import infer_run_number, load_run_frame_rates


def test_loads_camera_rates_by_run_number(tmp_path: Path):
    workbook_path = tmp_path / "runs.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Run Log"
    sheet.append(["Run No.", "Run Name", "Frame rate\n(fps)"])
    sheet.append([1, "Run 1", 1000])
    sheet.append([12, "Run 12", 10000])
    workbook.save(workbook_path)

    assert load_run_frame_rates(workbook_path) == {1: 1000.0, 12: 10000.0}


def test_omits_runs_without_a_numeric_acquisition_rate(tmp_path: Path):
    workbook_path = tmp_path / "runs.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Run Log"
    sheet.append(["Run No.", "Frame rate (fps)"])
    sheet.append([2, None])
    workbook.save(workbook_path)

    assert 2 not in load_run_frame_rates(workbook_path)


@pytest.mark.parametrize(
    ("path", "run_number"),
    [
        (Path("run14/run14.mp4"), 14),
        (Path("/data/Run_0012.MOV"), 12),
    ],
)
def test_infers_run_number(path: Path, run_number: int):
    assert infer_run_number(path) == run_number
