# Shadowgraph shock/separation analysis

These scripts implement selected image-based methods in [`../Quantifying_Shock_and_Separation_Unsteadiness.pdf`](../Quantifying_Shock_and_Separation_Unsteadiness.pdf):

- pixel-wise mean, standard deviation, skewness and kurtosis maps;
- scalar pixel-SD unsteadiness index;
- subpixel shock tracking, position distribution and RMS/SD;
- space-time diagram and Welch shock-position spectrum;
- optional hysteresis-based video intermittency \(\gamma(x)\) and footprint;
- optional thresholded bubble-signature area/state, cycle and dwell-time statistics.

The analysis is deliberately transparent and tunable rather than using a pretrained object detector. Shadowgraph intensity is not a direct measurement of density, separation, or reverse flow. In particular, bubble-signature area is only an image-based proxy; validate masks and states against representative frames, LDV, or other measurements before treating them as physical bubble dimensions.

Use Python 3.10 or newer. UV manages the project environment and lockfile.

## Setup

From this directory, create/sync the virtual environment and install dependencies with UV:

```bash
uv sync --extra dev
```

Run commands with `uv run ...` (or activate `.venv` if you prefer). Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

## Single-video example

First make a contact sheet to inspect the flow and choose ROIs without analyzing the full video:

```bash
uv run python preview_shadowgraph.py \
  --video ../michaelmas_data/videos/run14/run14.mp4 \
  --output results/run14_frames.png
```

Then analyze a video with ROIs selected from that preview:

```bash
uv run python analyze_shadowgraph.py \
  --video ../michaelmas_data/videos/run14/run14.mp4 \
  --output-dir results/run14 \
  --run-matrix ../michaelmas_runs.xlsx \
  --frame-step 10 \
  --shock-roi 80,80,560,300
```

ROI coordinates are `x0,y0,x1,y1` in the **original video** pixels; the right/bottom endpoints are exclusive. The shock tracker averages rows in the selected box, smooths the profile, then finds the strongest absolute streamwise intensity gradient with a parabolic subpixel fit. Use a box containing only the expected shock segment. The default box is the full image and is mainly a smoke-test fallback, not a recommended scientific setting.

The analyzer also writes `preview.png` with the selected boxes: shock (red), statistics (green), intermittency (blue), and bubble (magenta). Do not assume one ROI is suitable for every camera framing.

The MP4s are slow-motion playback files at 30 fps, while each frame represents a sample at the original camera acquisition rate. The analyzer reads the **camera acquisition fps** from the `Frame rate (fps)` column in the Excel `Run Log`, not from MP4 metadata. For example, 1,000 camera frames recorded at 1 kHz represent 1 second of physical flow, even though playback takes 33.333 seconds at 30 fps. In single-video mode, `--run-matrix` reads the run number from a `runN` folder or filename; alternatively, use `--fps 1000` to supply the original acquisition rate directly. The summary records both the 30 fps container/playback value and the acquisition fps used for analysis.

For quantitative frequency work, analyze every frame (`--frame-step 1`). A larger step lowers the effective sampling rate to `camera_acquisition_fps / frame_step`; this can alias the oscillation. The x-axis timestamps, cycle times, PSD frequency and Strouhal calculation use the original camera sampling rate. With the recorded rates, the 1 kHz runs cannot resolve a 600 Hz signal; use 10 kHz or faster recordings for that frequency.

## Optional methods

### Video intermittency

Select a narrow strip along the wall and thresholds from the intensity histogram at an intermittent location. For example:

```bash
--gamma-roi 60,310,580,320 --gamma-low 90 --gamma-high 115
```

The state enters when grayscale rises above `gamma-high`, leaves below `gamma-low`, and otherwise retains its previous value. Use `--gamma-invert` when the post-shock state is darker. The script reports \(\gamma(x)\) and the span between the first and last positions with \(0.05<\gamma<0.95\). Try threshold perturbations (e.g. ±20%) and report the chosen convention.

### Bubble signature

```bash
--bubble-roi 180,180,560,400 --bubble-diff-threshold 12 --min-component-area 20
```

By default, this second-pass analysis thresholds absolute frame-to-temporal-mean intensity differences inside the ROI, applies a small morphological cleanup, and records the largest connected component. If you have a clear attached/no-bubble frame, pass its original frame number with `--bubble-reference-frame` instead; it must be sampled by `--frame-step`. This often gives a more interpretable state signal than the temporal mean. The script writes `bubble_signature.csv` (component area, bounding box, and streamwise extent) and representative red-mask overlays under `bubble_overlays/`. Inspect these overlays and tune the ROI, threshold, reference, and minimum area; a shock, shear layer, or illumination fluctuation can also produce a component. The reported bubble-signature metrics are not automatically \(A_{sep}\) or \(L_{sep}\). The SD-threshold scalar index defaults to 15 grayscale levels; set `--sd-threshold` using a measured noise floor and test sensitivity.

### Calibration and Strouhal number

`--mm-per-pixel` is millimetres per **native-resolution** pixel. Pixel positions in output plots/CSVs use analysis pixels after `--scale`; reported physical lengths account for the scale. To calculate \(St=fL/U\), supply both `--length-scale-mm` and `--velocity-m-s`. State the physical length scale and velocity used when presenting the result.

## Outputs

Each analysis directory contains:

- `summary.json`: settings and headline metrics, including missing-shock fraction;
- `preview.png` with the selected analysis regions, `shock_position.csv` (mm columns are populated when calibrated), `xt_diagram.png`, and, when enough valid frames exist, `shock_psd.csv` / `shock_psd.png`;
- `pixel_statistics.npz` and `mean.png`, `sd.png`, `skewness.png`, `kurtosis.png`;
- optional `gamma_profile.csv` / `gamma_profile.png`;
- optional `bubble_signature.csv` and validation overlays.

The PSD is omitted when too many shock detections are missing (default limit 5%). If the limit is met, missing positions are linearly interpolated before Welch estimation; report this and check sensitivity. Results are not reliable if the search box locks onto a different edge.

## Batch processing

The batch runner applies common settings to every video under a folder and writes one `batch_summary.csv`:

```bash
uv run python batch_analyze_videos.py \
  --input-dir ../michaelmas_data/videos \
  --output-dir results/all_runs \
  --workbook ../michaelmas_runs.xlsx -- \
  --frame-step 1 --shock-roi 80,80,560,300
```

Batch processing matches each `runN` video directory/filename to the workbook's run number and reads that run's acquisition rate. It fails instead of silently using playback fps if a run is unmatched or has no frame rate. Choose a common ROI only if camera framing is consistent across runs. Supply per-run metadata (e.g. operating condition, calibration, velocity) separately before comparing parameter sweeps.

Pressure and LDV files are not treated as high-bandwidth video signals here. In particular, pressure tappings with tubing response near 33 Hz cannot validate a several-hundred-Hz oscillation.
