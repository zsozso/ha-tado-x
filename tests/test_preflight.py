"""Exercise deployment compatibility without cloud calls or real credentials."""
import asyncio
import importlib
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from requests import Response
from PyTado.zone import TadoXZone
from custom_components.tado.api_client import Tado
from custom_components.tado.coordinator import TadoDataUpdateCoordinator
from custom_components.tado.climate import create_climate_entity
from custom_components.tado.entity import TadoDeviceEntity

class PreflightTests(unittest.IsolatedAsyncioTestCase):
    def test_imports(self):
        for name in ('climate', 'binary_sensor', 'sensor', 'switch', 'select', 'water_heater', 'config_flow', 'diagnostics'):
            importlib.import_module('custom_components.tado.' + name)

    def test_quota(self):
        with patch("custom_components.tado.api_client.BaseTado.__init__", return_value=None) as init:
            client = Tado()
        session = init.call_args.kwargs["http_session"]
        response = Response()
        response.headers.update({'RateLimit-Policy': '"perday";q=20000;w=86400', 'RateLimit': '"perday";r=15211'})
        client._track_quota(response)
        self.assertEqual(client.rate_limit_info()['remaining'], '15211')
        self.assertTrue(session.headers['User-Agent'].startswith('HomeAssistant/'))

    async def test_x_devices_and_climate(self):
        coordinator = object.__new__(TadoDataUpdateCoordinator)
        coordinator.is_x = True
        coordinator.home_id = 123
        coordinator.home_name = 'Test'
        coordinator._tado = MagicMock()
        coordinator.config_entry = MagicMock()
        coordinator._listeners = {}
        coordinator.last_update_success = True
        devices = coordinator._update_device_info([
            [{'serialNo': 'bridge', 'type': 'IB02', 'firmwareVersion': '1'}],
            {'serialNo': 'valve', 'type': 'VA02', 'firmwareVersion': '2', 'temperatureOffset': 0.5}
        ])
        self.assertEqual(set(devices), {'bridge', 'valve'})
        self.assertEqual(devices['valve']['serialNumber'], 'valve')
        self.assertEqual(devices['valve']['temperatureOffset']['celsius'], 0.5)
        # X entity metadata must not reference itself as a bridge.
        entity = TadoDeviceEntity(devices['bridge'], coordinator)
        self.assertNotIn('via_device', entity.device_info)
        self.assertEqual(entity.device_info['model'], 'IB02')
        coordinator.data = {
            'device': devices,
            'zone': {1: TadoXZone.from_data(1, {'setting': {'power':'ON', 'temperature':{'value':21}}, 'heatingPower':{'percentage':30}, 'sensorDataPoints':{'insideTemperature':{'value':20}, 'humidity':{'percentage':45}}, 'connection':{'state':'CONNECTED'}})},
            'geofence': {'presence':'HOME'},
        }
        from custom_components.tado.binary_sensor import TADO_X_LINK_ENTITY_DESCRIPTION
        self.assertTrue(TADO_X_LINK_ENTITY_DESCRIPTION.state_fn(coordinator.data["zone"][1]))
        coordinator.zones = [{'id':1, 'type':'HEATING'}, {'id':2, 'type':'HOT_WATER'}]
        coordinator.get_auto_geofencing_supported = AsyncMock(return_value=False)
        climate = await create_climate_entity(coordinator, 'Test', 1, devices['valve'])
        self.assertEqual(climate.min_temp, 5.5)
        self.assertEqual(climate.max_temp, 30)
        self.assertEqual(climate.current_temperature, 20)
        self.assertEqual(climate.target_temperature, 21)
        self.assertEqual(climate.target_temperature_step, 0.5)
        self.assertEqual((await coordinator.get_capabilities(2))['type'], 'HOT_WATER')
        await coordinator._async_fetch_heating_circuits()
        coordinator._tado.get_heating_circuits.assert_not_called()

    def test_pre_x_devices(self):
        coordinator = object.__new__(TadoDataUpdateCoordinator)
        coordinator.is_x = False
        coordinator._tado = MagicMock()
        device = {'shortSerialNo':'old', 'serialNo':'old-full', 'deviceType':'VA01', 'characteristics':{'capabilities':[]}}
        self.assertIn('old', coordinator._update_device_info([device]))

if __name__ == '__main__':
    unittest.main(verbosity=2)
