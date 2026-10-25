"""Radiocity Energy Autonomy Explorer.

    streamlit run streamlit_app.py

Author: Muhammad Ibrahim Gimba
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from radiocity.devices import CATALOGUE  # noqa: E402
from radiocity.forecast import add_solar_forecast  # noqa: E402
from radiocity.harvesters import RFBeam, SolarPV, antenna_effective_area_m2, rectifier_efficiency  # noqa: E402
from radiocity.scenarios import CITIES, RF_ENVIRONMENTS_W_M2, build_conditions, load_history  # noqa: E402
from radiocity.simulation import Device, simulate  # noqa: E402

KIND_COLORS = {"ambient": "#2A78D6", "heat": "#EB6834", "beamed": "#1BAF7A"}
KIND_LABELS = {"ambient": "Ambient (sun, radio)", "heat": "Waste heat", "beamed": "Beamed power"}
DEMAND_COLOR = "#52514E"

DEVICE_LABELS = {
    "iot_sensor": "IoT sensor",
    "smartphone": "Smartphone",
    "electric_car": "Electric car",
    "warehouse_robot": "Warehouse robot",
    "factory_machine": "Factory machine (beside furnace)",
}

BEAMED_OPTIONS = {
    "iot_sensor": {"beamed": "RF power beam (3 W at 5 m)"},
    "smartphone": {"beamed": "Bedside charging pad + room RF beam"},
    "electric_car": {"beamed": "Electrified road lanes (half of each commute)", "home_pad": "Home wireless pad (overnight)"},
    "warehouse_robot": {"beamed": "Charging pads at work stations"},
    "factory_machine": {},
}

st.set_page_config(page_title="Radiocity", page_icon="⚡", layout="wide")


@st.cache_data(show_spinner=False)
def conditions_for(city: str, rf_environment: str, device: str, options: tuple, ai: bool) -> pd.DataFrame:
    _, schedules = CATALOGUE[device](**dict(options))
    conditions = build_conditions(city, rf_environment, schedules)
    if ai:
        conditions = add_solar_forecast(conditions, load_history(city))
    return conditions


@st.cache_data(show_spinner=False)
def run(city: str, rf_environment: str, device_name: str, options: tuple, policy: str,
        ai: bool, solar_scale: float, storage_scale: float) -> tuple[pd.DataFrame, dict, list]:
    device, _ = CATALOGUE[device_name](**dict(options))
    harvesters = [
        replace(h, area_m2=h.area_m2 * solar_scale) if isinstance(h, SolarPV) else h
        for h in device.harvesters
    ]
    template = device.storage_factory()

    def storage_factory():
        storage = device.storage_factory()
        storage.capacity_wh = template.capacity_wh * storage_scale
        storage.max_charge_w = template.max_charge_w * storage_scale
        storage.max_discharge_w = template.max_discharge_w * storage_scale
        storage.energy_wh = storage.capacity_wh * storage.initial_soc
        return storage

    scaled = Device(device.name, harvesters, storage_factory, device.loads, device.description)
    result = simulate(scaled, conditions_for(city, rf_environment, device_name, options, ai), policy)
    kinds = [(h.name, h.kind) for h in harvesters]
    return result.hourly, result.summary, kinds


def energy_text(kwh: float) -> str:
    if kwh >= 1:
        return f"{kwh:,.2f} kWh"
    if kwh >= 1e-3:
        return f"{kwh * 1000:,.1f} Wh"
    if kwh >= 1e-6:
        return f"{kwh * 1e6:,.1f} mWh"
    if kwh <= 0:
        return "0"
    return f"{kwh * 1e9:,.2f} µWh"


def page_explorer() -> None:
    st.title("Radiocity Energy Autonomy Explorer")
    st.caption(
        "How much of a device's energy can invisible energy supply - sunlight, radio waves, "
        "waste heat and beamed power? Calculated hour by hour over all of 2024 using real NASA weather "
        "for each city."
    )

    with st.sidebar:
        st.header("Scenario")
        device_name = st.selectbox("Device", list(DEVICE_LABELS), format_func=DEVICE_LABELS.get, index=2)
        city = st.selectbox("City", list(CITIES), format_func=CITIES.get)
        rf_environment = st.selectbox("Radio environment", list(RF_ENVIRONMENTS_W_M2), index=1,
                                      format_func=lambda k: k.replace("_", " ").capitalize())
        st.subheader("Beamed power")
        options = {}
        for key, label in BEAMED_OPTIONS[device_name].items():
            options[key] = st.checkbox(label, value=False)
        if device_name == "warehouse_robot":
            options.setdefault("beamed", False)
        st.subheader("Design")
        solar_scale = st.slider("Solar receiver area (× default)", 0.0, 3.0, 1.0, 0.25)
        storage_scale = st.slider("Storage capacity (× default)", 0.25, 3.0, 1.0, 0.25)
        policy = st.radio("Energy management", ["smart", "reserve", "basic"], horizontal=True)
        ai = st.toggle("AI day-ahead solar forecast", value=False, disabled=policy != "smart",
                       help="An AI that predicts tomorrow's sunshine (learned from 2019-2023 weather), so the power "
                            "manager knows how much energy to save tonight.")

    with st.spinner("Simulating 8,784 hours..."):
        hourly, summary, kinds = run(city, rf_environment, device_name, tuple(sorted(options.items())),
                                     policy, ai and policy == "smart", solar_scale, storage_scale)

    days = summary["days"]
    cols = st.columns(4)
    cols[0].metric("Energy autonomy", f"{summary['energy_autonomy_pct']:.1f}%",
                   help="Share of the year's energy need supplied by invisible energy.")
    cols[1].metric("Critical loads available", f"{summary['critical_availability_pct']:.1f}%",
                   help="Share of hours in which critical loads were fully powered.")
    cols[2].metric("Need per day", energy_text(summary["demand_kwh"] / days))
    cols[3].metric("Plug/fuel still needed per day", energy_text(summary["external_energy_kwh"] / days))

    if summary["critical_availability_pct"] < 99.9:
        st.caption(
            "Without any plug or fuel top-up, storage runs down and critical loads fall short in "
            f"{100 - summary['critical_availability_pct']:.0f}% of their hours. The shortfall is the energy "
            "still needed above - add receivers, storage or beamed power to close it."
        )

    if device_name == "electric_car":
        ambient_km = summary["ambient_kwh"] / days / 0.16
        st.info(f"The solar skin alone supplies about **{ambient_km:.0f} km of driving per day** on average "
                f"in {CITIES[city]} (at 0.16 kWh/km).")

    monthly = hourly.resample("MS").sum()
    fig = go.Figure()
    for kind in ["ambient", "heat", "beamed"]:
        names = [name for name, k in kinds if k == kind]
        if not names:
            continue
        values = monthly[[f"harvest_{n}_wh" for n in names]].sum(axis=1) / 1000
        if values.sum() <= 0:
            continue
        fig.add_bar(x=monthly.index, y=values, name=KIND_LABELS[kind], marker_color=KIND_COLORS[kind],
                    hovertemplate="%{x|%b}: %{y:,.3g} kWh<extra>" + KIND_LABELS[kind] + "</extra>")
    demand = monthly[[c for c in monthly if c.endswith("_demand_wh")]].sum(axis=1) / 1000
    fig.add_scatter(x=monthly.index, y=demand, name="Energy need", mode="lines+markers",
                    line=dict(color=DEMAND_COLOR, width=2, dash="dot"), marker=dict(size=8),
                    hovertemplate="%{x|%b}: %{y:,.3g} kWh<extra>Need</extra>")
    fig.update_layout(barmode="stack", title="Monthly energy harvested vs needed", yaxis_title="kWh",
                      legend=dict(orientation="h", y=-0.15), height=380, margin=dict(l=10, r=10, t=50, b=10),
                      bargap=0.25)
    st.plotly_chart(fig, width="stretch")

    st.subheader("Storage and regulation over one week")
    week_start = st.select_slider("Week starting", options=list(pd.date_range("2024-01-01", "2024-12-23", freq="7D").date),
                                  value=pd.Timestamp("2024-07-01").date(), format_func=lambda d: d.strftime("%d %b"))
    week = hourly.loc[str(week_start):str(pd.Timestamp(week_start) + pd.Timedelta(days=6))]
    soc = go.Figure()
    soc.add_scatter(x=week.index, y=100 * week["soc"], name="State of charge", mode="lines",
                    line=dict(color="#2A78D6", width=2), hovertemplate="%{x|%a %H:%M}: %{y:.0f}%<extra>Charge</extra>")
    if policy == "smart":
        soc.add_scatter(x=week.index, y=100 * week["reserve_soc"], name="Reserve kept for critical loads",
                        mode="lines", line=dict(color=DEMAND_COLOR, width=1.5, dash="dot"),
                        hovertemplate="%{x|%a %H:%M}: %{y:.0f}%<extra>Reserve</extra>")
    soc.update_layout(yaxis=dict(range=[0, 100], title="% of capacity"), height=300,
                      legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified")
    st.plotly_chart(soc, width="stretch")
    st.caption("Charging stops automatically at the upper limit (stop-when-full); surplus is curtailed. "
               f"Curtailed this year: {summary['curtailed_pct_of_harvest']:.0f}% of harvest.")

    st.subheader("Energy by receiver over the year")
    table = pd.DataFrame(
        [{"Receiver": name, "Kind": KIND_LABELS[kind], "Per day": energy_text(summary["harvest_by_source_kwh"][name] / days),
          "Per year": energy_text(summary["harvest_by_source_kwh"][name])} for name, kind in kinds]
    )
    st.dataframe(table, hide_index=True, width="stretch")


def page_limits() -> None:
    st.title("Physics check")
    st.caption("Quick calculators for what each kind of invisible energy can deliver.")

    st.subheader("Ambient radio waves")
    c1, c2, c3 = st.columns(3)
    density = c1.select_slider("Power density (W/m²)", options=[1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0], value=1e-4,
                               format_func=lambda v: f"{v:g}")
    frequency = c2.select_slider("Frequency", options=[900e6, 2.45e9, 5.8e9], value=2.45e9,
                                 format_func=lambda f: f"{f / 1e9:g} GHz")
    elements = c3.select_slider("Antennas", options=[1, 10, 100, 1000], value=1)
    aperture = antenna_effective_area_m2(frequency, 1.64)
    captured = density * aperture
    dc = elements * captured * rectifier_efficiency(captured)
    st.metric("DC power", f"{dc * 1e6:,.4g} µW", help="Effective area per antenna x density x rectifier efficiency.")
    st.caption(f"Each antenna captures {captured * 1e9:,.3g} nW over {aperture * 1e4:.1f} cm²; "
               f"rectifier efficiency at that power: {rectifier_efficiency(captured):.1%}.")

    st.subheader("Microwave power beam")
    c1, c2 = st.columns(2)
    power = c1.select_slider("Transmitter power (W)", options=[1, 10, 100, 1000], value=10)
    distance = c2.select_slider("Distance (m)", options=[1, 2, 5, 10, 20, 50], value=5)
    beam = RFBeam("beam", float(power), float(distance))
    st.metric("DC power received", f"{beam.power_w({'rf_beam_available': 1.0}):,.3g} W")
    st.caption(f"Power density at the receiver: {beam.power_density_w_m2():,.2g} W/m² - "
               + ("within" if beam.exposure_ok else "**above**")
               + " the ICNIRP public exposure limit (10 W/m²).")


def page_how_we_know() -> None:
    st.title("How we know")
    st.markdown(
        """
These numbers are **calculated, not invented**, and you can check every one:

- **Real weather.** Every hour of 2024 for Abuja, Lagos, Kano and Port Harcourt, measured and published by NASA.
- **Standard physics.** The same textbook equations engineers use for solar panels, antennas, heat engines and
  wireless chargers - each one cited in the code and documentation.
- **Open and repeatable.** The code is public; one command recalculates every result from scratch.
- **Checked against independent sources.** The table below compares Radiocity's own numbers with exact laws of
  physics, the European Commission's official solar calculator (PVGIS) and published laboratory records.
"""
    )
    path = ROOT / "results" / "validation.csv"
    if path.exists():
        table = pd.read_csv(path)[["check", "radiocity", "reference", "difference"]]
        table.columns = ["Check", "Radiocity", "Independent reference", "Difference"]
        st.table(table.set_index("Check"))
    st.markdown(
        """
**Solar check in plain words:** for a 1 kW solar installation, Radiocity predicts 4-7% *less* yearly energy
than the European Commission's calculator in every city - it does not exaggerate. Most of that small gap is
because 2024 was a less sunny year than the 2005-2023 average the calculator uses.

**Next step - real hardware.** A small solar panel, battery and energy logger, measured for a few weeks in
Abuja and compared with Radiocity's prediction for the same days. The guide and comparison script are in the
repository (`docs/FIELD_TEST.md`).
"""
    )


def page_about() -> None:
    st.title("About Radiocity")
    st.markdown(
        """
**The vision.** Devices that power themselves from invisible energy - sunlight, radio waves, heat from
machines, and energy beamed to them wirelessly. Each device carries receivers; a smart power system stores
the energy, stops charging when full, keeps a reserve for what matters most, and uses surplus while it is free.

**What we found** (every hour of 2024, four Nigerian cities):

- **Sensors** run entirely on a solar cell about 1-2 cm² in size.
- **Phones** get about 12-16% of their daily energy from a solar back; a bedside wireless pad covers the rest.
- **A compact electric car** with 5 m² of solar skin drives about **20-27 km per day on sunlight alone** -
  roughly 40-50% of a 40 km daily commute. Radio waves add almost nothing; electrified road lanes close the gap.
- **Machines beside a hot furnace** can run entirely on the recovered heat.
- **Smart planning helps:** on a deliberately undersized sensor, the smart power manager kept it running every
  single day, where a simple controller failed on about 2-3% of days.

**About the AI.** To plan how much energy to save, the power manager needs a guess of tomorrow's sunshine.
The simple rule is "tomorrow will be like today". Our AI learned from five years of past weather and was then
tested on 2024, a year it had never seen. In Abuja its guesses were off by about 9% on average; the best simple
rule was off by 11%. Across the four cities, the AI's mistakes were 20-30% smaller.

See **How we know** for how these numbers are checked.

**Author:** Muhammad Ibrahim Gimba ·
[GitHub](https://github.com/zameer-Gimba/radiocity-radiative-energy-harvesting)
"""
    )


pages = {"Explorer": page_explorer, "Physics check": page_limits, "How we know": page_how_we_know, "About": page_about}
with st.sidebar:
    choice = st.radio("Page", list(pages), horizontal=True, label_visibility="collapsed")
    st.divider()
pages[choice]()
