# Quantifying and Controlling Shock-Wave / Separation Unsteadiness
### Research notes for MEng/MSc project, building on Dickinson (2024) crosswind intake rig

**Conventions used for sourcing** (so you know what to double-check):

- **[T]** = taken directly from Luke Dickinson's thesis (page/section given where possible)
- **[S]** = found in a web search during this session (abstract, review or thesis page; I did not read every paper in full)
- **[K]** = my general background knowledge. Plausible and standard, but verify before you cite it.

Where I give numbers that depend on rig dimensions I have not been able to read from the thesis text (the figures are images), they are marked **ILLUSTRATIVE** and need replacing with your real values.

---

## 1. What the thesis already tells you

### 1.1 Two different unsteady phenomena are present in the rig

| | **A. Baseline: "weak" unsteadiness** | **B. Near-critical separation: bubble cycling** |
|---|---|---|
| Condition | M_entry = 0.150, MFS = 1, P0 = 201.3 kPa, Re = 1.0×10⁶ [T §6.1] | M_entry = 0.1575 (between 0.155 and 0.160, where peak isentropic Mach plateaus) [T §7.2.1] |
| Flow state | Attached SBLI, peak M_is ≈ 1.35, multiple weak shocks ahead of the final one [T §6.1] | Intermittent shock-induced separation bubble at the highlight [T §7.2.1] |
| Evidence | Shadowgraph SD image: high SD at the edges of the supersonic region, low SD in the core. Smeared supersonic region in the time-average [T §6.1] | 50,000 fps shadowgraph (0.54 ms between panels shown): shock visible → bubble forms, shock disappears → large separation → convects downstream → boundary layer reattaches → repeats [T Fig 7.15] |
| Quantification so far | Qualitative (SD of pixel intensity) | Rough **~600 Hz** from counting frames; thesis explicitly says no exact value because there were no unsteady pressure measurements [T §7.2.1] |
| Supporting data | Oil flow shows oil pooling just behind the shock, so the boundary layer may be close to separation [T §6.1] | LDV at the throat near the wall: velocity histograms become bimodal, with substantial positive and negative velocities at the same point [T Figs 7.17–7.18]. SD of pixel intensity peaks just downstream of the supersonic region [T Fig 7.16] |

### 1.2 The mechanism the thesis proposes for B
A separation bubble forms because the shock is strong enough to separate the boundary layer. Separation reduces streamline curvature, which weakens the shock. The weakened shock can no longer sustain separation, so the bubble convects downstream and the boundary layer reattaches. The cycle then restarts [T §7.2.1, §9.2.3]. This is a **feedback loop between shock strength, streamline curvature and separation**, which is a different picture from the classical "low-frequency breathing" of supersonic SBLIs (see §4). This matters for choosing which Strouhal scaling is meaningful.

### 1.3 Things the thesis explicitly says are unknown or missing (your project gaps)

1. No dynamic pressure measurements. The existing static tappings, through neoprene tubing, behave as a low-pass filter with a cut-off of about 33 Hz, based on Bruce's findings on a similar system, so they are only quasi-steady [T §5.2].
2. The exact frequency of the unsteadiness is unknown. The thesis recommends **flush-mounted high-frequency-response pressure transducers** to resolve it and to link upstream separation response to the downstream boundary layer (LDV) [T §9.3].
3. It is unknown whether the unsteadiness depends on Reynolds number. The thesis suggests varying stagnation pressure and/or using a scaled model [T §9.3].
4. It may also occur at other M_entry values close to critical separation [T §7.2.1], so the map of *where* it occurs is incomplete.
5. Vortex generators are suggested as an untested way to extend the performance envelope; the type, position and height are "unknown at present" [T §9.3].

### 1.4 Useful rig facts for your calculations

- Baseline boundary layer upstream of the interaction: δ/D = 0.069, δ*ᵢ/D = 0.020, θᵢ/D = 0.011, Hᵢ = 1.78, where D is the intake thickness at the throat [T Table 6.2].
- The thesis mentions δ = 3 mm in the LDV alignment-accuracy discussion [T §5.4]. If that is the baseline δ, it implies D ≈ 43 mm (3 / 0.069). **Check against the Fig 4.3 dimensions before using this.**
- Camera: Photron FASTCAM NOVA S-6, 640×480 px at the standard settings. Baseline images were taken at 1000 fps for 10 s (10,000 frames); the unsteady case at 50,000 fps (100,000 frames over 2 s) [T §5.1, Fig 7.16]. Resolution drops as frame rate rises, so check the actual pixel dimensions of the 50 kHz recordings.
- Sidewall separations exist near the walls but were judged far enough from the shock not to affect it [T §6.1]. This matters if you add control devices spanwise.

---

## 2. Quantification toolbox

Your original notes list the main metrics. This section extends them, ties each to the instrument you could actually use on this rig, and flags rig-specific pitfalls.

### 2.1 Summary table

| Metric | What it tells you | Instrument | Feasible with existing data? |
|---|---|---|---|
| **Shock position σ_xs** (RMS about mean), plus PDF, skewness | Amplitude of the shock excursion | Shadowgraph (track shock edge per frame) | **Yes**, for the 50 kHz video, and probably the 1 kHz video for slow motion |
| **x–t diagram** along a line parallel to the wall | Visual proof of periodicity, shock/bubble motion direction and speed | Shadowgraph | **Yes** |
| **Pixel-wise SD, skewness and kurtosis maps** | Where unsteadiness lives. You already have SD maps; higher moments distinguish intermittent from Gaussian-like motion | Shadowgraph | **Yes** |
| **Pixel-wise (or line-wise) PSD / spectral map** | Frequency content at every location, so you can see where the ~600 Hz peak is strongest | Shadowgraph at ≥ 10 kHz | **Yes** (50 kHz data) |
| **Intermittency γ(x)** | Fraction of time at position x that the flow is "post-shock" or "separated" | Wall pressure (ideal) or shadowgraph intensity (proxy) | Proxy only; the pressure version needs new transducers |
| **Footprint Δx_foot** (e.g. 0.05 < γ < 0.95) | Streamwise extent of shock/foot travel | As above | As above |
| **p_rms(x) and its peak** | Unsteady loading intensity | Flush dynamic transducers | **No** (new hardware) |
| **PSD / premultiplied f·PSD** of wall pressure | Dominant frequencies and their energy | Transducers | **No** |
| **St = fL/U** | Non-dimensional frequency for comparison with literature | Any of the above | Yes, once f is known |
| **Coherence / cross-correlation / lag** between two signals | Causality (shock → bubble or bubble → shock; upstream → shock) | ≥ 2 transducers, or transducer + video, or video line pairs | Partly (video line pairs); full version needs transducers |
| **Backflow probability** χ (fraction of time U < 0) | Direct measure of intermittent separation | LDV near wall | **Yes** (existing LDV histograms; re-process) |
| **Bubble length or area L_sep(t), A_sep(t)** | Separation unsteadiness (the second thing you need to quantify) | Shadowgraph (segment the bubble) plus oil flow for the mean | Yes, with image processing |
| **POD / DMD** | Coherent modes and their frequencies | Shadowgraph image sequence | **Yes** |
| **Cycle statistics**: period distribution, bubble occurrence probability, dwell times in attached/separated states | Distinguishes a periodic limit cycle from stochastic switching | Any time series | Yes |

### 2.2 Shock position from shadowgraph

Shadowgraph shows the second derivative of density, not the shock position directly [T §5.1], so you need a defined tracking rule. Options:

1. **Gradient or threshold crossing along a line.** Choose a line (or several) roughly parallel to the wall at fixed y, extract the intensity profile I(x, t), locate the sharp dark-to-light transition or the peak of |∂I/∂x|, and record x_s(t). Repeat at several y to see whether the shock tilts or "rocks". [K]
2. **Background-subtracted ridge detection.** Subtract a time-mean image, then locate the extremum of the fluctuation field. Less sensitive to illumination drift. [K]
3. **Template or correlation tracking** if the shock structure stays similar frame to frame. [K]

Practical cautions [K]:

- Calibrate mm/pixel from a known feature (tapping hole spacing, intake dimension).
- Report the localisation uncertainty (about ±1 px is typical for edge detection; sub-pixel interpolation helps).
- Note that near critical separation the shock *vanishes* from the image when the bubble forms (thesis Fig 7.15c). A tracker will fail there. Treat "shock absent" as a state in its own right instead of forcing a position. This is itself a useful metric (fraction of time with no resolvable shock).
- Mask the model surface and check there is no vibration of the rig or camera that mimics motion.

### 2.3 Intermittency analysis

**Classic definition** (Dolling & Murphy; Dolling & Or) [S]: wall pressure under a moving shock foot is intermittent, switching between an "upstream" level and a "downstream" level. Using thresholds on the pressure signal, γ(x) is the fraction of time the signal is in the downstream/shocked state. The intermittent region is where the shock foot translates, and in separated interactions it is a region of intermittent separation [S].

**Thresholds**: the commonly used approach is the **two-threshold (hysteresis) method**, which converts the pressure trace to a boxcar (0/1) signal and from it yields the shock-foot position history, crossing frequency and mean shock velocity [S; Nowlin 1993, Dolling & Brusniak]. Thresholds are normally set relative to the upstream and downstream pressure levels and the local standard deviation [K], so report your threshold choice and show sensitivity to it.

**Observed statistics in supersonic cases** [S]: the shock-foot position is approximately normally distributed (Dolling and co-workers' fin and ramp data). **Check whether this holds in your transonic case.** A skewed or bimodal x_s PDF would be significant evidence of switching between attached and separated states, which is what the thesis LDV histograms (Fig 7.18d) already hint at.

**Video proxy for γ** [K]: for each pixel, threshold the intensity relative to the "supersonic region present" and "not present" levels and compute the fraction of frames in each state. Validate against pressure when you have transducers.

**Footprint thresholds** such as 0.05 < γ < 0.95 are conventions, not universal; state yours.

**Wavelet alternative** [S]: Bernardini et al. (JFM 2023) used a wavelet transform and a "local intermittency measure" (a frequency-dependent flatness factor) to isolate intermittent bursts of the shock scale by scale. This is more advanced, but potentially useful if your spectra show more than one band.

### 2.4 Spectral analysis and Strouhal number

**Spectral estimation** [K]:

- Use Welch's method (segment averaging, e.g. Hann window, 50% overlap). Choose segment length so you have ≥ ~20–50 segments for a stable estimate but still resolve the lowest frequency of interest.
- Plot both PSD (log–log) and **premultiplied f·PSD vs log f**. The latter shows where the *energy* is, because equal areas under the curve mean equal variance.
- Frequency resolution Δf = 1/T_segment. At 50 kHz for 2 s you have up to 100,000 samples, which is plenty for ~600 Hz. For low-frequency work (hundreds of times lower than the bubble frequency) you need long records instead.

**Nyquist check on the existing data** [K, from numbers in T]: the baseline and parameter-sweep videos were captured at 1000 fps, so the Nyquist frequency is 500 Hz. A ~600 Hz process would be **aliased** (it would appear near 400 Hz in a spectrum). The pixel-SD images are not strongly affected as variance estimates (aliasing folds energy rather than removing it), provided the exposure per frame is short compared with the cycle, but any spectrum or "frequency" you derive from the 1 kHz recordings is unreliable for near-critical cases. Use the 50 kHz recordings for frequency work, and consider re-recording the key cases at ≥ 10 kHz (≥ ~15× the expected frequency gives a good waveform, not just the peak).

**Strouhal number**: St = f·L/U. The choice of L and U must be stated, because the literature uses different ones:

| Scaling | Typical use | Literature range [S unless noted] |
|---|---|---|
| St_L = f·L_sep/U∞ | Separated oblique and normal-shock SBLI. Dussauge & Piponniau report ramp-induced interaction unsteadiness at roughly 0.02–0.05 | ~0.01–0.05 (your notes), 0.02–0.05 (Dussauge & Piponniau, quoted in review) |
| St_δ = f·δ/U∞ | Boundary-layer scaling. Low-frequency motion is often given as f ~ O(0.01 U∞/δ) | ~0.01 (from a transonic-nozzle STBLI paper) |
| St_c = f·c/U∞ | Transonic airfoil buffet [K] | ~0.06–0.07 for typical buffet [K, verify] |
| St_D = f·D/U | The natural option for this rig, using intake throat thickness D | none to compare with, so you would be establishing it |

**ILLUSTRATIVE** estimate for case B (replace with real numbers): shock Mach ≈ 1.35, T0 ≈ 293 K gives U ≈ 400 m/s upstream of the shock. With f ≈ 600 Hz and D ≈ 43 mm: St_D ≈ 0.065. With δ ≈ 3 mm: St_δ ≈ 0.0045. Without a measured L_sep these cannot be compared directly with the 0.01–0.05 band. Do not assume the 600 Hz is the "classical" low-frequency mode (see §4).

Also worth reporting: 1/f in cycles per bubble convection time. If the bubble convects at a fraction of U_e over a distance of order L_sep, the shedding frequency may be predicted from convection length scales (a check on the thesis's mechanism) [K].

### 2.5 Wall-pressure measurements (what you will probably need to add)

The thesis explicitly points to this as the next step [T §9.3].

- **Sensors**: flush-mounted miniature piezoresistive transducers (Kulite-type) with a flat response well above the expected frequencies (target ≥ 5–10 kHz for a 600 Hz signal) [K]. Needs pressure taps designed into the 3D-printed intake (the existing tappings are 0.5 mm with hypodermic tubes; those cannot be reused for dynamic work because of the tubing response noted above [T §5.2]).
- **Placement**: a streamwise array across the highlight region (where the shock moves) and further downstream beneath the bubble and its reattachment region, plus at least one upstream reference. This gives γ(x), p_rms(x), and cross-correlations. Place sensors so that shock-foot excursion (a few mm) is covered at < ~1 mm spacing if possible [K].
- **Sampling**: ≥ 20–50 kHz; anti-alias filter below Nyquist; record long enough for hundreds of cycles.
- **Calibration**: static calibration against the reference pressure before and after each run; note temperature sensitivity [K].
- **Time-synchronise** the transducers with the high-speed camera (trigger signal recorded on a spare channel) so you can cross-correlate shock position from video with the pressure signals.
- **Analysis**: p_rms(x), skewness and kurtosis, γ(x), PSD per sensor, coherence and cross-correlation between neighbouring sensors, and conditional averaging of pressure on separation events detected in video.

A note on a recent technique [S]: an MDPI paper (2024) on screen-printed PVDF transducers for SWBLI unsteadiness emphasises that *low-frequency* pressure accuracy is the difficult part of unsteadiness studies. PVDF is an AC-coupled sensor type and not suited to very low frequency; for your ~hundreds-of-Hz phenomenon, standard piezoresistive transducers are the safer choice [K].

### 2.6 LDV-based separation metrics

Your LDV data already show reversed flow intermittently near the wall at the throat [T §7.2.1]. Things you can compute from raw data (you will need the raw burst data, not just the plotted histograms):

- **Backflow probability** (also called the intermittent-reversal fraction): fraction of validated samples with U < 0 at each y.
- **Mean, SD, skewness and bimodality of u(y)** to show where the near-wall switching happens (the thesis finds it is near-wall).
- **Time-resolved statistics** are difficult because LDV samples at random times (particle arrival), so spectra require techniques such as slot correlation or sample-and-hold with proper caveats [K]. A simpler and more defensible option is to use conditional averaging of LDV samples on an event signal (shadowgraph or pressure) if synchronised.
- **Velocity bias** raises measured fluctuation levels; the thesis quotes a ~4% error in U′ near the wall from this effect [T §5.4.4]. Quote it when you report u′.
- The same LDV data give downstream boundary-layer parameters (δ*, θ, H_i), the quantities that matter for fan performance. A **time-varying shape factor** would be the ideal downstream consequence metric, but with point LDV only conditional or statistical estimates are possible.

### 2.7 Data-driven decomposition

- **POD** (snapshot method) on shadowgraph frames: isolates dominant spatial modes and temporal coefficients. In a limit-cycle situation the first pair of modes typically forms a phase-shifted pair that traces a circle in the coefficient plane, a clean demonstration of periodicity [K]. Use fluctuating images (mean subtracted), a masked region of interest and a few thousand frames spanning many cycles.
- **DMD**: gives modes at specific frequencies and growth rates. Useful for checking whether ~600 Hz is a single clean mode, and for finding secondary frequencies. DMD is sensitive to noise and to the chosen truncation rank, so show the spectrum of eigenvalues and test robustness [K].
- Treat both as *descriptive* tools. Shadowgraph intensity is not a linear function of density, so mode amplitudes are qualitative.

### 2.8 Convergence and uncertainty

For every statistic, report [K]:

- Number of independent cycles or shock excursions behind the number (use autocorrelation time to estimate independent samples).
- Bootstrap or block-bootstrap confidence intervals for σ_xs, γ and spectral peak frequency.
- Repeatability: repeat runs on different days, since the wind tunnel stagnation conditions drift and the near-critical case is sensitive (M_entry 0.155 vs 0.160 flips the state [T Fig 7.10]).
- A sensitivity study for tracking thresholds.
- Measured M_entry resolution: the case sits on a knife edge, so quote the actual M_entry and P0 with uncertainty for every run.

---

## 2B. Quantifying unsteadiness *behind* the shock

The shock is only the start of the problem. For an intake, what ultimately matters is what the unsteady separation does to the flow that goes on to the fan. This section covers four downstream regions, each with its own metrics, and then how to link them to the shock.

| Region | What is unsteady there | Why it matters |
|---|---|---|
| **1. Separation bubble** | Separation point, reattachment point, bubble size ("breathing"), reverse-flow state | Source of most downstream disturbance |
| **2. Separated shear layer** | Vortex roll-up and shedding, shear-layer flapping | Medium/high-frequency content |
| **3. Reattachment and recovering boundary layer** | Fluctuating wall pressure, u′ levels, time-varying shape factor | Determines the boundary layer entering the diffuser and fan |
| **4. Throat / diffuser exit (fan-plane proxy)** | Time-variant total pressure and distortion | Engine compatibility and stability |

### 2B.1 Region 1: separation bubble dynamics

**Quantities to extract as time series** (from shadowgraph segmentation, plus wall-pressure or LDV where available):

- Separation point x_sep(t), reattachment point x_R(t), bubble length L_sep(t) = x_R − x_sep, bubble height and area A_sep(t). For each: mean, σ, PDF, skewness, spectrum. In the 50 kHz shadowgraph (thesis Fig 7.15) the bubble is visible, so this is feasible now. Note that a shadowgraph "bubble" is a density-gradient feature and not a direct measure of reverse flow, so validate against LDV/oil flow [K].
- **Reverse-flow fraction** (the fraction of time the flow near the wall is reversed), at fixed points (LDV) or as a map (PIV). Conditioning velocity fields on reverse-flow fraction is a standard way to define the mean separation and reattachment locations and their ±2σ excursions [S: a University of Washington MSc thesis on a speed-bump separation used exactly this with PIV].
- **Bubble state indicator**: a binary "attached / separated" signal, giving dwell-time distributions, switching rate and the fraction of time separated. This is the downstream counterpart of intermittency γ, and it distinguishes a regular limit cycle (narrow dwell-time distribution) from random switching (broad or exponential).
- **Separation–reattachment coupling**: cross-correlate x_sep(t) and x_R(t). In a swept-SBLI PIV study, separation and reattachment were broadband and correlated only in the low-frequency band, where "breathing" is seen; mid- and high-frequency unsteadiness appeared uncorrelated [S: Vanstone & Clemens, APS DFD 2018 abstract]. Whether your transonic bubble cycle behaves the same way is an open question and a possible result.

**Two characteristic modes in separation bubbles** [S, from turbulent-separation-bubble literature; subsonic and supersonic examples]:

| Mode | Description | Typical St (check the scaling length each paper used) |
|---|---|---|
| **Breathing** | Low-frequency contraction/expansion of the whole bubble and up-and-down motion of the shear layer, with wall-pressure fluctuations felt upstream of detachment and downstream of reattachment | ~0.01–0.05 on L_sep (e.g. ≈0.03 for shock-induced separation; ≈0.05 on L_sep in a pressure-induced speed-bump bubble; ≈0.01 in another large-bubble study) |
| **Shedding** | Roll-up of spanwise vortices in the shear layer and their shedding past reattachment | much higher: ≈0.35 to ≈0.6 in the separation-bubble studies found |

In a large pressure-induced bubble, the first POD mode held roughly 30% of the fluctuating kinetic energy and described breathing, with a bubble length variation of about 90% of its mean [S: JFM 2016, turbulent separation bubble study]. Peak wall-pressure fluctuation sat downstream of mean reattachment, at the same streamwise position as the peak vertical turbulence from convected structures [S, same paper]. Use this as a template for what to look for in your own data: **where is p_rms maximal relative to mean reattachment?**

**Applying this to your case**: the thesis's ~600 Hz cycle involves the bubble forming, being swept downstream, and reforming. That is a large-amplitude event, not small breathing. Test explicitly whether your bubble shows (i) the 600 Hz cycle only, (ii) a lower-frequency breathing as well, or (iii) a shedding-type higher-frequency band. A premultiplied spectrum of A_sep(t) and of downstream pressure answers this directly.

**Model to compare against**: Piponniau et al. propose that low-frequency unsteadiness arises from an imbalance between entrainment of fluid by the shear layer and the recharge of the bubble at reattachment [S, described in a paper citing it]. If your bubble length and shear-layer properties are measurable, this gives a *predicted* frequency scale to compare with data (details in Piponniau et al. 2009; read before using).

### 2B.2 Region 2: separated shear layer

- **Convection velocity U_c** of structures: from the lag of peak cross-correlation between two streamwise locations of the shadowgraph intensity (or of pressure). Typical value is a fraction of the edge velocity [K]; report it measured.
- **Shear-layer thickness growth**: vorticity thickness δ_ω = ΔU / (∂u/∂y)_max from LDV profiles (needs several wall-normal points; you already take profiles) or PIV. Shedding frequency is often scaled as f·δ_ω/U_c and compared with mixing-layer values [S: the separation-bubble paper above did this and found good agreement with mixing-layer vortex frequencies].
- **Turbulence statistics** from LDV where the shear layer is probed: u′/U_e, Reynolds stress −⟨u′v′⟩ (only if both velocity components are measured; check the LDV configuration in thesis Table 5.1), skewness and flatness of u. High near-wall u′ already exists in the thesis (u′/U_e up to ~0.4 near the wall, quoted from earlier work [T §5.4.4]).
- **Space–time (x–t) diagram of the shear layer** along a line following the shear layer from shadowgraph: structures appear as inclined streaks whose slope is U_c.
- **Spatial POD** of velocity (if PIV is available) or of shadowgraph intensity: separates breathing, shedding and convecting-structure modes; see §2.7.

### 2B.3 Region 3: reattachment and the recovering boundary layer

This is probably the most useful region for the "consequence" side of your project, because the thesis already measures the boundary layer at the throat with LDV [T §5.4, §7.2.1].

- **Fluctuating wall pressure p_rms(x)** through and beyond reattachment (new transducers, §2.5). The maximum is expected near or just downstream of mean reattachment [S].
- **Time-resolved boundary-layer integral parameters**: δ*, θ and H_i are normally obtained from mean profiles. For unsteady flow, report them as (a) the usual time-mean values, (b) values **conditioned on bubble state or phase** (e.g. just after bubble shedding vs. during a fully attached period), and (c) their spread. Conditioning is possible if every LDV burst timestamp is recorded and the camera is synchronised (§2B.6).
- **Profile-level unsteadiness**: u′(y)/U_e, skewness S(u), the near-wall reverse-flow fraction at each y, and histograms (your Fig 7.18 already does this at four heights). Plot **how far downstream the reverse-flow fraction and u′ take to relax** back toward an undisturbed profile: a recovery length is a clean downstream metric.
- **Wall shear stress fluctuations** τ_w′ via flush hot-film or Preston-type techniques [K, not verified]. The thesis uses LDV profile fitting for friction velocity [T §5.4.5]. A direct, unsteady τ_w sensor would be new capability and probably out of scope, but it is the most direct instantaneous separation sensor.
- **Mean-flow consequence checks**: downstream mean pressure recovery and total-pressure loss with and without unsteadiness.

### 2B.4 Region 4: throat / diffuser exit as a fan-plane proxy

The rig has no fan, so true fan-face distortion metrics cannot be measured. But the intake-engine compatibility literature gives you the right *language*, and a few of its ideas can be applied to a quasi-2D rig.

**What the intake literature does** [S]:
- Intake researchers stress that **peak events** of unsteady distortion can affect engine stability even when mean distortion is acceptable (Gil-Prieto et al., *Aerosp. Sci. Technol.* 72, 2018). Mean values alone are therefore not sufficient. This applies directly to your project: an intermittent separation may be harmless in the mean but harmful in its peaks.
- Peak distortion data is typically low-pass filtered at a frequency tied to the engine's minimum response time [S, same paper]. **Ask your supervisor or Rolls-Royce contact which frequency band matters.** A ~600 Hz event may be above or below the band that the fan responds to, and that determines whether it is damaging. (The paper reports frequencies of S-duct distortion descriptors inside the range where engine stability could be compromised, but that is for a different intake type.)
- Standard descriptors (SAE ARP1420 style) include radial and circumferential total-pressure distortion indices such as DC(θ) (lowest sector-average total pressure relative to face average, normalised by dynamic head); see the descriptor definitions in the compressor-rig literature [S, DTIC fan-distortion report nomenclature]. These need a circumferential rake and are not directly available in a quasi-2D rig.
- **Extreme Value Theory (EVT)** is used to predict peak distortion beyond the measured record, since testing times two orders of magnitude longer than typical would otherwise be needed (Tanguy et al., 2018; Gil-Prieto et al., 2018) [S]. It is relevant if you want to claim how bad the worst event could be. Results depend on sensitivity choices (de-clustering frequency, number of exceedances, record length), which those papers discuss.
- Joint probability maps of two simultaneous distortion metrics, and POD of the total-pressure field at the duct exit, are used to find the underlying unsteady modes (MacManus et al., *AIAA J.* 55, 2017) [S]. Peak total-pressure and swirl events were found not to be synchronous.

**Practical rig analogues** [K, my suggestions]:
- **Fast-response total-pressure measurement** at the throat or a diffuser station: a small Kiel or pitot probe with a miniature transducer, traversed or in a fixed wall-normal array (e.g. 3–5 heights across the boundary layer).
- **Quasi-2D distortion index** across the wall-normal direction: for example, ΔP = (p0,free-stream − p0,near-wall)/q, as a time series, plus its mean, rms, skewness, spectrum, and its extreme-value tail.
- **Shape factor H(t)** from a near-wall and an outer sensor pair (two-point surrogate for the profile), if the full profile cannot be time-resolved.
- **Unsteady blockage**: the time series of displacement thickness (or its proxy) is effectively an unsteady effective area change at the throat. It is the 2D equivalent of a distortion event.
- Compare **time scales**: the bubble cycle period, the convection time from the bubble to the throat, and the fan blade-passing and response time scales. Even without a fan, writing these down shows whether the disturbance is quasi-steady, resonant or filtered from the fan's viewpoint.

### 2B.5 Whole-field unsteadiness metrics (all regions at once)

- **Time-resolved PIV** (if the lab has it; a 50 kHz PIV system has been used on supersonic SBLI by other groups [S]). Gives u′, v′, Reynolds stresses, reverse-flow maps, vorticity, shear-layer thickness, POD/DMD modes. Seeding a compressible, small-scale rig at kHz rates is demanding; check feasibility.
- **Fluctuation maps from shadowgraph**: pixel SD (done already), skewness/kurtosis, spectral peak amplitude maps at the bubble frequency, and **coherence maps** relative to a reference pixel or reference pressure sensor. These tell you which regions *move together* with the shock.
- **Energy fractions**: share of fluctuation energy captured by each POD mode (e.g. "mode 1 holds X%") gives a compact single-number characterisation of how dominated the unsteadiness is by one coherent motion [S: such a number is reported in the separation-bubble literature].
- **Space-time correlation maps** R(Δx, τ) for estimating convection speeds and length scales.

### 2B.6 Linking downstream behaviour to the shock: coupling metrics

The thesis explicitly wants "the upstream separation response matched to downstream changes in the boundary layer state from LDV" [T §9.3]. Options:

1. **Event-conditioned (phase-averaged) statistics**: detect bubble events in the high-speed video, then average pressure signals and LDV bursts in windows relative to that event time. Because LDV samples arrive at random times, the practical approach is to store every burst's arrival time and the camera trigger, then assign each burst a bubble phase or state afterwards [K]. This requires hardware synchronisation.
2. **Cross-correlation and coherence** between shock/bubble signals (x_s, x_sep, A_sep) and downstream signals (wall pressure at several stations). The sign and size of the time lag tells you whether disturbances propagate downstream with the flow or upstream through the subsonic region, and the peak lag per station gives a propagation speed. In classical SBLI studies, bubble and reflected-shock wall-pressure signals were found in phase opposition at low frequency [S: Debiève & Dupont]. Look for the transonic analogue.
3. **Transfer functions** between a shock-side signal and a downstream signal at the bubble frequency (gain and phase) [K].
4. **Upstream-of-shock monitor**: include one upstream sensor so you can test whether upstream boundary-layer fluctuations precede shock/bubble events, which separates the "upstream" from the "downstream" mechanisms of §4 [S: Clemens & Narayanaswamy].
5. **Pressure-wave propagation**: because the flow behind a transonic shock is subsonic, downstream pressure disturbances can propagate back to the shock [S: Babinsky & Harvey, Ch. 3]. Estimate the acoustic travel time from throat to shock and compare with the period of your oscillation. If the half-period is comparable with that travel time, an acoustic feedback loop is plausible and the downstream geometry (choke, exit aerofoil) becomes part of the mechanism [K, my inference].

### 2B.7 Summary table: downstream metrics

| Metric | Region | Instrument | Possible with existing data? |
|---|---|---|---|
| x_sep(t), x_R(t), L_sep(t), A_sep(t), PDFs and spectra | 1 | Shadowgraph segmentation | Yes (50 kHz video) |
| Attached/separated dwell times, switching rate | 1 | Shadowgraph, near-wall LDV | Yes (video); LDV partly |
| Reverse-flow fraction vs y | 1, 3 | LDV | Yes (raw bursts needed) |
| Breathing vs shedding band energy, St on L_sep | 1, 2 | Spectra of A_sep, wall pressure | Video yes; pressure needs transducers |
| Convection velocity U_c | 2 | Space–time correlation | Yes (video) |
| Vorticity thickness, shear-layer growth | 2 | LDV or PIV profiles | Partly |
| u′/U_e(y), skewness, Reynolds stress | 2, 3 | LDV | Yes (if components available) |
| p_rms(x) through reattachment | 3 | Flush transducers | No |
| State-conditioned δ*, θ, H_i | 3 | LDV + synced video | Needs timestamps and sync |
| Recovery length of u′ and reverse flow | 3 | LDV traverses downstream | Partly |
| Time-variant total pressure, wall-normal distortion index | 4 | Fast total-pressure probe(s) | No |
| EVT-based peak distortion estimate | 4 | Long records of the above | After new data |
| Joint PDFs of two distortion metrics, POD of total-pressure field | 4 | Rake or array | No |
| Time-scale comparison (bubble, convection, acoustic, fan response) | 4 | Calculation | Yes, with the fan-response band from your supervisor |
| Coherence and cross-correlation, shock ↔ downstream | all | Synced video + pressure | Partly |

### 2B.8 Pitfalls specific to downstream measurements

- **LDV limitations** [T §5.4.4, plus K]: velocity bias raises fluctuation estimates (about 4% near wall per the thesis); near-wall measurement is limited by probe-volume size and wall reflections; random sampling forbids direct FFTs; data rate falls in reversed, low-seeding regions, which can bias reverse-flow statistics. Report sample counts and data rates per point.
- **Shadowgraph is line-of-sight integrated and sensitive to density gradients only**: a bubble or shear layer in the subsonic region behind the shock produces weak density gradients, so segmentation may under-detect it. Use thresholds validated against LDV or oil flow.
- **Sidewall separations** exist near the walls [T §6.1], so centreline measurements may not represent the span. Check spanwise uniformity of the unsteady bubble if you can (e.g. with oil flow or a second LDV/pressure position off-centre).
- **Different sensors, different bandwidths**: tubing-coupled tappings ~33 Hz [T §5.2], shadowgraph limited by frame rate and exposure, LDV by data rate, transducers by their own resonance. State the bandwidth of each statistic you report.
- **Quasi-2D caveat**: results are for a quasi-2D rig, so you cannot claim real fan-face distortion. Phrase conclusions as "unsteady blockage / boundary-layer state at the throat".

---

## 3. Practical measurement plan (suggested order)

**Phase 0: re-analyse what exists (no new rig time)**
1. Extract shock-position time series from the baseline (1 kHz) and near-critical (50 kHz) videos. Compute σ_xs, PDFs, x–t diagrams.
2. Segment the bubble in the 50 kHz video; compute a bubble-presence time series and A_sep(t); get the cycle-time distribution. **Re-derive the 600 Hz properly** from the full record: the thesis itself calls it rough, and the number of panels you count as one cycle strongly affects it.
3. POD/DMD on the 50 kHz sequence.
4. Reprocess LDV raw data for backflow probability and histogram metrics.
4b. **Downstream:** extract x_sep(t), x_R(t), A_sep(t) from the 50 kHz video, compute the cycle-time and dwell-time distributions, estimate the shear-layer convection velocity from space-time correlations, and compute time-mean and (if timestamps exist) state-conditioned u′ and reverse-flow fractions at the throat (§2B).

**Phase 1: quantify on the rig**
5. High-speed video at ≥ 10 kHz (preferably 20–50 kHz) across a *sweep* of M_entry (0.150 → 0.165 in fine steps, e.g. 0.0025) and MFS, to map the unsteady region of the parameter space. The thesis says it "may also occur at other M_entry values" and gives only one example [T §7.2.1].
6. Add dynamic pressure transducers, synchronised with the camera. Measure p_rms(x), γ(x), spectra, coherence.
6b. Add a fast-response total-pressure measurement at the throat or a diffuser station, synchronised with the camera and LDV, to quantify the downstream consequence and the shock-to-throat time lag (§2B.4, §2B.6).
7. Reynolds-number test via P0 variation (the thesis lists this as unknown [T §9.3]); keep M_entry fixed.

**Phase 2: control**
8. Repeat the identical measurement set with each control option (§5). Using *the same metrics* before and after is what makes the result defensible.

---

## 4. Physics context from the literature

### 4.1 Classical (supersonic) SBLI low-frequency unsteadiness [S]
- Two families of explanation: **upstream** (large-scale structures in the incoming boundary layer drive the shock) and **downstream** (an intrinsic instability or "breathing" of the separation bubble). Clemens & Narayanaswamy (Annu. Rev. Fluid Mech. 2014) argue both operate, with their relative importance depending on the strength (length scale) of separation; for small, intermittently separated bubbles the correlation with the upstream boundary layer is stronger, and for large bubbles an intrinsic instability dominates [S].
- Low-frequency motions are about two orders of magnitude lower than the frequencies of the upstream boundary-layer turbulence [S]. They cause large fluctuating pressure loads and can excite panel vibration [S].
- Recent global stability and resolvent analysis (e.g. Hao, JFM 2023) treats the low-frequency mode as a coherent global structure [S].

### 4.2 Transonic specifics (more relevant to your case) [S unless noted]
- In transonic SBLIs there is **subsonic flow behind the shock, so downstream conditions feed forward** and affect shock strength, shape and position (Babinsky & Harvey, *Shock Wave–Boundary-Layer Interactions*, Ch. 3). This is the structural reason a feedback loop like the thesis's curvature mechanism is plausible.
- Bruce & Babinsky (JFM 603, 2008) forced a normal shock in a parallel-walled duct; viscosity effects on shock dynamics were small in that study but the authors expected their model to be less applicable where separation is severe. A 43 Hz forcing example was filmed with high-speed schlieren. Follow-ups: Bruce & Babinsky, Aerosp. Sci. Technol. 14 (2010); Bruce, Babinsky, Tartinville & Hirsch, AIAA J. 49 (2011). The same group's "transonic intake at incidence" rig (Coschignano et al.) found that a +2° incidence step made the separation noticeably larger and **unsteadiness appeared**.
- Sartor et al. (JFM 2015) studied transonic SBLI unsteadiness experimentally combined with global stability analysis. This is probably the most directly useful comparison for a limit-cycle-type transonic oscillation. (I only saw the title and reference list, so read the paper before citing details.)
- Transonic airfoil **buffet** (self-sustained shock oscillation with separation) is the closest external-flow analogue: a feedback process involving the shock, the separated region and trailing-edge disturbances [K; Lee (2001) mentioned in a thesis I found]. Typical buffet Strouhal numbers are an order of magnitude higher than the SBLI low-frequency band when based on chord [K, verify].
- Diffuser/duct oscillations: forced-oscillation work (e.g. Doerffer et al.) reports that shock amplitude decreases with increasing forcing frequency, with a small natural oscillation insensitive to forcing at high frequency [S]. Relevant if your downstream flow-path or choke setting acts as a forcing source. Consider whether the rig's downstream configuration (the variable-area choke or the exit aerofoil) could be contributing acoustically. This would need checking, for example by seeing whether the frequency changes with MFS at fixed state.

### 4.3 Suggested way to frame the 600 Hz phenomenon (my interpretation, not from a source)
It looks like a **self-sustained limit cycle driven by shock-strength / curvature feedback**, closer to buffet-type or "intermittent separation" behaviour than to the broadband low-frequency motion of oblique-shock interactions. The practical consequence for your project:
1. Do not blindly compare with St ≈ 0.01–0.05; present St based on several lengths and discuss.
2. A test of the mechanism: does the period scale with the bubble convection time (L_sep/U_c), with the time for the shock to respond, or with something acoustic? Varying Reynolds number and M_entry gives you the scaling data.
3. Check bistability: is the system switching stochastically (broadband, bimodal PDF) or periodically (narrow spectral peak, circular POD phase portrait)? Different statistics, different control strategy.

---

## 5. Control options to limit unsteadiness

Control strategies from the literature and how they might map onto this rig.

### 5.1 Micro vortex generators (MVGs): the thesis's own suggestion
- Passive devices smaller than the boundary layer that generate streamwise vortices, bring high-momentum fluid toward the wall, and make the boundary layer fuller so it can sustain a larger adverse pressure gradient [S].
- Evidence relevant to unsteadiness: in a normal-shock/subsonic-diffuser study at UIUC (Herges, PhD 2014), upstream micro-VGs reduced separation in the subsonic diffuser and lowered shock-position and pressure RMS fluctuations in the diffuser [S]. Flow-control reviews note that reducing separation and shock unsteadiness by stabilising the incoming boundary layer is the aim [S].
- Review/primary references: Panaras & Lu (Prog. Aerosp. Sci. 74, 2015), Lin (Prog. Aerosp. Sci. 38, 2002), Babinsky, Li & Pitt Ford (AIAA J. 47, 2009), Bur, Coponet & Carpels (Shock Waves 19, 2009; transonic channel), Giepman et al. (EUCASS; micro-ramp size and location in an oblique shock reflection) [S].
- Design parameters to study: **height** (published ranges are fractions of δ; one transonic study plans heights of 10–100% of the boundary-layer height [S]), **streamwise position** relative to the shock, **spanwise spacing**, number of devices, shape (micro-ramps give relatively low drag [S]).
- Costs: extra drag and a thicker wake downstream; in some conditions vortex generators can degrade the interaction if misplaced, so run a position sweep and measure the *downstream* boundary-layer state (H_i), not just the separation [K].
- **Rig-specific considerations**: the intake is a 3D-printed part in a quasi-2D tunnel section with sidewall separations [T §4, §5.2, §6.1]. The VG array must stay clear of the sidewall corner flow and span enough of the width that the central region is genuinely 2D. At δ of a few mm, VG heights of order 0.5–1.5 mm are fabrication-challenging (printed ramps vs. adhesive or machined ramps). Check feasibility with the workshop early. Very small VGs may also be destroyed or lifted by shadowgraph-adjacent mounting, so plan attachment.
- Remember the upstream flow here is **curved** and strongly accelerating (the suction peak is in the region of highest streamline curvature [T §5.1]), so published flat-plate optimum heights and spacings may not transfer. Treat them as starting points.

### 5.2 Boundary-layer bleed / suction
- Removing the low-momentum portion of the boundary layer gives a fuller profile and is a well-known solution [S]. The thesis dismisses *eliminating* separation without suction as unlikely and notes suction is expensive and heavy [T §9.3]; it is nevertheless a reasonable **upper-bound reference** for what control can achieve, and the rig design already included a bleed concept in the conceptual stage [T Fig 4.6, §4.3]. Check whether a bleed slot position is available in the current hardware.

### 5.3 Shock control bumps and contour changes [S for existence; K for details]
- 2D adaptive shock-control bumps have been studied for off-design performance (Gramola, Bruce & Santer, J. Fluids Struct. 93, 2020) [S, title only]. These modify the shock structure (smearing it into a lambda system) rather than the boundary layer. On an intake lip the geometry is constrained by the Rolls-Royce lip shape, so this is mainly a "design-space" option, but it fits the thesis's "alternative geometries" suggestion [T §9.3].

### 5.4 Other options worth a short literature check [K, not verified in this session]
- **Passive porous surface with cavity** beneath the shock, which allows pressure equalisation across the interaction and typically smears the shock; frequently studied for transonic airfoils and intakes.
- **Boundary-layer tripping or roughness** upstream, if the upstream boundary layer is not fully turbulent (the thesis's LDV profile fitting and Re of 10⁶ suggest it is turbulent, but check).
- **Active methods** (synthetic jets, plasma actuators, pulsed jets). Probably out of scope for a short project but worth one paragraph in a literature review.

### 5.5 How to judge whether a control "works"

Report the same set for baseline and controlled cases, at the same M_entry, MFS and P0:

| Metric | Desired change |
|---|---|
| Shock-position σ_xs (and shock-absent fraction) | Down |
| Bubble occurrence probability or backflow probability χ | Down |
| Height/prominence of the spectral peak at the bubble frequency (and its St) | Down (or shifted to a harmless frequency) |
| p_rms peak and footprint Δx_foot | Down |
| Time-mean separation extent (oil flow) | Down |
| Downstream δ*, θ, H_i, and unsteadiness there (LDV) | Healthier, more steady |
| Bubble length/area variability σ_Lsep, dwell-time distribution, switching rate | Narrower / fewer switches |
| u′/U_e and reverse-flow fraction at the throat, and recovery length | Down / shorter |
| Time-variant total-pressure fluctuation and peak (extreme-value) distortion at the throat or diffuser exit | Down |
| Peak isentropic Mach and mean pressure recovery | Not significantly degraded |
| Added drag or blockage proxy (e.g. a change in M_entry for the same tunnel setting) | Small |

Note: control that moves the system **away from the critical condition** (e.g. delays separation to a higher M_entry) counts as success, but you should show the unsteady condition has genuinely shifted rather than disappeared because the operating point drifted. Compare across a full M_entry sweep, not a single point.

---

## 6. Questions to take to your supervisor

1. Which length scale and velocity does he want for the Strouhal number (L_sep, δ, D, c)? What is the Reynolds number based on?
2. Is a pressure-transducer insert for the intake already designed or available? Which sensors does the lab own, with what frequency response?
3. Can the camera be run at ≥ 10 kHz at a useful resolution (and what resolution is realistically available at 20–50 kHz)?
4. Is the 50 kHz raw footage still available (and raw LDV burst data)?
5. Which control devices can be manufactured and fitted to the existing intake (3D-printed VGs? bleed slot?), and what tunnel time is available?
6. Is the target the near-critical bubble cycling (case B), the baseline weak unsteadiness (case A), or both? Which M_entry/MFS conditions should be the "test cases"?
7. Does the downstream configuration (choke, exit aerofoil) have any acoustic signature that could couple to the 600 Hz?
8. What time-scale or frequency band is relevant for the fan (engine response time)? That decides whether a ~600 Hz disturbance matters for the engine, and which downstream metrics to prioritise.
9. Is a fast-response total-pressure probe (or rake) available, and can the LDV record burst arrival times for synchronisation with the camera?

---

## 7. References (verify each before citing)

**Thesis**
- L. Dickinson, *An experimental rig to investigate crosswind effects on intake flow behaviour*, PhD thesis, University of Cambridge, 2024. [T]

**SBLI unsteadiness: reviews and mechanisms**
- N. T. Clemens & V. Narayanaswamy, "Low-frequency unsteadiness of shock wave/turbulent boundary layer interactions," *Annu. Rev. Fluid Mech.* 46, 469–492, 2014. [S, via citations]
- J. Hao, "On the low-frequency unsteadiness in shock wave–turbulent boundary layer interactions," *J. Fluid Mech.* 971, A28, 2023. [S]
- S. Piponniau, J. P. Dussauge, J. F. Debiève & P. Dupont, "A simple model for low frequency unsteadiness in shock-induced separation," *J. Fluid Mech.* 629, 87, 2009. [S, via citations]
- Dussauge & Piponniau, Strouhal number range 0.02–0.05 as quoted in the review "Shock wave–boundary layer interactions: review" (*Advances in Aerodynamics*, 2020, doi 10.1186/s42774-020-0028-1). [S]
- M. Bernardini, G. Della Posta, F. Salvadore & E. Martelli, "Unsteadiness characterisation of shock wave/turbulent boundary-layer interaction at moderate Reynolds number," *J. Fluid Mech.*, 2023 (doi 10.1017/jfm.2022.1038). [S]
- H. Babinsky & J. K. Harvey (eds.), *Shock Wave–Boundary-Layer Interactions*, Cambridge University Press, 2011: Ch. 3 (transonic SBLIs) and Ch. 9 (shock-wave unsteadiness). [S, chapter listings]

**Intermittency and measurement methods**
- D. S. Dolling & M. Murphy, "Unsteadiness of the separation shock wave structure in a supersonic compression ramp flowfield," *AIAA J.* 21, 1628–1634, 1983. [S, via citation list; check exact title]
- D. S. Dolling & C. T. Or, "Unsteadiness of the shock wave structure in attached and separated compression ramp flows," *Exp. Fluids* 3, 24–32, 1985. [S]
- D. S. Dolling, "Fluctuating loads in shock wave/turbulent boundary layer interaction: tutorial and update," AIAA Paper 93-0284, 1993. [S, via citation list]
- S. R. Nowlin, *Correlation of incoming boundary layer pitot pressure fluctuations with the unsteadiness of fin-induced shock wave turbulent boundary layer interactions*, MS thesis, UT Austin, 1993 (two-threshold method; shock-foot histories). [S]

**Transonic and intake-specific**
- P. J. K. Bruce & H. Babinsky, "Unsteady shock wave dynamics," *J. Fluid Mech.* 603, 463, 2008. [S]
- P. J. K. Bruce & H. Babinsky, "An experimental study of transonic shock-boundary layer interactions subject to downstream pressure perturbations," *Aerosp. Sci. Technol.* 14, 134–142, 2010. [S, via citations]
- P. J. K. Bruce, H. Babinsky, B. Tartinville & C. Hirsch, "Experimental and numerical study of oscillating transonic shock waves in ducts," *AIAA J.* 49, 1710–1720, 2011. [S, via citations]
- F. Sartor, C. Mettot, R. Bur & D. Sipp, "Unsteadiness in transonic shock-wave/boundary-layer interactions: experimental investigation and global stability analysis," *J. Fluid Mech.*, 2015. [S, title and reference list only; author list from memory]
- A. Coschignano et al., "Normal-shock/boundary-layer interactions in transonic intakes at high incidence," *AIAA J.* (Cambridge repository record). [S]
- A. Coschignano, *Normal shock wave–boundary layer interactions in transonic intakes at incidence*, PhD thesis, Cambridge, 2018. [S]
- P. Doerffer, O. Szulc & F. Magagnato, "Unsteady shock wave–turbulent boundary layer interaction in the Laval nozzle," *TASK Quarterly* 9(1), 115–132, 2005. [S]

**Downstream flow, separation bubbles and intake distortion**
- Mohammed-Taifour & Weiss (authors and volume from memory), "Unsteadiness in a large turbulent separation bubble," *J. Fluid Mech.* (2016), doi 10.1017/jfm.2016.377. Breathing and shedding modes, POD. [S, abstract]
- Weiss et al., turbulent separation bubble breathing and shedding modes, *C. R. Mécanique* (2015), doi 10.1016/j.crme.2015.09.003. [S, excerpts]
- L. Vanstone & N. T. Clemens, "Shock-wave boundary-layer interaction unsteadiness mechanisms: an experimental investigation using 50 kHz PIV," APS DFD 2018 abstract. [S]
- J. F. Debiève & P. Dupont, "Dependence between shock and separation bubble in a shock wave/boundary layer interaction," IUTAM 2007 proceedings. [S]
- H. Annamalai, MSc thesis, University of Washington, 2022 (speed-bump separated flow: reverse-flow conditioning, POD, St ≈ 0.05 and ≈ 0.62). [S]
- D. Gil-Prieto, D. G. MacManus, P. K. Zachos & A. Bautista, "Assessment methods for unsteady flow distortion in aero-engine intakes," *Aerosp. Sci. Technol.* 72, 292–304, 2018. [S]
- G. Tanguy, D. G. MacManus, E. Garnier & P. G. Martin, "Characteristics of unsteady total pressure distortion for a complex aero-engine intake duct," *Aerosp. Sci. Technol.* 78, 297–311, 2018. [S]
- D. G. MacManus, N. Chiereghin, D. Gil Prieto & P. Zachos, "Complex aero-engine intake ducts and dynamic distortion," *AIAA J.* 55(7), 2395–2409, 2017. [S]
- SAE ARP1420 (inlet distortion descriptors; DC(θ) etc.). [K, standard reference; not read this session]

**Flow control**
- A. G. Panaras & F. K. Lu, "Micro-vortex generators for shock wave/boundary layer interactions," *Prog. Aerosp. Sci.* 74, 16–47, 2015. [S, via citations]
- J. C. Lin, "Review of research on low-profile vortex generators to control boundary-layer separation," *Prog. Aerosp. Sci.* 38, 389–420, 2002. [S, via citations]
- H. Babinsky, Y. Li & C. W. Pitt Ford, "Micro-ramp control of supersonic oblique shock-wave/boundary-layer interactions," *AIAA J.* 47, 668–675, 2009. [S, via citations]
- R. Bur, D. Coponet & Y. Carpels, "Separation control by vortex generator devices in a transonic channel flow," *Shock Waves* 19, 521–530, 2009. [S, via citations]
- R. H. M. Giepman, F. F. J. Schrijer & B. W. van Oudheusden, "Flow control of an oblique shock wave reflection with micro-ramp vortex generators: effects of location and size," EUCASS. [S]
- T. Herges, *The effects of micro-vortex generators on normal shock wave/boundary layer interactions*, PhD thesis, UIUC, 2014. [S]
- G. Della Posta, E. Martelli, F. Salvadore & M. Bernardini, "High-fidelity simulations of microramp-controlled shock wave/boundary layer interaction," arXiv:2402.18971, 2024. [S]
- M. Gramola, P. J. K. Bruce & M. Santer, "Off-design performance of 2D adaptive shock control bumps," *J. Fluids Struct.* 93, 102856, 2020. [S, citation only]

---

## Appendix: your original notes, with comments

Your original `.txt` is reproduced here in condensed form. Comments in *italics* flag what changes for your rig.

**Spatial and displacement metrics**
- Shock-position standard deviation σ_xs. *Needs a tracking rule on shadowgraph (§2.2). Report it alongside the PDF, because a single σ hides bimodality.*
- Intermittency factor γ (0 upstream, 1 downstream). *Proper definition needs wall pressure; video is a proxy (§2.3).*
- Shock-foot footprint Δx_foot (0.05 < γ < 0.95). *Threshold values are a convention.*

**Statistical pressure metrics**
- Wall pressure RMS peak. *Your tappings cannot measure it, since they are quasi-steady with ~33 Hz cut-off [T §5.2]. This is the main new hardware requirement.*
- Skewness and kurtosis. *Also compute them for pixel-intensity time series and for shock-position series.*

**Frequency and spectral metrics**
- PSD, Strouhal number, coherence. *The 0.01–0.05 range is for the classical low-frequency band, scaled with separation length. Your ~600 Hz bubble cycle may be a different mechanism (§4.3). Report St on more than one length scale.*

**Not in the original notes: downstream flow**
- Your list focuses on the shock. Section 2B adds metrics for the separation bubble, shear layer, recovering boundary layer and throat/diffuser exit, and for coupling them to the shock.

**Advanced methods**
- POD, DMD. *Feasible immediately on the existing 50 kHz shadowgraph video (§2.7).*