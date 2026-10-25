"""Harvesters: one model per kind of invisible energy.

Every harvester converts the conditions of one timestep into electrical
power (W) using the physics that governs that energy form:

- SolarPV            sunlight (temperature-corrected photovoltaics)
- Rectenna           ambient radio waves (antenna aperture, low-power rectifier losses)
- Thermophotovoltaic heat radiation from a hot source (detailed-balance photon counting)
- Thermoelectric     heat flowing across a temperature difference (Carnot-bounded)
- InductiveLink      near-field magnetic wireless charging (coil coupling)
- RFBeam             far-field microwave power beaming (Friis + rectenna)
- LaserBeam          optical power beaming (laser-tuned photovoltaics)

Conditions are passed as a mapping, e.g. ``{"ghi_w_m2": 650,
"air_temperature_c": 31, "rf_power_density_w_m2": 1e-4, "inductive_available": 1}``.
Each harvester reads only the keys it needs; a missing key means the
energy form is absent at that moment.

Each harvester has a ``kind``: ``ambient`` (energy already around us -
sunlight, radio), ``heat`` (waste heat from machines and processes) or
``beamed`` (energy deliberately sent to the device).

Conservation of energy is enforced structurally: every model multiplies an
incident power by efficiencies in [0, 1], and the thermal models are
additionally bounded by the Carnot or detailed-balance limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp, log10, pi, sqrt
from typing import Mapping

import numpy as np

from radiocity.planck_model import BOLTZMANN_CONSTANT, LIGHT_SPEED, PLANCK_CONSTANT

Conditions = Mapping[str, float]

ELECTRON_VOLT = 1.602176634e-19

# ICNIRP (2020) general-public reference level for 2-300 GHz, averaged.
ICNIRP_PUBLIC_POWER_DENSITY_W_M2 = 10.0


def _fraction(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


def _positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


class Harvester:
    """Common interface."""

    name: str
    kind: str

    def power_w(self, conditions: Conditions) -> float:  # pragma: no cover - interface
        raise NotImplementedError


# --------------------------------------------------------------------- solar


@dataclass(frozen=True)
class SolarPV(Harvester):
    """Photovoltaic surface (panel, roof, coating).

    P = G * A * f_orient * eta_stc * [1 + gamma (T_cell - 25)] * eta_system

    Cell temperature uses the NOCT model:
    T_cell = T_air + (NOCT - 20) / 800 * G.
    """

    name: str
    area_m2: float
    efficiency_stc: float = 0.22
    temperature_coefficient_per_k: float = -0.004
    noct_c: float = 45.0
    orientation_factor: float = 1.0
    system_efficiency: float = 0.92
    kind: str = "ambient"

    def __post_init__(self) -> None:
        if self.area_m2 < 0:
            raise ValueError("area_m2 must be non-negative")
        for value, label in [
            (self.efficiency_stc, "efficiency_stc"),
            (self.orientation_factor, "orientation_factor"),
            (self.system_efficiency, "system_efficiency"),
        ]:
            _fraction(value, label)

    def cell_temperature_c(self, irradiance_w_m2: float, air_temperature_c: float) -> float:
        return air_temperature_c + (self.noct_c - 20.0) / 800.0 * irradiance_w_m2

    def power_w(self, conditions: Conditions) -> float:
        irradiance = max(0.0, conditions.get("ghi_w_m2", 0.0)) * self.orientation_factor
        if irradiance == 0.0:
            return 0.0
        cell_c = self.cell_temperature_c(irradiance, conditions.get("air_temperature_c", 25.0))
        derate = max(0.0, 1.0 + self.temperature_coefficient_per_k * (cell_c - 25.0))
        efficiency = min(self.efficiency_stc * derate, self.efficiency_stc)
        return irradiance * self.area_m2 * efficiency * self.system_efficiency


# ------------------------------------------------------------------------ RF


def rectifier_efficiency(input_power_w: float, peak_efficiency: float = 0.70,
                         half_efficiency_dbm: float = -12.0, slope_db: float = 5.0) -> float:
    """RF-to-DC efficiency as a function of input power.

    Diode rectifiers need a minimum voltage swing, so efficiency collapses at
    low input power (roughly <5% below -30 dBm, ~50-70% near 0 dBm). Modelled
    as a logistic curve in dBm; parameters are adjustable and should be
    calibrated to a specific rectifier.
    """

    if input_power_w <= 0:
        return 0.0
    dbm = 10.0 * log10(input_power_w / 1e-3)
    return peak_efficiency / (1.0 + exp(-(dbm - half_efficiency_dbm) / slope_db))


def antenna_effective_area_m2(frequency_hz: float, gain_linear: float) -> float:
    """Effective aperture of an antenna: A_e = G * lambda^2 / (4 pi)."""

    _positive(frequency_hz, "frequency_hz")
    wavelength = LIGHT_SPEED / frequency_hz
    return gain_linear * wavelength**2 / (4.0 * pi)


@dataclass(frozen=True)
class Rectenna(Harvester):
    """Ambient radio-wave harvester (antenna + rectifier).

    The captured power is incident power density times effective area; an
    array of ``elements`` antennas adds area, but each element rectifies its
    own small power, so the low-power efficiency penalty applies per element.
    """

    name: str
    frequency_hz: float = 2.45e9
    gain_linear: float = 1.64
    elements: int = 1
    density_key: str = "rf_power_density_w_m2"
    kind: str = "ambient"

    def power_w(self, conditions: Conditions) -> float:
        density = max(0.0, conditions.get(self.density_key, 0.0))
        per_element = density * antenna_effective_area_m2(self.frequency_hz, self.gain_linear)
        return self.elements * per_element * rectifier_efficiency(per_element)


# ------------------------------------------------------------------- thermal


@lru_cache(maxsize=4096)
def _above_gap_photon_power(temperature_k: float, bandgap_ev: float, samples: int = 400) -> float:
    """Number of above-bandgap photons emitted per m^2 per second, times E_g (W/m^2).

    Integrates the blackbody photon flux over photon energy from E_g upwards
    (hemispherical, unit emissivity).
    """

    e_gap = bandgap_ev * ELECTRON_VOLT
    kt = BOLTZMANN_CONSTANT * temperature_k
    upper = e_gap + 40.0 * kt
    energies = np.linspace(e_gap, upper, samples)
    exponent = np.minimum(energies / kt, 700.0)
    photon_flux = (
        2.0 * pi / (PLANCK_CONSTANT**3 * LIGHT_SPEED**2) * energies**2 / np.expm1(exponent)
    )
    count = float(np.sum(0.5 * (photon_flux[1:] + photon_flux[:-1]) * np.diff(energies)))
    return count * e_gap


@lru_cache(maxsize=4096)
def _band_power(temperature_k: float, low_ev: float, high_ev: float, samples: int = 400) -> float:
    """Blackbody hemispherical power (W/m^2) emitted between two photon energies."""

    kt = BOLTZMANN_CONSTANT * temperature_k
    energies = np.linspace(max(low_ev, 1e-4) * ELECTRON_VOLT, high_ev * ELECTRON_VOLT, samples)
    exponent = np.minimum(energies / kt, 700.0)
    spectral = 2.0 * pi / (PLANCK_CONSTANT**3 * LIGHT_SPEED**2) * energies**3 / np.expm1(exponent)
    return float(np.sum(0.5 * (spectral[1:] + spectral[:-1]) * np.diff(energies)))


@dataclass(frozen=True)
class Thermophotovoltaic(Harvester):
    """Photovoltaic cell facing a hot source (furnace, engine, exhaust, kiln).

    Detailed-balance style model: every above-bandgap photon net-exchanged
    between source and cell delivers at most E_g of energy; a voltage/fill
    factor (``practical_factor``) accounts for the gap between that ultimate
    limit and real cells.

    P_el = A * F * eta_practical * [N_above(T_source) - N_above(T_cell)] * E_g

    Heat absorbed = above-gap photon energy + (1 - R_sub) * sub-gap energy,
    where R_sub is the reflectance of the cell's back mirror for sub-bandgap
    light (sent back to the source, not wasted). Efficiency = P_el / heat.

    The bandgap trade-off is physical: a small bandgap gives more power per
    m^2 but wastes more energy per photon; a large bandgap converts each
    photon better but lets more photons pass unconverted. With imperfect
    sub-gap reflection the efficiency peaks at a bandgap that moves with
    source temperature.
    """

    name: str
    area_m2: float
    bandgap_ev: float = 0.74
    view_factor: float = 0.8
    practical_factor: float = 0.55
    subgap_reflectance: float = 0.95
    cell_temperature_k: float = 300.0
    source_key: str = "heat_source_temperature_k"
    kind: str = "heat"

    def __post_init__(self) -> None:
        _positive(self.bandgap_ev, "bandgap_ev")
        _fraction(self.view_factor, "view_factor")
        _fraction(self.practical_factor, "practical_factor")
        _fraction(self.subgap_reflectance, "subgap_reflectance")

    def _net(self, source_k: float) -> tuple[float, float, float]:
        """(electric, above-gap heat, sub-gap heat) per m^2 at unit view factor."""

        top = 40.0 * BOLTZMANN_CONSTANT * source_k / ELECTRON_VOLT + self.bandgap_ev
        electric = _above_gap_photon_power(source_k, self.bandgap_ev) - _above_gap_photon_power(
            self.cell_temperature_k, self.bandgap_ev
        )
        above = _band_power(source_k, self.bandgap_ev, top) - _band_power(
            self.cell_temperature_k, self.bandgap_ev, top
        )
        below = _band_power(source_k, 1e-4, self.bandgap_ev) - _band_power(
            self.cell_temperature_k, 1e-4, self.bandgap_ev
        )
        return max(0.0, electric) * self.practical_factor, max(0.0, above), max(0.0, below)

    def efficiency(self, source_temperature_k: float) -> float:
        """Electric output / heat absorbed from the source."""

        if source_temperature_k <= self.cell_temperature_k:
            return 0.0
        electric, above, below = self._net(source_temperature_k)
        heat = above + (1.0 - self.subgap_reflectance) * below
        return electric / heat if heat > 0 else 0.0

    def power_w(self, conditions: Conditions) -> float:
        source_k = conditions.get(self.source_key, 0.0)
        if source_k <= self.cell_temperature_k:
            return 0.0
        electric, _, _ = self._net(source_k)
        return electric * self.area_m2 * self.view_factor


@dataclass(frozen=True)
class Thermoelectric(Harvester):
    """Thermoelectric generator across a temperature difference.

    eta = eta_Carnot * (sqrt(1 + ZT) - 1) / (sqrt(1 + ZT) + T_c / T_h)
    P = eta * K * (T_h - T_c), with K the thermal conductance (W/K).
    """

    name: str
    thermal_conductance_w_k: float
    zt: float = 1.0
    hot_key: str = "heat_source_temperature_k"
    cold_key: str = "air_temperature_c"
    kind: str = "heat"

    def power_w(self, conditions: Conditions) -> float:
        hot = conditions.get(self.hot_key, 0.0)
        cold = conditions.get(self.cold_key, 25.0) + 273.15
        if hot <= cold:
            return 0.0
        carnot = 1.0 - cold / hot
        root = sqrt(1.0 + self.zt)
        efficiency = carnot * (root - 1.0) / (root + cold / hot)
        return efficiency * self.thermal_conductance_w_k * (hot - cold)


# ------------------------------------------------------------------- beamed


def inductive_link_efficiency(coupling_k: float, q_transmitter: float, q_receiver: float) -> float:
    """Maximum efficiency of a resonant inductive link.

    With figure of merit U = k * sqrt(Q1 Q2):
    eta_max = U^2 / (1 + sqrt(1 + U^2))^2
    """

    _fraction(coupling_k, "coupling_k")
    u_squared = coupling_k**2 * q_transmitter * q_receiver
    return u_squared / (1.0 + sqrt(1.0 + u_squared)) ** 2


@dataclass(frozen=True)
class InductiveLink(Harvester):
    """Wireless charging pad or electrified road lane (near-field).

    Delivers transmitter power x link efficiency x power-electronics efficiency
    while the device is over a transmitter (``availability_key`` = share of
    the timestep spent over one, 0..1).
    """

    name: str
    transmitter_power_w: float
    coupling_k: float = 0.2
    q_transmitter: float = 300.0
    q_receiver: float = 300.0
    electronics_efficiency: float = 0.92
    availability_key: str = "inductive_available"
    kind: str = "beamed"

    def power_w(self, conditions: Conditions) -> float:
        share = min(1.0, max(0.0, conditions.get(self.availability_key, 0.0)))
        link = inductive_link_efficiency(self.coupling_k, self.q_transmitter, self.q_receiver)
        return share * self.transmitter_power_w * link * self.electronics_efficiency


@dataclass(frozen=True)
class RFBeam(Harvester):
    """Far-field microwave power beaming to a receiving antenna (Friis equation).

    P_r = P_t * G_t * G_r * (lambda / (4 pi d))^2, capped at P_t, then rectified.
    ``exposure_ok`` reports whether the power density at the receiver is
    within the ICNIRP general-public reference level.
    """

    name: str
    transmitter_power_w: float
    distance_m: float
    frequency_hz: float = 5.8e9
    gain_transmitter: float = 100.0
    gain_receiver: float = 100.0
    availability_key: str = "rf_beam_available"
    kind: str = "beamed"

    def received_power_w(self) -> float:
        _positive(self.distance_m, "distance_m")
        wavelength = LIGHT_SPEED / self.frequency_hz
        friis = self.gain_transmitter * self.gain_receiver * (wavelength / (4 * pi * self.distance_m)) ** 2
        return self.transmitter_power_w * min(1.0, friis)

    def power_density_w_m2(self) -> float:
        return self.transmitter_power_w * self.gain_transmitter / (4 * pi * self.distance_m**2)

    @property
    def exposure_ok(self) -> bool:
        return self.power_density_w_m2() <= ICNIRP_PUBLIC_POWER_DENSITY_W_M2

    def power_w(self, conditions: Conditions) -> float:
        share = min(1.0, max(0.0, conditions.get(self.availability_key, 0.0)))
        received = self.received_power_w()
        return share * received * rectifier_efficiency(received)


@dataclass(frozen=True)
class LaserBeam(Harvester):
    """Optical power beaming to a laser-tuned photovoltaic receiver."""

    name: str
    beam_power_w: float
    link_transmission: float = 0.8
    receiver_efficiency: float = 0.5
    availability_key: str = "laser_available"
    kind: str = "beamed"

    def power_w(self, conditions: Conditions) -> float:
        share = min(1.0, max(0.0, conditions.get(self.availability_key, 0.0)))
        return share * self.beam_power_w * self.link_transmission * self.receiver_efficiency
