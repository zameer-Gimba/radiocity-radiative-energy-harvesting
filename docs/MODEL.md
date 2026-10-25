# Model Specification

Equations, assumptions and parameter sources for every part of the Radiocity engine. Code references are to `src/radiocity/`.

## 1. Conditions (`scenarios.py`)

Hourly inputs for one year:

| Input | Source |
|---|---|
| Global horizontal irradiance G, clear-sky irradiance, air temperature | NASA POWER hourly data, 2024 (simulation) and 2019-2023 (forecast training), local solar time |
| Ambient RF power density S | Environment assumption: rural 2×10⁻⁵, urban 10⁻⁴, near a base station 10⁻² W/m² (order of magnitude from urban surveys, e.g. Piñuela et al., 2013) |
| Beamed-power availability | Share of each hour spent over a pad/lane or inside a beam (device schedule) |
| Heat-source temperatures | Device schedule (e.g. furnace 1500 K, 06:00-22:00) |

## 2. Harvesters (`harvesters.py`)

**Solar PV.** P = G · A · f · η_opt · η_STC · [1 + γ(T_cell − 25 °C)] · η_sys, with T_cell = T_air + (NOCT − 20)/800 · G (NOCT model; Duffie & Beckman, 2013). Defaults: η_STC = 22%, γ = −0.4 %/K, NOCT = 45 °C, η_opt = 97% (reflection at low sun angles), η_sys = 92% (MPPT, wiring). Validated against PVGIS: see `results/VALIDATION.md`. f is an exposure/orientation factor (e.g. 0.85 for a car body, 0.15 for a phone mostly in a pocket).

**Rectenna (ambient RF).** Captured P_in = S · A_e per element with A_e = Gλ²/4π. Rectifier efficiency η(P_in) = η_max / (1 + exp(−(P_dBm − P½)/s)), η_max = 70%, P½ = −12 dBm, s = 5 dB: an adjustable logistic fit to the documented collapse of diode efficiency at low input power (Valenta & Durgin, 2014). Arrays rectify per element.

**Thermophotovoltaic.** Detailed-balance photon counting: P_el = A · F · ε_p · E_g · [N(T_s) − N(T_c)], with N(T) the hemispherical blackbody photon flux above the bandgap E_g and ε_p = 0.55 a voltage/fill factor. Heat absorbed = above-gap power + (1 − R_sub) · sub-gap power, with sub-gap mirror reflectance R_sub = 0.95. Efficiency = P_el / heat. The optimal bandgap rises linearly with source temperature (≈0.38 eV per 1000 K in this model).

**Thermoelectric.** η = η_C (√(1+ZT) − 1)/(√(1+ZT) + T_c/T_h), P = η · K · ΔT (Snyder & Toberer, 2008). Default ZT = 1.

**Inductive link.** η_link = U²/(1 + √(1+U²))², U = k√(Q₁Q₂) (maximum efficiency of a resonant two-coil link; cf. Kurs et al., 2007), times power-electronics efficiency.

**RF beam.** Friis: P_r = P_t G_t G_r (λ/4πd)², capped at P_t, rectified with η(P_r). Exposure check: power density P_t G_t / 4πd² ≤ 10 W/m² (ICNIRP, 2020, general public, 2-300 GHz).

**Laser beam.** P = P_beam · T_link · η_receiver (defaults 0.8, 0.5).

## 3. Storage and regulation (`storage.py`)

State of charge kept within [SoC_min, SoC_max]; acceptance tapers linearly to zero between SoC_taper and SoC_max (constant-voltage phase); charge/discharge efficiencies; power limits (C-rate); self-discharge per day; equivalent full cycles. Presets: lithium-ion (96%/96%, 10-90% window, 0.1%/day) and supercapacitor (98%/98%, 10%/day).

Bookkeeping per hour: offered = stored-from-offer + refused (curtailed); stored energy changes by charge·η_c − discharge/η_d − self-discharge.

## 4. Loads (`loads.py`)

Hourly profiles with a priority: **critical** (must run), **normal** (may be shed to protect critical loads), **deferrable** (a daily energy amount that may move within the day).

## 5. Energy manager (`simulation.py`)

Each hour: harvest → serve loads from harvest (critical, normal, deferrable) → store surplus (regulator refuses when full → curtailed) → serve remaining demand from storage (critical down to SoC_min; others down to the reserve).

| Policy | Reserve for non-critical loads | Deferrable loads |
|---|---|---|
| basic | SoC_min | run on schedule |
| reserve | fixed (default 40%) | run on schedule |
| smart | SoC_min + max(0, critical need₂₄ₕ − 0.8 · expected harvest₂₄ₕ) / capacity | run in surplus hours; remainder forced at 23:00 |

Expected harvest₂₄ₕ = last 24 h harvest × (tomorrow's reference irradiance / today's), where the reference is clear-sky irradiance or the LightGBM day-ahead forecast. Forecasts never use the actual future weather.

Simulations run the year twice and report the second pass (steady-state storage).

**Metrics:** energy autonomy (delivered / demanded energy), critical availability (share of critical-demand hours fully met), fully autonomous days, external energy still needed, curtailed share of harvest, storage cycles. Energy conservation is tested hour by hour.

## 6. Forecasting (`forecast.py`)

LightGBM (native API, L1 objective, 300 rounds) predicts hourly irradiance for the next day from clear-sky irradiance, hour and day-of-year encodings, yesterday's same-hour irradiance and the clearness indices of the last two days. Trained on 2019-2023, tested on unseen 2024 against persistence and clear-sky persistence.

## 7. Design optimisation (`design.py`)

Particle swarm optimisation (Kennedy & Eberhart, 1995) over design variables, each candidate judged by a full-year simulation: minimum-cost PV area and storage for a target critical availability (infeasible designs penalised by their shortfall); efficiency-maximising TPV bandgap, checked against a 0.01 eV grid.

## 8. Known simplifications (research targets)

- Irradiance is horizontal (GHI) times an exposure factor; no transposition to tilted or moving surfaces, no shading model.
- Ambient RF is a constant density per environment; no spatial or temporal variation.
- TPV uses a constant voltage/fill factor and ideal blackbody source; no near-field enhancement, cell heating or parasitic conduction.
- Storage has no temperature dependence or capacity fade.
- Beamed-power availability is a schedule, not a traffic or alignment model.
- Hourly time step; sub-hour peaks are averaged.
