"""Map the empirical TPV model across source temperature and bandgap."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from radiocity.planck_model import net_band_radiative_flux
from tpv_empirical_model import empirical_efficiency

def main() -> None:
    """Generate a source-temperature/bandgap operating map."""
    output = Path(__file__).resolve().parents[1] / "results" / "tpv_temperature_bandgap_map.csv"
    output.parent.mkdir(exist_ok=True)
    receiver, capture, heat_limit = 373.15, 0.8, 1000.0
    temperatures = (1000.0, 1250.0, 1500.0, 1750.0, 2000.0, 2250.0, 2500.0, 2673.15, 3000.0)
    bandgaps = tuple(round(0.4 + 0.1 * i, 2) for i in range(13))
    with output.open("w", encoding="utf-8") as file:
        file.write("source_temperature_k,bandgap_ev,cutoff_wavelength_um,efficiency,absorbed_w_m2,gross_electric_w_m2,rejected_heat_w_m2,sustainable_electric_w_m2\n")
        for source in temperatures:
            flux = max(0.0, net_band_radiative_flux(0.1e-6, 10e-6, source, receiver))
            absorbed = flux * capture
            for bandgap in bandgaps:
                efficiency = empirical_efficiency(source, bandgap)
                gross = absorbed * efficiency
                rejected = absorbed - gross
                sustainable = gross if rejected <= heat_limit else heat_limit * efficiency / (1.0 - efficiency)
                cutoff = 1.239841984 / bandgap
                file.write(f"{source},{bandgap:.2f},{cutoff:.6f},{efficiency:.6f},{absorbed:.6f},{gross:.6f},{rejected:.6f},{sustainable:.6f}\n")

if __name__ == "__main__":
    main()
