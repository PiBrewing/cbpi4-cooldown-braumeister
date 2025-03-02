# Craftbeerpi4 Plugin for Cooldown step with calculation of end time

The last step in cbpi that can be configured is a cooldown step. It'll be created if you have selected a cooldown step for the corresponding parameter. The step type must Start with Cooldown. One step comes with Craftbeerpi4. 

This step is applicable to kettles with cooling jacket (such as Speidel Braumeister Plus), but should work also with a cooling coil inside the wort.

The step caLculates the cooldown behavior based on newtons law of cooling and uses the data of the past 10 minutes in the step. In the beginning it waits for 2 Minutes and after the first 12 Minuted you will receive an estimation on when the process will be completed and the target temperature is reached 

The calculation is down with scipy and this formula is used for the curve fit: a * exp(-c * time) + d

The picture below shows as an example the principle. You can see the initial data in red from a cooldown step and the fitted curve in blue. The green datapoint is the estimated time, when the target Temperature is reached.

![Simulation data](https://github.com/PiBrewing/cbpi4-cooldown-braumeister/blob/main/Prediction_Curve.png?raw=true)

Below is an example of a real process done with the Braumeister 20 Plus. You can see, that the prediction has an accuracy  within 5 Minutes.

![Process Log](https://github.com/PiBrewing/cbpi4-cooldown-braumeister/blob/main/log.png?raw=true)

## Software installation:

Please have a look at the [Craftbeerpi4 Documentation](https://openbrewing.gitbook.io/craftbeerpi4_support/readme/plugin-installation)

- Package name: cbpi4-cooldown-braumeister
- Package link: https://github.com/PiBrewing/cbpi4-cooldown-braumeister/archive/main.zip

## Step Configuration

- Once successfully installed, select 'CooldownStepBM' for 'steps_cooldown' in the Craftbeerpi settings-

### Changelog:

- 02.03.25: (0.0.1) Initial Release
