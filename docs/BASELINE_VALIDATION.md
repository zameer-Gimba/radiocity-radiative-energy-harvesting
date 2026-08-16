# Baseline Model Validation

## Status

Initial sanity-check of the Portfolio A reference scenarios.

## Key result

The first comparison demonstrates that the model can represent materially different useful-power regimes, but **does not yet establish an engineering advantage for multi-spectral harvesting**.

For the current illustrative assumptions:

| Scenario | Incident power | Useful power |
|---|---:|---:|
| Solar reference | 1000 W | 225 W |
| 300 K thermal blackbody | 459.27 W | 41.33 W |
| 500 K thermal blackbody | 3543.75 W | 318.94 W |
| Combined solar + 300 K thermal | 1459.27 W | 266.33 W |

The combined case is approximately the sum of its independent channels because the present model has no spectral competition or adaptive routing.

## Important scientific correction before the next model stage

The current thermal examples use ideal blackbody emission, `P = sigma T^4`, as an incident-power reference. A practical radiative heat-transfer model must distinguish **gross emission** from **net radiative exchange** with the environment, generally using a relationship of the form:

`q_net = epsilon * sigma * (T_source^4 - T_surroundings^4)`

Geometry/view factors, atmospheric transmission, spectral selectivity, and the receiver temperature must also be considered where applicable.

Similarly, the present thermal bookkeeping treats conversion loss as system heating. This is intentionally simplified and must be separated into optical reflection/transmission, non-converted absorbed radiation, electrical conversion loss, and thermal rejection before making claims about thermal limits.

## Interpretation

The first scientifically useful observation is therefore not "more radiation creates more energy." It is:

> A multi-channel architecture can combine heterogeneous radiative inputs, but its value depends on whether additional channels provide meaningful net recoverable power after geometric, spectral, conversion, thermal, and control losses.

## Next validation requirements

1. Replace gross blackbody emission with net radiative exchange where appropriate.
2. Introduce source and receiver temperatures explicitly.
3. Separate capture loss from absorbed thermal load.
4. Add energy-conservation assertions to the tests.
5. Establish realistic RF power-density scenarios.
6. Only then compare fixed multi-spectrum and adaptive architectures.
