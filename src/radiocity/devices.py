"""Device catalogue: from a sensor to a car to a factory machine.

Each builder returns a Device and the hour-of-day schedules its energy
sources need. ``beamed=True`` adds the wireless-power infrastructure that
fits the device (charging pad, electrified lane, RF beam).

Figures are typical published or datasheet values, chosen as reasonable
defaults - every one can be overridden:

- EV consumption ~0.16 kWh/km (efficient compact EVs); 5 m^2 of body solar
  (as on the Lightyear 0 solar car)
- smartphone ~10 Wh/day of use, 15 Wh battery
- outdoor IoT sensor ~0.2 mW sensing plus daily radio uplink
- warehouse robot (AGV) ~400 W while driving, opportunity charging on pads
- factory machine beside a 1500 K furnace, recovering heat with TPV
"""

from __future__ import annotations

from typing import Callable

from radiocity.harvesters import (
    InductiveLink,
    RFBeam,
    Rectenna,
    SolarPV,
    Thermoelectric,
    Thermophotovoltaic,
)
from radiocity.loads import Load, constant, hours
from radiocity.scenarios import HourlySchedule, during
from radiocity.simulation import Device
from radiocity.storage import lithium_ion

Builder = Callable[..., tuple[Device, dict[str, HourlySchedule]]]


def iot_sensor(beamed: bool = False) -> tuple[Device, dict[str, HourlySchedule]]:
    harvesters = [
        SolarPV("solar_cell", area_m2=0.0025, efficiency_stc=0.18, orientation_factor=0.8),
        Rectenna("ambient_rf", frequency_hz=2.45e9, elements=4),
    ]
    schedules: dict[str, HourlySchedule] = {}
    if beamed:
        harvesters.append(RFBeam("rf_beam", transmitter_power_w=3.0, distance_m=5.0,
                                 frequency_hz=915e6, gain_transmitter=6.0, gain_receiver=1.64))
        schedules["rf_beam_available"] = during(range(24), 1.0)

    device = Device(
        name="iot_sensor",
        description="Outdoor environmental sensor with daily radio uplink",
        harvesters=harvesters,
        storage_factory=lambda: lithium_ion("lipo_0.5wh", 0.5),
        loads=[
            Load("sensing", "critical", constant(0.0002)),
            Load("data_uplink", "deferrable", hours(0.02, [12]), max_power_w=0.05),
        ],
    )
    return device, schedules


def smartphone(beamed: bool = False) -> tuple[Device, dict[str, HourlySchedule]]:
    harvesters = [
        # Back-of-phone solar; mostly in a pocket or indoors, so a low exposure factor.
        SolarPV("back_solar", area_m2=0.01, efficiency_stc=0.22, orientation_factor=0.15),
        Rectenna("ambient_rf", frequency_hz=2.45e9, elements=1),
    ]
    schedules: dict[str, HourlySchedule] = {}
    if beamed:
        harvesters.append(InductiveLink("bedside_pad", transmitter_power_w=15.0, coupling_k=0.3,
                                        q_transmitter=100, q_receiver=50, electronics_efficiency=0.8))
        harvesters.append(RFBeam("room_rf_beam", transmitter_power_w=1.0, distance_m=2.0,
                                 frequency_hz=5.8e9, gain_transmitter=10.0, gain_receiver=10.0))
        schedules["inductive_available"] = during([22, 23, 0, 1, 2, 3, 4, 5], 1.0)
        schedules["rf_beam_available"] = during(range(8, 22), 0.5)

    device = Device(
        name="smartphone",
        description="Smartphone, ~10 Wh/day",
        harvesters=harvesters,
        storage_factory=lambda: lithium_ion("phone_15wh", 15.0, c_rate=1.0),
        loads=[
            Load("standby", "critical", constant(0.05)),
            Load("active_use", "normal", hours(0.6, range(7, 22))),
        ],
    )
    return device, schedules


def electric_car(beamed: bool = False, home_pad: bool = False) -> tuple[Device, dict[str, HourlySchedule]]:
    harvesters = [
        SolarPV("body_solar", area_m2=5.0, efficiency_stc=0.22, orientation_factor=0.85),
        Rectenna("body_rf_array", frequency_hz=2.45e9, elements=200),
    ]
    schedules: dict[str, HourlySchedule] = {}
    if beamed:
        # Electrified road lanes: half of each commute hour spent over a 20 kW lane.
        harvesters.append(InductiveLink("electrified_road", transmitter_power_w=20_000.0,
                                        availability_key="road_lane_available"))
        schedules["road_lane_available"] = during([7, 17], 0.5)
    if home_pad:
        harvesters.append(InductiveLink("home_pad", transmitter_power_w=11_000.0,
                                        availability_key="home_pad_available"))
        schedules["home_pad_available"] = during([22, 23, 0, 1, 2, 3, 4, 5], 1.0)

    device = Device(
        name="electric_car",
        description="Compact EV, 40 km/day at 0.16 kWh/km",
        harvesters=harvesters,
        storage_factory=lambda: lithium_ion("pack_60kwh", 60_000.0, c_rate=0.5, initial_soc=0.6),
        loads=[
            Load("driving", "critical", hours(3200.0, [7, 17])),
            Load("standby_telematics", "normal", constant(15.0)),
            Load("cabin_precool", "deferrable", hours(750.0, [6, 16]), max_power_w=3000.0),
        ],
    )
    return device, schedules


def warehouse_robot(beamed: bool = True) -> tuple[Device, dict[str, HourlySchedule]]:
    harvesters = [
        # Indoors: only skylight daylight reaches the robot's top panel.
        SolarPV("top_solar", area_m2=0.5, efficiency_stc=0.22, orientation_factor=0.05),
    ]
    schedules: dict[str, HourlySchedule] = {}
    if beamed:
        harvesters.append(InductiveLink("station_pads", transmitter_power_w=3000.0, coupling_k=0.25))
        schedules["inductive_available"] = during(range(8, 18), 0.25)

    device = Device(
        name="warehouse_robot",
        description="Autonomous mobile robot, 10-hour shift",
        harvesters=harvesters,
        storage_factory=lambda: lithium_ion("robot_2kwh", 2000.0, c_rate=1.0),
        loads=[
            Load("driving", "critical", hours(400.0, range(8, 18))),
            Load("sensors_compute", "normal", constant(30.0)),
        ],
    )
    return device, schedules


def factory_machine(beamed: bool = False) -> tuple[Device, dict[str, HourlySchedule]]:
    harvesters = [
        Thermophotovoltaic("furnace_tpv", area_m2=0.05, bandgap_ev=0.55, view_factor=0.5),
        Thermoelectric("flue_teg", thermal_conductance_w_k=5.0, hot_key="flue_temperature_k"),
    ]
    schedules = {
        "heat_source_temperature_k": during(range(6, 22), 1500.0),
        "flue_temperature_k": during(range(6, 22), 600.0),
    }
    device = Device(
        name="factory_machine",
        description="Conveyor and controls beside a 1500 K furnace (16 h/day)",
        harvesters=harvesters,
        storage_factory=lambda: lithium_ion("machine_5kwh", 5000.0),
        loads=[
            Load("conveyor", "critical", hours(800.0, range(6, 22))),
            Load("controls", "normal", constant(50.0)),
        ],
    )
    return device, schedules


CATALOGUE: dict[str, Builder] = {
    "iot_sensor": iot_sensor,
    "smartphone": smartphone,
    "electric_car": electric_car,
    "warehouse_robot": warehouse_robot,
    "factory_machine": factory_machine,
}
