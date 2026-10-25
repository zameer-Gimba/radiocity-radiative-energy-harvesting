"""Storage regulation and energy bookkeeping."""

import pytest

from radiocity.storage import Storage, lithium_ion, supercapacitor


def test_stops_charging_when_full():
    battery = lithium_ion("b", 100.0, initial_soc=0.5)
    for _ in range(100):
        battery.charge(1000.0, 1.0)
    assert battery.soc == pytest.approx(battery.soc_max)
    assert battery.charge(1000.0, 1.0) == 0.0


def test_charge_tapers_near_full():
    battery = lithium_ion("b", 100.0, initial_soc=0.5)
    battery.energy_wh = 0.5 * 100
    early = battery.charge_acceptance_w()
    battery.energy_wh = 0.88 * 100
    late = battery.charge_acceptance_w()
    assert late < early


def test_never_discharges_below_minimum():
    battery = lithium_ion("b", 100.0, initial_soc=0.5)
    delivered = battery.discharge(10_000.0, 10.0)
    assert battery.soc == pytest.approx(battery.soc_min)
    assert delivered <= (0.5 - battery.soc_min) * 100


def test_energy_bookkeeping_balances():
    battery = Storage("b", 100.0, initial_soc=0.5)
    start = battery.energy_wh
    taken = battery.charge(30.0, 1.0)
    delivered = battery.discharge(20.0, 1.0)
    lost = battery.idle(24.0)
    assert battery.energy_wh == pytest.approx(start + taken - delivered - battery.losses_wh + 0.0)
    assert lost > 0


def test_supercapacitor_self_discharges_faster():
    cap = supercapacitor("c", 10.0, initial_soc=0.9)
    cell = lithium_ion("b", 10.0, initial_soc=0.9)
    assert cap.idle(24.0) > cell.idle(24.0)


def test_invalid_window_rejected():
    with pytest.raises(ValueError):
        Storage("b", 10.0, soc_min=0.5, taper_start_soc=0.4, soc_max=0.9)
