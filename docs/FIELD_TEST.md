# Field Test: Measuring Real Solar Harvest

Simulation is checked against physics and independent models (see [../results/VALIDATION.md](../results/VALIDATION.md)). The next level of evidence is **measurement**: build a small harvester, log what it really produces, and compare with what Radiocity predicts for the same place and days.

## Kit (low cost)

| Part | Purpose |
|---|---|
| Small solar panel, 10-20 W, with its datasheet | The receiver |
| Charge controller (MPPT preferred) | Regulation (stop-when-full) - as in the model |
| 12 V battery (e.g. 7-12 Ah) | Storage |
| Constant load, e.g. a 5 W DC lamp or USB fan for some hours each day | Keeps the battery from staying full, so the panel keeps working |
| Energy logger: an ESP32 or Arduino with an INA219/INA226 current sensor (or a USB/DC energy meter you read daily) | Measures the panel's energy |

## Procedure

1. Mount the panel **flat (horizontal)** in a place with no shade from 07:00 to 18:00. Record latitude and longitude (from your phone's map).
2. Log the energy from the **panel to the controller** at least once per hour (or read a cumulative Wh meter at the same time every day).
3. Run for **at least 3-4 weeks**; longer covers more weather.
4. Keep a short diary: shading, dust (clean the panel weekly), anything unusual.
5. Save the log as CSV with columns `time_local` and `energy_wh` (energy since the previous row).

## Compare with Radiocity

NASA POWER publishes hourly data for recent days with a delay of a few days to a few weeks. After that:

```bash
python scripts/compare_field_test.py --csv my_log.csv --lat 9.06 --lon 7.49 \
    --panel-watts 20 --panel-efficiency 0.20
```

The script downloads NASA POWER weather for your exact location and dates, predicts the panel's daily energy with Radiocity's solar model, and reports the daily and total difference.

## How to read the result

- Within ±10-15% over a few weeks: the model is supported by measurement.
- Consistently lower measurement: check shading, dust, cable losses, controller efficiency, panel temperature; these become calibrated model parameters.
- This measurement - with photos of the setup and the raw log - is the strongest evidence you can show funders and reviewers.
