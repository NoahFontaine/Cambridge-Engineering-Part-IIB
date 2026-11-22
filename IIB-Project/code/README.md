# Shadowgraph shock/separation analysis

These scripts implement selected image-based methods in [`../Quantifying_Shock_and_Separation_Unsteadiness.pdf`](../Quantifying_Shock_and_Separation_Unsteadiness.pdf):

- pixel-wise mean, standard deviation, skewness and kurtosis maps;
- scalar pixel-SD unsteadiness index;
- subpixel shock tracking, position distribution and RMS/SD;
- space-time diagram and Welch shock-position spectrum;
- optional hysteresis-based video intermittency \(\gamma(x)\) and footprint;
- optional thresholded bubble-signature area/state, cycle and dwell-time statistics.
- ROI-masked statistics, streamline-motion tracking, Proper Orthogonal Decomposition (POD), and Dynamic Mode Decomposition (DMD) in separate scripts.

The analysis is deliberately transparent and tunable rather than using a pretrained object detector. Shadowgraph intensity is not a direct measurement of density, separation, or reverse flow. In particular, bubble-signature area is only an image-based proxy; validate masks and states against representative frames, LDV, or other measurements before treating them as physical bubble dimensions.

Use Python 3.10 or newer. UV manages the project environment and lockfile.

## Setup

From this directory, create/sync the virtual environment and install dependencies with UV:

```bash
uv sync --extra dev
```

Run commands with `uv run ...` (or activate `.venv` if you prefer). Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

## Split workflow (recommended)

Select ROIs separately for each run, using the middle frame of every video:

```bash
uv run python select_rois.py \
  --input-dir ../michaelmas_data/videos \
  --output results/rois.json
```

Drag shock, separation-bubble, and boundary-layer/light-streamline boxes in the displayed frame, then press Enter to accept each one. Shock and bubble ROIs may be skipped for cases without those features; the boundary-layer ROI is required for motion tracking. For the optional aerofoil exclusion, click inside the dark aerofoil: the connected dark region is previewed as a filled overlay with an outline. Click again to reseed, use `+` / `-` to adjust the intensity tolerance, Enter to accept, or Esc to skip. The stored exclusion is a polygon rather than a rectangular box, so the non-square aerofoil outline is excluded without masking adjacent flow.

The generated manifest is editable. Set `"regime"` to `"subsonic"` or `"sbli"` (or `null`), set `"wall_edge"` to `"top"` or `"bottom"` according to the wall's position in the boundary-layer ROI, and tune `"attached_fraction"` / `"detached_fraction"` as needed. The tracker classifies the light streamline by its distance from the wall: it reports attached, detached, transition, or intermittent behavior. The continuous distance signal's Welch spectrum reports its dominant motion frequency. This is an image-based proxy rather than a direct measurement of reversed flow. Shock presence, bubble-signature presence, regime, and attachment are kept as separate signals; regime is not inferred from images.

Pixel statistics, POD, and DMD use the **entire frame, including the aerofoil**. Their maps and modes do not apply the aerofoil exclusion polygon or limit analysis to the shock, bubble, or boundary-layer boxes. The shock, bubble, and boundary-layer boxes and aerofoil exclusion remain available for the tracking workflow.

All commands below accept `--input-dir` for batch runs or `--video` for one run. Batch commands require `--workbook` with each run's original camera acquisition rate. For one video, use `--fps N` instead. The MP4 playback frame rate is not the physical sampling rate.

### Pixel statistics and scalar unsteadiness (1.1 and 1.2)

```bash
uv run python pixel_statistics.py \
  --input-dir ../michaelmas_data/videos \
  --roi-config results/rois.json \
  --output-dir results/pixel_statistics \
  --workbook ../michaelmas_runs.xlsx \
  --frame-step 1
```

Writes mean, SD, skewness, and kurtosis maps plus `unsteadiness.csv`. Its time signals are ROI-mean absolute and RMS deviations from the temporal mean and the fraction of ROI pixels exceeding `--sd-threshold`; Welch PSDs are written when enough samples exist.

### Shock, bubble, and boundary-layer tracking (1.3)

```bash
uv run python track_flow.py \
  --input-dir ../michaelmas_data/videos \
  --roi-config results/rois.json \
  --output-dir results/tracking \
  --workbook ../michaelmas_runs.xlsx \
  --frame-step 1
```

Shock detection is skipped if its ROI is absent. For each run with a configured shock ROI, the output directory also contains `shock_motion.mp4`, showing the tracked shock location over the frames and its time within the run. The video follows the input playback cadence (adjusted for `--frame-step`); its marker reports analysis-pixel coordinates. Bubble-signature detection is optional and remains an image proxy; inspect `bubble_signature.csv` and tune `--bubble-diff-threshold` using representative frames. Boundary-layer outputs include `boundary_layer_motion.csv`, attachment-state labels, and a streamline-distance PSD when enough samples exist.

### Proper Orthogonal Decomposition (1.11)

```bash
uv run python pod_analysis.py \
  --input-dir ../michaelmas_data/videos \
  --roi-config results/rois.json \
  --output-dir results/pod \
  --workbook ../michaelmas_runs.xlsx \
  --max-snapshots 300 --rank 20
```

POD uses an SVD of mean-subtracted ROI snapshots and writes spatial modes, temporal coefficients, and modal energy fractions.

### Dynamic Mode Decomposition (1.12)

```bash
uv run python dmd_analysis.py \
  --input-dir ../michaelmas_data/videos \
  --roi-config results/rois.json \
  --output-dir results/dmd \
  --workbook ../michaelmas_runs.xlsx \
  --max-snapshots 300 --rank 20
```

DMD uses consecutive, uncentered ROI snapshots and writes spatial modes, eigenvalues, frequencies, and growth rates. POD and DMD automatically thin long videos to at most `--max-snapshots` snapshots. Interpret frequencies using the acquisition rate and resulting snapshot interval. Use every frame for quantitative frequency work when possible; larger frame steps can alias oscillations.

### PSD peak and POD visualization

After running the pixel-statistics and POD analyses, summarize and visualize the saved results:

```bash
uv run python visualize_analysis.py \
  --psd-dir results \
  --pod-dir results/pod \
  --output-dir results/visualizations
```

The PSD search defaults to the `results` tree, so it includes spectra from pixel statistics and tracking; use a narrower `--psd-dir` if you want to limit the source data. The script marks local PSD peaks in per-run plots and writes `psd_peak_summary.csv` with each peak's frequency, power, prominence, and rank. `psd_peak_frequencies.png` compares each signal's strongest peak across runs. For POD, it writes per-run energy, coefficient time-series, and coefficient-spectrum diagnostics, plus energy and dominant-frequency heatmaps. `pod_mode_summary.csv` reports each mode's energy fraction and dominant coefficient frequency; `pod_mode_frequency_peaks.csv` lists all detected modal spectral peaks. Peak detection uses local prominence of at least 5% of the maximum spectrum by default; adjust with `--peak-prominence-fraction`. POD frequencies are computed from the saved coefficient time stamps, so their resolution is bounded by the analyzed record duration and snapshot spacing.

### Animate the leading POD modes as smooth harmonic oscillations

Create one four-panel video per run from the four modes with the highest energy fractions:

```bash
uv run python pod_mode_videos.py \
  --pod-dir results/pod \
  --output-dir results/pod_mode_videos_smooth \
  --video-fps 30 \
  --display-frequency-hz 1 \
  --cycles 3
```

Each panel shows one mode's spatial field multiplied by an idealized sinusoidal-harmonic coefficient. Its frequency is estimated from the saved POD coefficient spectrum and fitted to the coefficient history; the animation then slows each mode to the chosen display frequency (1 Hz by default) so oscillations are easy to see. Playback stays at 30 fps, giving 30 frames per cycle, and the default three cycles make a smooth, three-second video. The panel and `pod_mode_videos.csv` report both the measured POD frequency and the displayed frequency. These are illustrative SHM animations, not reconstructions of the original time-varying flow. The color scale remains fixed during each mode's animation.

## Single-video example

The `analyze_shadowgraph.py` and `batch_analyze_videos.py` examples below document the earlier combined workflow; they do not consume the per-video ROI manifest or mask maps to the selected regions. Use the split scripts above when excluding the aerofoil or distant regions.

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
