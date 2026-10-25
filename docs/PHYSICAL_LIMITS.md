# Physical Limits and Open Frontiers

What invisible energy can and cannot do, so Radiocity aims at everything that is possible and nothing that is not.

## Laws no design can break

| Law | What it means for Radiocity |
|---|---|
| **Conservation of energy** | A receiver collects at most *(arriving power per m²) × (area) × (efficiency)*. No coating, material or algorithm creates energy. |
| **Second law of thermodynamics** | Heat radiation is only useful across a temperature difference. An object at the same temperature as its surroundings receives no net energy from them. Heat-to-electricity is bounded by the Carnot efficiency 1 − T_cold/T_hot. |
| **Inverse-square law** | Power from a transmitter spreads over 4πd². Ambient radio power far from transmitters is therefore tiny, and beamed power falls fast with distance unless the beam is focused (antenna gain, lasers). |
| **Antenna aperture** | An antenna captures power over an effective area A_e = Gλ²/4π - small at high frequencies (≈20 cm² for a 2.45 GHz dipole). |
| **Detailed balance (Shockley–Queisser)** | Photovoltaic conversion is bounded: ≈33% for one junction under sunlight, ≈47% achieved with multi-junction cells in the lab. |

Everything else - materials, cost, manufacturing, regulation, infrastructure - is engineering, and engineering can be beaten.

## Ceilings per energy source (orders of magnitude)

| Source | Power arriving | Realistic electrical output | Fits |
|---|---|---|---|
| Sunlight | ≈1000 W/m² peak; 4.2-5.8 kWh/m²/day in Nigerian cities (NASA POWER 2024) | ≈150-200 W/m² peak, ≈0.8-1.0 kWh/m²/day | sensors to vehicles (partly) |
| Ambient radio (urban, away from transmitters) | ≈10⁻⁵-10⁻³ W/m² | nanowatts to microwatts per antenna; rectifiers lose most of it at low power | only ultra-low-power tags, or near transmitters |
| Waste heat (furnace 1500 K) | ≈290 kW/m² blackbody | tens of kW/m² with thermophotovoltaics (≈38% of absorbed heat in Radiocity's model; 40% measured at ≈2400 K by LaPotin et al., 2022) | industrial machinery |
| Body heat / ambient heat | net flux only across small temperature differences | microwatts to milliwatts | wearables |
| Beamed: inductive pads / electrified lanes | as designed (kW-tens of kW) | ≈85-95% link efficiency at close range | robots, cars |
| Beamed: microwave | as transmitted, falls with d² | limited by beam size and human-exposure limits (ICNIRP: 10 W/m² public, 2-300 GHz) | devices at metres; drones/space with large apertures |
| Beamed: laser | as transmitted | ≈50% laser-to-electric photovoltaics; needs line of sight and safety interlocks | drones, remote equipment |

## What this means for the vision

- **Small devices** (sensors, tags): ambient energy is already enough - fully autonomous today.
- **Phones and wearables**: ambient solar gives ≈12-16% in Radiocity's simulations; short-range beamed power gives the rest.
- **Cars**: a 5 m² solar skin gives ≈20-27 km/day in Nigerian cities - about 40-50% of a 40 km commute. Ambient radio adds essentially nothing (milliwatt-hours per year). Electrified lanes or wireless pads close the gap.
- **Indoor machines**: almost no sunlight indoors; beamed power or waste heat is required.
- **Hot-process machinery**: waste heat can fully power co-located equipment.

## Open frontiers - research targets, not boundaries

Physics allows all of these; they are where Radiocity can push:

1. **Near-field thermophotovoltaics** - nanometre gaps exceed far-field blackbody transfer, raising power density (Fiorino et al., 2018; Mittapally et al., 2021). The extra energy still comes from the hot source.
2. **Air-bridge and high-reflectance TPV cells** - near-perfect reuse of sub-bandgap photons (Fan et al., 2020); in Radiocity's model this sets the efficiency ceiling.
3. **Sky-cooling energy harvesting** - the cold night sky (outer space ≈3 K) is a usable heat sink; energy can be harvested at night from the temperature difference (Li, Buddhiraju & Fan, 2020).
4. **Solar coatings and paints** - perovskite and organic photovoltaics that can be printed onto curved bodies.
5. **Rectifiers for microwatt-level radio** - pushing efficiency up at -30 to -20 dBm makes ambient RF useful for more devices.
6. **Smart infrastructure** - electrified lanes, building-wide wireless power, focused beams with safety interlocks.
7. **Intelligent power management** - forecasting, scheduling and multi-source coordination; Radiocity's core contribution.

## Things that are not possible, however framed

- Running a device indefinitely on radiation from surroundings at its own temperature.
- Extracting more energy from a beam or field than its transmitter emits.
- Harvesting meaningful power from ambient radio far from transmitters for anything above microwatts per antenna.

## Key references

See [REFERENCES.md](REFERENCES.md).
