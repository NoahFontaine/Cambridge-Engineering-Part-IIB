#!/usr/bin/env python3
"""Summarize existing PSD and POD outputs with peak tables and diagnostic plots."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal


def _read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV has no header: {path}") from exc
        rows = list(reader)
    return headers, rows


def _write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _run_label(path: Path, base: Path) -> str:
    relative = path.relative_to(base)
    for part in relative.parts:
        if re.fullmatch(r"run[_-]?\d+", part, flags=re.IGNORECASE):
            return part
    return relative.parent.name or relative.stem


def _safe_stem(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "run"


def _find_peaks(
    frequencies: np.ndarray, power: np.ndarray, prominence_fraction: float
) -> list[tuple[float, float, float]]:
    valid = np.isfinite(frequencies) & np.isfinite(power) & (frequencies > 0) & (power >= 0)
    frequencies, power = frequencies[valid], power[valid]
    if power.size < 3 or float(np.max(power)) <= 0:
        return []
    indices, properties = signal.find_peaks(
        power, prominence=float(np.max(power)) * prominence_fraction
    )
    peaks = [
        (float(frequencies[index]), float(power[index]), float(prominence))
        for index, prominence in zip(indices, properties["prominences"])
    ]
    return sorted(peaks, key=lambda peak: peak[1], reverse=True)


def _save_psd_outputs(
    psd_dir: Path, output_dir: Path, prominence_fraction: float
) -> list[dict[str, object]]:
    files = sorted(psd_dir.rglob("*_psd.csv")) if psd_dir.is_dir() else []
    (output_dir / "psd_runs").mkdir(parents=True, exist_ok=True)
    peak_rows: list[list[object]] = []
    records: list[dict[str, object]] = []
    for path in files:
        headers, rows = _read_csv(path)
        if "frequency_hz" not in headers:
            raise ValueError(f"PSD CSV is missing frequency_hz: {path}")
        freq_column = headers.index("frequency_hz")
        series_headers = [header for header in headers if header != "frequency_hz"]
        if not series_headers:
            raise ValueError(f"PSD CSV has no power column: {path}")
        run = _run_label(path, psd_dir)
        relative = path.relative_to(psd_dir).as_posix()
        figure, axis = plt.subplots(figsize=(9, 5))
        plotted = False
        for name in series_headers:
            power_column = headers.index(name)
            try:
                frequencies = np.asarray([float(row[freq_column]) for row in rows])
                power = np.asarray([float(row[power_column]) for row in rows])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Invalid numeric PSD data in {path}") from exc
            valid = np.isfinite(frequencies) & np.isfinite(power) & (frequencies > 0) & (power > 0)
            if not valid.any():
                continue
            peaks = _find_peaks(frequencies, power, prominence_fraction)
            axis.loglog(frequencies[valid], power[valid], label=name)
            plotted = True
            for rank, (frequency, peak_power, prominence) in enumerate(peaks, start=1):
                peak_rows.append([
                    run, relative, name, rank, frequency, peak_power, prominence,
                    prominence / float(np.max(power[valid])),
                ])
                axis.scatter(frequency, peak_power, marker="x", s=38, zorder=3)
                records.append({
                    "run": run, "relative": relative, "signal": name,
                    "rank": rank, "frequency": frequency,
                })
        if plotted:
            axis.set(
                title=f"{run}: PSD peaks (prominence ≥ {prominence_fraction:.0%} of max)",
                xlabel="Frequency (Hz)", ylabel="PSD",
            )
            axis.grid(True, which="both", alpha=0.25)
            axis.legend()
            figure.tight_layout()
            figure.savefig(
                output_dir / "psd_runs" / f"{_safe_stem(Path(relative).with_suffix('').as_posix())}.png",
                dpi=160,
            )
        plt.close(figure)
    _write_csv(
        output_dir / "psd_peak_summary.csv",
        [
            "run", "source_file", "signal", "peak_rank", "frequency_hz", "psd_value",
            "prominence", "prominence_fraction_of_max",
        ],
        peak_rows,
    )
    if records:
        channels = sorted({str(record["signal"]) for record in records})
        run_count = len({str(record["run"]) for record in records})
        figure, axis = plt.subplots(figsize=(max(9, run_count * 0.45), 5))
        for channel in channels:
            selected = [
                record for record in records
                if record["signal"] == channel and record["rank"] == 1
            ]
            axis.scatter(
                [record["run"] for record in selected],
                [record["frequency"] for record in selected],
                label=channel, s=35,
            )
        axis.set(title="Dominant PSD peak frequency by run", xlabel="Run", ylabel="Frequency (Hz)")
        axis.tick_params(axis="x", rotation=45)
        axis.grid(True, axis="y", alpha=0.25)
        axis.legend()
        figure.tight_layout()
        figure.savefig(output_dir / "psd_peak_frequencies.png", dpi=160)
        plt.close(figure)
    return records


def _save_pod_outputs(
    pod_dir: Path, output_dir: Path, prominence_fraction: float
) -> list[dict[str, object]]:
    energy_files = sorted(pod_dir.rglob("pod_energy.csv")) if pod_dir.is_dir() else []
    (output_dir / "pod_runs").mkdir(parents=True, exist_ok=True)
    mode_rows: list[list[object]] = []
    peak_rows: list[list[object]] = []
    runs: list[dict[str, object]] = []
    heatmap_energy: dict[str, dict[int, float]] = {}
    heatmap_frequency: dict[str, dict[int, float]] = {}

    for energy_path in energy_files:
        run = _run_label(energy_path, pod_dir)
        relative = energy_path.parent.relative_to(pod_dir).as_posix()
        energy_headers, energy_data = _read_csv(energy_path)
        energy_column = energy_headers.index("energy_fraction")
        mode_column = energy_headers.index("mode")
        energy = {
            int(row[mode_column]): float(row[energy_column]) for row in energy_data
        }
        if not energy or not np.isfinite(list(energy.values())).all():
            raise ValueError(f"POD energy fractions must be finite and non-empty: {energy_path}")
        coefficient_path = energy_path.parent / "pod_coefficients.csv"
        if not coefficient_path.is_file():
            raise FileNotFoundError(f"POD coefficients not found: {coefficient_path}")
        coefficient_headers, coefficient_data = _read_csv(coefficient_path)
        time_column = coefficient_headers.index("time_s")
        times = np.asarray([float(row[time_column]) for row in coefficient_data])
        if times.size < 3 or not np.isfinite(times).all():
            raise ValueError(f"POD time series needs at least three finite samples: {coefficient_path}")
        sample_intervals = np.diff(times)
        if np.any(sample_intervals <= 0):
            raise ValueError(f"POD timestamps must be strictly increasing: {coefficient_path}")
        sample_rate = 1.0 / float(np.median(sample_intervals))
        mode_columns = [
            (int(match.group(1)), index)
            for index, header in enumerate(coefficient_headers)
            if (match := re.fullmatch(r"mode_(\d+)", header))
        ]
        if not mode_columns:
            raise ValueError(f"POD coefficient CSV has no mode_N columns: {coefficient_path}")

        coefficients: dict[int, np.ndarray] = {}
        spectra: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        dominant_frequencies: dict[int, float] = {}
        for mode, column in mode_columns:
            values = np.asarray([float(row[column]) for row in coefficient_data])
            if not np.isfinite(values).all():
                raise ValueError(f"POD coefficients must be finite: {coefficient_path}")
            coefficients[mode] = values
            frequencies, power = signal.periodogram(
                values, fs=sample_rate, window="hann", detrend="constant", scaling="density"
            )
            spectra[mode] = frequencies, power
            peaks = _find_peaks(frequencies, power, prominence_fraction)
            dominant = peaks[0][0] if peaks else None
            if dominant is not None:
                dominant_frequencies[mode] = dominant
                heatmap_frequency.setdefault(run, {})[mode] = dominant
            for rank, (frequency, peak_power, prominence) in enumerate(peaks, start=1):
                peak_rows.append([
                    run, mode, rank, frequency, peak_power, prominence,
                    prominence / float(np.max(power[frequencies > 0])),
                ])
            mode_rows.append([
                run, relative, mode, energy.get(mode), dominant, sample_rate,
                times.size,
            ])
        heatmap_energy[run] = energy
        runs.append({
            "run": run, "relative": relative, "energy": energy,
            "coefficients": coefficients, "spectra": spectra,
            "dominant_frequencies": dominant_frequencies, "times": times,
        })

        mode_numbers = sorted(coefficients)
        leading_modes = mode_numbers[: min(6, len(mode_numbers))]
        figure, axes = plt.subplots(3, 1, figsize=(11, 12))
        ordered = sorted(energy)
        axes[0].bar(ordered, [energy[mode] for mode in ordered], color="steelblue")
        axes[0].set(title=f"{run}: POD modal energy", xlabel="Mode", ylabel="Energy fraction")
        axes[0].set_ylim(bottom=0)
        axes[0].grid(True, axis="y", alpha=0.25)
        cumulative = np.cumsum([energy[mode] for mode in ordered])
        energy_axis = axes[0].twinx()
        energy_axis.plot(ordered, cumulative, color="darkorange", marker=".", linewidth=1)
        energy_axis.set_ylabel("Cumulative energy fraction")
        energy_axis.set_ylim(0, 1.02)

        for mode in leading_modes:
            coefficient = coefficients[mode]
            scale = float(np.max(np.abs(coefficient)))
            if scale > 0:
                axes[1].plot(times, coefficient / scale, label=f"Mode {mode}")
        axes[1].set(
            title="Leading POD coefficients (normalized independently)",
            xlabel="Time (s)", ylabel="Normalized coefficient",
        )
        axes[1].grid(True, alpha=0.25)
        axes[1].legend(ncol=3)
        for mode in leading_modes:
            frequencies, power = spectra[mode]
            positive = (frequencies > 0) & (power > 0)
            if positive.any():
                normalized = power[positive] / np.max(power[positive])
                axes[2].semilogy(frequencies[positive], normalized, label=f"Mode {mode}")
                peaks = _find_peaks(frequencies, power, prominence_fraction)
                if peaks:
                    axes[2].scatter(
                        [peak[0] for peak in peaks[:1]], [1.0], marker="x", s=35
                    )
        axes[2].set(
            title="POD coefficient spectra (each normalized to its own peak)",
            xlabel="Frequency (Hz)", ylabel="Normalized spectral density",
        )
        axes[2].grid(True, which="both", alpha=0.25)
        axes[2].legend(ncol=3)
        figure.suptitle(f"POD diagnostics: {run} (sample rate ≈ {sample_rate:g} Hz)")
        figure.tight_layout()
        figure.savefig(output_dir / "pod_runs" / f"{_safe_stem(relative)}.png", dpi=160)
        plt.close(figure)

    _write_csv(
        output_dir / "pod_mode_summary.csv",
        [
            "run", "run_output_path", "mode", "energy_fraction",
            "dominant_frequency_hz", "coefficient_sample_rate_hz", "coefficient_samples",
        ],
        mode_rows,
    )
    _write_csv(
        output_dir / "pod_mode_frequency_peaks.csv",
        [
            "run", "mode", "peak_rank", "frequency_hz", "spectral_density",
            "prominence", "prominence_fraction_of_max",
        ],
        peak_rows,
    )
    if runs:
        _save_pod_heatmap(
            output_dir / "pod_energy_heatmap.png", heatmap_energy,
            "POD modal energy fraction by run", "Energy fraction",
        )
        _save_pod_heatmap(
            output_dir / "pod_frequency_heatmap.png", heatmap_frequency,
            "Dominant POD coefficient frequency by run", "Frequency (Hz)",
        )
    return runs


def _save_pod_heatmap(
    path: Path, values: dict[str, dict[int, float]], title: str, colorbar_label: str
) -> None:
    runs = list(values)
    modes = sorted({mode for data in values.values() for mode in data})
    matrix = np.full((len(modes), len(runs)), np.nan)
    for column, run in enumerate(runs):
        for row, mode in enumerate(modes):
            if mode in values[run]:
                matrix[row, column] = values[run][mode]
    figure, axis = plt.subplots(figsize=(max(9, len(runs) * 0.45), 7))
    image = axis.imshow(np.ma.masked_invalid(matrix), aspect="auto", origin="lower", cmap="viridis")
    axis.set(
        title=title, xlabel="Run", ylabel="POD mode",
        xticks=np.arange(len(runs)), xticklabels=runs,
        yticks=np.arange(len(modes)), yticklabels=modes,
    )
    axis.tick_params(axis="x", rotation=45)
    figure.colorbar(image, ax=axis, label=colorbar_label)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def visualize(
    psd_dir: Path, pod_dir: Path, output_dir: Path, prominence_fraction: float = 0.05
) -> None:
    if not 0 <= prominence_fraction < 1:
        raise ValueError("--peak-prominence-fraction must be in [0, 1)")
    output_dir.mkdir(parents=True, exist_ok=True)
    psd_count = len(list(psd_dir.rglob("*_psd.csv"))) if psd_dir.is_dir() else 0
    pod_count = len(list(pod_dir.rglob("pod_energy.csv"))) if pod_dir.is_dir() else 0
    if psd_count == 0 and pod_count == 0:
        raise ValueError(f"No PSD or POD result files found under {psd_dir} and {pod_dir}")
    _save_psd_outputs(psd_dir, output_dir, prominence_fraction)
    _save_pod_outputs(pod_dir, output_dir, prominence_fraction)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--psd-dir", type=Path, default=Path("results"))
    parser.add_argument("--pod-dir", type=Path, default=Path("results/pod"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/visualizations"))
    parser.add_argument(
        "--peak-prominence-fraction", type=float, default=0.05,
        help="Minimum local-peak prominence as a fraction of each spectrum's maximum",
    )
    args = parser.parse_args()
    try:
        visualize(args.psd_dir, args.pod_dir, args.output_dir, args.peak_prominence_fraction)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    print(f"Wrote PSD and POD visualizations to {args.output_dir}")


if __name__ == "__main__":
    main()
