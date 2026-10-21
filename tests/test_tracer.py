"""Exercise reported controller responses without a serial connection."""

import importlib.util
from pathlib import Path
from unittest.mock import Mock
import sys

from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus.pdu.mei_message import ReadDeviceInformationResponse
from pymodbus.pdu.register_message import ReadHoldingRegistersResponse, ReadInputRegistersResponse
import pytest
import weewx
import weewx.units

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin/user'))
import tracer


@pytest.mark.parametrize('raw,want', [(1234, 12.34), (0xFF85, -1.23)])
def test_signed_fractional_readings(raw, want):
    assert tracer.value16(raw) == pytest.approx(want)
    assert tracer.value32(raw, 0xFFFF if raw & 0x8000 else 0) == pytest.approx(want)


def test_energy_counters_match_weewx_metric_units(monkeypatch):
    controller = tracer.Tracer('/dev/not-opened', 115200, 1)
    registers = [0] * 31
    registers[4] = 123
    registers[10:12] = [0xFFFF, 0xFFFF]
    monkeypatch.setattr(controller, 'read_input_registers', lambda *args, **kwargs:
                        ReadInputRegistersResponse(registers=registers))
    data = controller.get_statistics()
    assert data['consumed_energy_today'] == 1230.0
    assert data['consumed_energy_total'] == 42949672950.0


def test_ls1024b_settings_do_not_read_reserved_register(monkeypatch):
    controller = tracer.Tracer('/dev/not-opened', 115200, 1)
    requests = []

    def read(address, *, count, device_id):
        requests.append((address, count, device_id))
        if address <= 0x9068 < address + count:
            return ExceptionResponse(3, 2)
        if address == 0x9067:
            return ReadHoldingRegistersResponse(registers=[2])
        if address == 0x9069:
            return ReadHoldingRegistersResponse(registers=[1, 1, 120, 90, 30, 80])
        if address == 0x9013:
            return ReadHoldingRegistersResponse(registers=[0, 0x0100, 0x1A01] + [0] * 12)
        return ReadHoldingRegistersResponse(registers=[0] * count)

    monkeypatch.setattr(controller, 'read_holding_registers', read)
    data = controller.get_settings()
    assert data['battery_rated_voltage_code'] == '24V'
    assert data['load_timing_control_selection'] == 'using timer 2'
    assert data['default_load_onoff_in_manual_mode'] == 'on'
    assert data['equalize_duration'] == 120
    assert data['boost_duration'] == 90
    assert data['discharge_percentage'] == 30
    assert data['charging_percentage'] == 80
    assert (0x9067, 1, 1) in requests and (0x9069, 6, 1) in requests


def test_charge_fault_flag_reports_controller_bit(monkeypatch):
    controller = tracer.Tracer('/dev/not-opened', 115200, 1)
    monkeypatch.setattr(controller, 'read_input_registers', lambda *args, **kwargs:
                        ReadInputRegistersResponse(registers=[0, 2, 0]))
    assert controller.get_status()['status_charge_fault'] == 1


def test_driver_retries_transport_errors_and_preserves_current_units(monkeypatch):
    controller = Mock()
    controller.get_info.return_value = {}
    controller.get_data.side_effect = [ModbusException('timeout'), {'battery_current': 1.25}]
    controller.get_statistics.return_value = {'consumed_energy_total': 0.75, 'battery_voltage': 12.4}
    monkeypatch.setattr(tracer, 'Tracer', Mock(return_value=controller))
    monkeypatch.setattr(tracer.time, 'sleep', Mock())
    driver = tracer.TracerDriver(port='/dev/not-opened', baud_rate=115200, timeout=1, retry_wait=0)
    packet = next(driver.genLoopPackets())
    assert controller.get_data.call_count == 2
    assert packet['battery_current'] == 1.25
    assert packet['battery_voltage'] == 12.4
    assert packet['consumed_energy'] == 0.75
    assert packet['usUnits'] == weewx.METRIC
    assert weewx.units.obs_group_dict['battery_current'] == 'group_amp'
    assert weewx.units.obs_group_dict['battery_voltage'] == 'group_volt'


def test_identification_uses_current_pymodbus_api(monkeypatch):
    controller = tracer.Tracer('/dev/not-opened', 115200, 1)
    read = Mock(side_effect=[ReadDeviceInformationResponse(information={0: b'EPEVER', 1: b'3210A', 2: b'1'}),
                            ReadDeviceInformationResponse(information={3: b'123'})])
    monkeypatch.setattr(controller, 'read_device_information', read)
    assert controller.get_info()['serial'] == b'123'
    assert [call.kwargs for call in read.call_args_list] == [
        {'read_code': 1, 'device_id': 1}, {'read_code': 2, 'device_id': 1}]


def test_unsupported_identification_is_not_a_driver_failure(monkeypatch):
    controller = tracer.Tracer('/dev/not-opened', 115200, 1)
    monkeypatch.setattr(controller, 'read_device_information', Mock(return_value=ExceptionResponse(43, 1)))
    assert controller.get_info() == {'error': 'Device identification is not supported'}


def test_installer_version_matches_driver():
    path = Path(__file__).resolve().parents[1] / 'install.py'
    spec = importlib.util.spec_from_file_location('tracer_installer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    installer = module.loader()
    assert installer['name'] == 'tracer'
    assert installer['version'] == tracer.DRIVER_VERSION
