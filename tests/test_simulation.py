"""System-level checks: conservation, regulation, policies, devices."""

import pytest

from radiocity.devices import CATALOGUE
from radiocity.harvesters import SolarPV
from radiocity.loads import Load, constant, hours
from radiocity.scenarios import build_conditions
from radiocity.simulation import Device, compare_policies, simulate
from radiocity.storage import lithium_ion


@pytest.fixture(scope="module")
def abuja():
    return build_conditions("abuja", "urban")


def sensor(area_m2: float) -> Device:
    return Device(
        "sensor",
        [SolarPV("pv", area_m2, efficiency_stc=0.18, orientation_factor=0.8)],
        lambda: lithium_ion("b", 0.05),
        [
            Load("sensing", "critical", constant(0.0002)),
            Load("uplink", "deferrable", hours(0.02, [20]), max_power_w=0.05),
            Load("display", "normal", hours(0.001, range(6, 22))),
        ],
    )


def test_energy_is_conserved_every_hour(abuja):
    """Harvest = used directly + offered to storage; delivered = direct + from storage."""

    result = simulate(sensor(0.0003), abuja, "smart", warmup=False)
    h = result.hourly
    delivered = sum(h[f"{p}_delivered_wh"] for p in ("critical", "normal", "deferrable"))

    assert (h["harvest_wh"] - h["used_directly_wh"] - h["stored_wh"] - h["curtailed_wh"]).abs().max() < 1e-12
    assert (delivered - h["used_directly_wh"] - h["from_storage_wh"]).abs().max() < 1e-12
    assert h["curtailed_wh"].min() >= -1e-12


def test_storage_balance_closes_over_the_year(abuja):
    """Change in stored energy = charge in - discharge out - all losses."""

    device = sensor(0.0003)
    result = simulate(device, abuja, "smart", warmup=False)
    h = result.hourly
    start = device.storage_factory().energy_wh
    end = h["storage_energy_wh"].iloc[-1]
    taken = h["stored_wh"].sum()
    delivered_from_storage = h["from_storage_wh"].sum()
    # Losses are the only remaining term, and they must be non-negative.
    losses = start + taken - delivered_from_storage - end
    assert losses >= 0
    assert losses < 0.2 * (taken + start)


def test_regulation_curtails_when_full(abuja):
    result = simulate(sensor(0.01), abuja, "basic")
    assert result.summary["curtailed_pct_of_harvest"] > 50
    assert result.hourly["soc"].max() <= 0.9 + 1e-9


def test_smart_policy_is_never_worse_than_basic_for_critical_loads():
    conditions = build_conditions("port_harcourt", "urban")
    table = compare_policies(sensor(0.0002), conditions).set_index("policy")
    assert table.loc["smart", "critical_availability_pct"] >= table.loc["basic", "critical_availability_pct"]
    assert table.loc["smart", "energy_autonomy_pct"] >= table.loc["basic", "energy_autonomy_pct"]


@pytest.mark.parametrize("name", sorted(CATALOGUE))
def test_every_catalogue_device_runs(name):
    device, schedules = CATALOGUE[name]()
    conditions = build_conditions("kano", "urban", schedules)
    summary = simulate(device, conditions, "smart", warmup=False).summary
    assert 0.0 <= summary["energy_autonomy_pct"] <= 100.0
    assert summary["harvest_kwh"] >= 0.0


def test_beamed_power_closes_the_gap_for_the_car(abuja):
    car, _ = CATALOGUE["electric_car"]()
    beamed_car, schedules = CATALOGUE["electric_car"](beamed=True)
    solar_only = simulate(car, abuja, "smart").summary["energy_autonomy_pct"]
    with_road = simulate(beamed_car, build_conditions("abuja", "urban", schedules), "smart").summary["energy_autonomy_pct"]
    assert solar_only < 80 < with_road


def test_unknown_policy_rejected(abuja):
    with pytest.raises(ValueError):
        simulate(sensor(0.001), abuja, "magic")
