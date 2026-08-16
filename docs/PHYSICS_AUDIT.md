# Physics Audit: Radiative Energy Harvesting

## Purpose

This audit establishes the physical boundaries that the Radiocity model must respect before optimization or engineering claims are made.

## 1. Radiation is not a universal extractable energy reservoir

A receiver can absorb electromagnetic radiation only when there is a net radiative energy flux into it. For thermal radiation, the net exchange depends on the source and receiver states, spectra, view factors, and optical properties. A blackbody is an ideal absorber/emitter, not an unlimited energy source.

## 2. Blackbody emission

For an ideal blackbody, total hemispherical emitted power is

\[
P/A = \sigma T^4,
\]

where \(\sigma\) is the Stefan–Boltzmann constant. For two radiative surfaces, a useful first-order net-exchange expression is proportional to

\[
q_{net} = \sigma F_{12}(T_1^4-T_2^4),
\]

before spectral, angular, and material corrections.

Therefore, harvesting from a warm object cannot continuously produce more energy than the available net radiative flux without another energy source or a change in the thermodynamic boundary conditions.

## 3. Spectral selectivity

A practical receiver should be modeled spectrally rather than as a generic radiation trap. Absorption, emission, reflection, transmission, and conversion efficiency depend on wavelength and angle. Kirchhoff's law links absorptivity and emissivity at thermal equilibrium for a given mode, so a perfect absorber is also an efficient emitter in that mode.

## 4. Conversion limits

Thermophotovoltaic systems demonstrate that thermal radiation can be converted to electricity. However, conversion is not lossless. Below-bandgap photons are not efficiently converted by a PV absorber, while excess photon energy can be lost through thermalization. Thermodynamic limits therefore remain essential.

## 5. Near-field opportunity

Near-field radiative transfer is a legitimate route for increasing radiative heat flux between closely spaced surfaces. Evanescent modes can produce heat transfer above the conventional far-field blackbody flux under suitable nanoscale conditions. This does **not** mean that energy is created: the additional transferred energy originates from the hot source and requires a temperature/chemical potential gradient.

## 6. Consequence for the Radiocity hypothesis

The strongest physically defensible research direction is not a device that "traps all radiation" or creates more energy than its sources provide. It is an **adaptive multispectral radiative-energy harvesting architecture** that:

1. senses incoming spectral/thermal conditions;
2. dynamically selects or modulates compatible absorption/conversion channels;
3. manages receiver temperature and storage;
4. recovers useful energy from otherwise wasted radiative/thermal flux;
5. optionally exploits near-field coupling where the geometry permits it.

The research question becomes whether adaptive spectral and thermal management can improve **net usable electrical energy, exergy utilization, power density, or lifetime** relative to a fixed architecture under realistic constraints.

## 7. Model requirements before publication

The current repository model contains simplified efficiency and temperature relationships. These are placeholders and must not be presented as experimentally validated material/device laws.

The next model revision should use:

- Planck spectral radiance;
- wavelength-dependent emissivity/absorptivity;
- view factors/geometric coupling;
- radiative, conductive, and convective heat transfer;
- temperature-dependent material/device efficiency;
- realistic electrical storage and conversion losses;
- explicit energy and entropy/exergy accounting;
- measured or literature-derived parameters.

## Key references

- Fan, S., & Li, W. (2022). Photonics and thermodynamics concepts in radiative cooling. *Nature Photonics, 16*, 182–190.
- Li, W., Buddhiraju, S., & Fan, S. (2020). Thermodynamic limits for simultaneous energy harvesting from the hot sun and cold outer space. *Light: Science & Applications, 9*, 68.
- Mittapally, R., et al. (2021). Near-field thermophotovoltaics for efficient heat to electricity conversion at high power density. *Nature Communications, 12*, 4364.
- Fiorino, A., et al. (2018). Nanogap near-field thermophotovoltaics. *Nature Nanotechnology, 13*, 806–811.
- Fan, D., et al. (2020). Near-perfect photon utilization in an air-bridge thermophotovoltaic cell. *Nature, 586*, 237–241.

These references are starting points for the formal literature review; the paper should later use the agreed APA style consistently.
