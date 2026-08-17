# Research Model Policy

## Purpose

Radiocity separates exploratory engineering models from validated physical models so that repository results can later be translated into an academically defensible paper.

## Evidence hierarchy

1. **Validated physical model** — equations and assumptions are physically justified, numerically tested, and supported by appropriate literature.
2. **Calibrated engineering model** — model is anchored to measured or literature data but remains an approximation.
3. **Sensitivity model** — deliberately simplified model used to understand parameter dependence.
4. **Illustrative model** — conceptual model used to explore an idea; not suitable for quantitative scientific claims.

## TPV policy

The earlier wavelength-dependent 40%/20%/0% TPV efficiency function is retained only for provenance and sensitivity analysis. Its outputs must not be treated as experimentally validated TPV performance.

The current literature-anchored TPV efficiency envelope is also an engineering sensitivity model. Literature anchors can constrain plausible efficiency ranges, but they do not constitute a calibrated Radiocity device model.

A future final TPV model should explicitly account for the relevant spectral response, bandgap, below-bandgap losses, voltage/current losses, radiative recombination, and thermal balance, using published device data where available.

## Result policy

Every quantitative result intended for the paper should record:

- model version or commit;
- source and receiver temperatures;
- spectral range and numerical integration method;
- optical/capture assumptions;
- conversion assumptions;
- thermal rejection constraint;
- parameter sources;
- whether the result is simulated, calibrated, or experimentally validated.

Historical exploratory results remain useful for showing why the final model was selected, but they should be clearly marked as superseded when a fundamental assumption changes.
