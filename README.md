# Tracer / EPEVER

A WeeWX driver for EPEVER and Tracer MPPT solar charge controllers. It reads
battery, temperature and energy values over RS485 Modbus through a local
serial port. It uses no cloud account and does not write settings to the
controller.

This is an independent continuation of
[matthewwall/weewx-tracer](https://github.com/matthewwall/weewx-tracer),
continued from commit `7ffb96444660fe1363c3b8df5ec55b76aadd71de`. Original
author: Matthew Wall.

## Requirements

- An EPEVER or Tracer charge controller connected through an RS485 serial
  adapter. The WeeWX service account needs permission to open the serial port.
- The Python packages `pymodbus` and `pyserial`, installed in the Python
  environment that runs WeeWX:

  ```sh
  python -m pip install 'pymodbus>=3.11,<4' 'pyserial>=3.5'
  ```

## Installation

Install `tracer` from the [WeeWX packages catalog](https://github.com/weewx-packages/catalog/blob/main/packages/tracer.md).
The catalog page lists the current release, its WeeWX and Python
requirements, and the install, update and removal commands.

Then select the driver and restart WeeWX:

```sh
weectl station reconfigure --driver=user.tracer --config=/path/to/weewx.conf
```

## Configuration

```ini
[Station]
    station_type = Tracer

[Tracer]
    driver = user.tracer
    port = /dev/ttyUSB0
```

Options in `[Tracer]`:

| Option | Default | Meaning |
|---|---|---|
| `port` | `/dev/ttyUSB0` | Serial port of the RS485 adapter. |
| `baud_rate` | `115200` | Serial speed. |
| `timeout` | `1` | Modbus timeout in whole seconds. |
| `poll_interval` | `10` | Seconds between packets. `0` polls without a pause. |
| `max_tries` | `3` | Attempts per read before the driver raises an I/O error. |
| `retry_wait` | `5` | Seconds between attempts. |
| `model` | `EPEVER` | Hardware name the driver reports to WeeWX. |
| `[[sensor_map]]` | see below | Maps packet fields to controller values. Entries replace the defaults with the same name. |

Packets use `METRIC` units and contain these fields:

| Packet field | Controller value | Unit |
|---|---|---|
| `battery_voltage` | `battery_voltage` | volt |
| `battery_current` | `battery_current` | amp |
| `battery_temperature` | `battery_temperature` | degree_C |
| `ambient_temperature` | `ambient_temperature` | degree_C |
| `consumed_energy` | `consumed_energy_total` | watt-hour |
| `consumed_energy_today` | `consumed_energy_today` | watt-hour |
| `generated_energy` | `generated_energy_total` | watt-hour |
| `generated_energy_today` | `generated_energy_today` | watt-hour |

The energy fields are counters. Take differences to get the energy of a
period.

### Storing the data

WeeWX stores only fields that have a column in the archive database. The
driver module contains an example schema, `user.tracer.schema`, with the
columns `ambient_temperature`, `battery_temperature`, `battery_current`,
`battery_voltage`, `consumed_energy` and `generated_energy`. Use it for a new
database in the binding's `schema` option. Changing the schema option does
not change an existing database.

The driver assigns unit groups to the six fields of the example schema. The
`_today` fields have no unit group and no column in the example schema. Add
both yourself if you want to keep them. The package has no skin; show the
fields in a skin of your choice.

### Reading the controller directly

Stop WeeWX first, then run the module with the Python of the WeeWX
environment:

```sh
PYTHONPATH=/path/to/station/bin python -m user.tracer --port /dev/ttyUSB0
```

It prints device identification, ratings, settings, status flags, current
readings, coils and statistics. Further options: `--baud-rate`, `--timeout`,
`--debug`, `--version`. `status_charge_fault` is bit 1 of register 0x3201 as
the controller reports it.

## Limitations

- Tested only with simulated Modbus responses, not with a physical
  controller. The original driver was tested with a 3210A.
- LS1024B controllers reject reads across register 0x9068. The driver reads
  0x9067 and 0x9069 to 0x906E separately.
- Earlier versions of this driver reported energy in kWh under the WeeWX
  watt-hour unit. The energy fields are now watt-hours. Check archived energy
  data from the earlier driver before combining it with new records.
- The driver writes its log messages to syslog with the prefix `Tracer:`, not
  through the WeeWX logging configuration.

## Development

```sh
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
```

## License

Copyright 2019 Matthew Wall. Distributed under the GNU General Public License
version 3, see [license](license) and the source headers.
