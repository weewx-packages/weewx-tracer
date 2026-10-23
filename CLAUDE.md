# WeeWX Tracer driver

Independent continuation of Matthew Wall's GPLv3 Tracer solar-controller driver.
The upstream history and copyright notices remain intact.

## Commands

- Install dependencies: `python -m pip install -r requirements.txt pytest`.
- Driver regression tests: `python -m pytest -q tests`.

## Structure and conventions

- `bin/user/tracer.py`: WeeWX driver and read-only Modbus diagnostics.
- `install.py`: WeeWX extension installer; version must match the driver.
- Follow the existing WeeWX style, using types in Google docstrings.
- Test Modbus responses without requiring a physical controller.
- Keep this repository independent; do not synchronize upstream over our fixes.

## Documentation

README follows the weewx-packages schema and names no versions or archive URLs; installation links to the catalog page.
