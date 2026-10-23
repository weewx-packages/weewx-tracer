weewx-tracer
============

WeeWX driver for EPEVER/Tracer MPPT solar charge controllers over RS485 Modbus.
Independent continuation of https://github.com/matthewwall/weewx-tracer at
7ffb96444660fe1363c3b8df5ec55b76aadd71de. Original author: Matthew Wall.
The original [GPLv3 license](license) and copyright notices remain in this repository.
This is a local serial driver; it does not use a cloud account.

Requirements
------------
Python >= 3.10, WeeWX >= 5, pymodbus >= 3.11 and < 4, and pyserial >= 3.5.
Install requirements.txt into the same Python environment as WeeWX. Give the
WeeWX service account access to the serial device. EPEVER USB adapters may use
/dev/ttyXRUSB0 and need their USB/serial driver installed on the host.

Installation
------------

    python -m pip install -r requirements.txt
    weectl extension install https://github.com/weewx-packages/weewx-tracer/releases/download/v0.3.0/tracer-0.3.0.zip --config=/path/to/weewx.conf
    weectl station reconfigure --driver=user.tracer --config=/path/to/weewx.conf

Use the `weectl` and Python interpreter from your WeeWX environment. Download
or clone this repository before using `requirements.txt`, or install the runtime
dependencies directly with `python -m pip install 'pymodbus>=3.11,<4' 'pyserial>=3.5'`.
Replace `/path/to/weewx.conf` with the station configuration. Stock WeeWX accepts
the fixed URL above or a downloaded copy of the same archive. It needs no catalog
integration. Release 0.3.0 supports WeeWX >=5,<6.

Restart WeeWX after configuring the station:

    [Station]
        station_type = Tracer

    [Tracer]
        port = /dev/ttyUSB0
        baud_rate = 115200
        poll_interval = 10
        driver = user.tracer

The original controller was a 3210A. LS1024B settings now read 0x9067 and
0x9069-0x906E separately, avoiding its unsupported 0x9068 register. Regression
tests use simulated Modbus responses; physical controller operation still needs
confirmation from a station operator.

Reports and diagnostics
-----------------------
The driver supplies battery_current, battery_voltage, battery_temperature,
ambient_temperature and energy observations. Select an archive schema containing
the fields you want to retain, then include those fields in your report's plots
or templates. This package supplies the driver and its example schema; use a
skin of your choice to display the data. For a new archive, the bundled example
schema is `user.tracer.schema`, declared in `bin/user/tracer.py`. Changing a
schema setting does not migrate an existing database. Daily counter fields need
your own schema columns and unit declarations; they are not in that example.
Energy readings in version 0.3.0 are
watt-hours, matching WeeWX METRIC units. Older driver versions emitted kWh under
that same unit label; review historical data before combining old and new energy
records. Daily and lifetime fields are counters; take differences when computing
energy consumed or generated during a period.

From a stopped station, using its Python environment and installed module path:

    PYTHONPATH=/path/to/station/bin python -m user.tracer --port /dev/ttyUSB0

The diagnostic prints device identification, ratings, settings, status, current
readings and statistics. status_charge_fault reports bit 1 of register 0x3201.
A value of 1 is the controller's reported status. Collect the full status output
and consult the controller's register documentation when investigating it.

The transport remains pymodbus. Timing differences between alternative Modbus
libraries and controller models have not been measured by this project.

Validation
----------

    python -m pytest -q tests

Tests cover fractional and signed readings, the LS1024B register gap, reported
fault flags, transient transport failures, device identification, observation
mapping and matching installer/driver versions.

<!-- Documentation updated 2026-10-23 by weewx-packages. -->
