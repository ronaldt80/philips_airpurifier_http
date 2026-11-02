from unittest.mock import MagicMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier_http.client import CannotConnect
from custom_components.philips_airpurifier_http.const import DOMAIN

P = "custom_components.philips_airpurifier_http"
MAC = "aa:bb:cc:dd:ee:ff"


def fake_client(status=None):
    c = MagicMock()
    c.get_status.return_value = status or {
        "pwr": "1",
        "om": "2",
        "mode": "M",
        "pm25": 7,
    }
    c.get_filters.return_value = {"fltsts0": 10, "fltsts1": 100, "fltsts2": 200}
    c.get_firmware.return_value = {"name": "AC2889_10"}
    c.get_wifi.return_value = {"macaddress": MAC.upper()}
    return c


async def test_user_flow_creates_entry(hass):
    with patch(
        f"{P}.config_flow.probe", return_value={"mac": MAC, "model": "AC2889_10"}
    ):
        r = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert r["type"] == data_entry_flow.FlowResultType.FORM
        r = await hass.config_entries.flow.async_configure(
            r["flow_id"], {"host": " 192.168.1.50 ", "name": "Salon purifier"}
        )
    assert r["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert r["title"] == "Salon purifier"
    assert r["data"] == {"host": "192.168.1.50", "mac": MAC}
    assert r["result"].unique_id == MAC


async def test_user_flow_cannot_connect(hass):
    with patch(f"{P}.config_flow.probe", side_effect=CannotConnect("x")):
        r = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        r = await hass.config_entries.flow.async_configure(
            r["flow_id"], {"host": "192.168.1.50", "name": "P"}
        )
    assert r["type"] == data_entry_flow.FlowResultType.FORM
    assert r["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_changes_host_and_rejects_other_device(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MAC, data={"host": "192.168.0.10", "mac": MAC}
    )
    entry.add_to_hass(hass)
    with patch(
        f"{P}.config_flow.probe",
        return_value={"mac": "11:22:33:44:55:66", "model": None},
    ):
        r = await entry.start_reconfigure_flow(hass)
        r = await hass.config_entries.flow.async_configure(
            r["flow_id"], {"host": "192.168.1.99"}
        )
    assert r["errors"] == {"base": "wrong_device"}

    with patch(
        f"{P}.config_flow.probe", return_value={"mac": MAC, "model": None}
    ), patch(f"{P}.connect", return_value=fake_client()):
        r = await hass.config_entries.flow.async_configure(
            r["flow_id"], {"host": "192.168.1.60"}
        )
        await hass.async_block_till_done()
    assert r["type"] == data_entry_flow.FlowResultType.ABORT
    assert r["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "192.168.1.60"


async def test_setup_retries_when_offline_then_comes_back(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        title="Philips AirPurifier",
        data={"host": "192.168.1.60", "mac": MAC},
    )
    entry.add_to_hass(hass)
    with patch(f"{P}.connect", side_effect=CannotConnect("timeout")):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY

    client = fake_client()
    with patch(f"{P}.connect", return_value=client):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    state = hass.states.get("fan.philips_airpurifier")
    assert state is not None and state.state == "on", state
    assert state.attributes["pm25"] == 7

    # device drops off, then returns: entity goes unavailable and recovers via polling
    ent = hass.data["fan.philips_airpurifier"][0]
    client.get_filters.side_effect = OSError("timed out")
    await ent.async_update_ha_state(True)
    assert hass.states.get("fan.philips_airpurifier").state == "unavailable"
    client.get_filters.side_effect = None
    await ent.async_update_ha_state(True)
    assert hass.states.get("fan.philips_airpurifier").state == "on"

    # custom service still routes to the entity
    await hass.services.async_call(
        DOMAIN,
        "set_child_lock",
        {"entity_id": "fan.philips_airpurifier", "lock": True},
        blocking=True,
    )
    client.set_values.assert_called_with({"cl": True})

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert hass.data["fan.philips_airpurifier"] == []


async def test_yaml_import_without_device(hass):
    with patch(f"{P}.config_flow.probe", side_effect=CannotConnect("offline")), patch(
        f"{P}.connect", side_effect=CannotConnect("offline")
    ):
        assert await async_setup_component(
            hass,
            "fan",
            {"fan": [{"platform": DOMAIN, "host": "192.168.0.5", "name": "Old"}]},
        )
        await hass.async_block_till_done()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1 and entries[0].data["host"] == "192.168.0.5"
    assert entries[0].title == "Old"
    from homeassistant.helpers import issue_registry as ir

    assert ir.async_get(hass).async_get_issue(DOMAIN, "deprecated_yaml")

    # second boot: no duplicate entry
    r = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={"host": "192.168.0.5", "name": "Old"},
    )
    assert r["reason"] == "already_configured"


async def test_request_timeout_applied(hass):
    from pyairctrl import http_client
    from custom_components.philips_airpurifier_http import client as c

    with patch("urllib.request.urlopen") as uo:
        c._patch_request_timeout()
        http_client.urllib.request.urlopen("http://x/")
    assert uo.call_args.args[2] == 5


async def test_ssdp_updates_ip_of_known_purifier_and_offers_new_one(hass):
    from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MAC, data={"host": "192.168.0.10", "mac": MAC}
    )
    entry.add_to_hass(hass)
    info = SsdpServiceInfo(
        ssdp_usn="u",
        ssdp_st="urn:philips-com:device:DiProduct:1",
        ssdp_location="http://192.168.1.77:80/upnp/description.xml",
        upnp={"friendlyName": "Bedroom"},
    )
    with patch(
        f"{P}.config_flow.probe", return_value={"mac": MAC, "model": None}
    ), patch(f"{P}.connect", return_value=fake_client()):
        r = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "ssdp"}, data=info
        )
        await hass.async_block_till_done()
    assert r["reason"] == "already_configured"
    assert entry.data["host"] == "192.168.1.77"

    with patch(
        f"{P}.config_flow.probe",
        return_value={"mac": "11:22:33:44:55:66", "model": None},
    ):
        r = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "ssdp"}, data=info
        )
    assert r["step_id"] == "discovery_confirm"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {})
    assert r["title"] == "Bedroom" and r["data"]["host"] == "192.168.1.77"


async def _loaded_off_fan(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        title="Philips AirPurifier",
        data={"host": "192.168.1.60", "mac": MAC},
    )
    entry.add_to_hass(hass)
    client = fake_client(status={"pwr": "0", "om": "1", "mode": "P", "pm25": 14})
    client.get_firmware.return_value = {"name": "AC2889_10"}
    with patch(f"{P}.connect", return_value=client):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert hass.states.get("fan.philips_airpurifier").state == "off"
    return client


async def test_speed_on_off_purifier_powers_it_on(hass):
    client = await _loaded_off_fan(hass)
    for pct, om in ((40, "1"), (60, "2")):
        await hass.services.async_call(
            "fan",
            "set_percentage",
            {"entity_id": "fan.philips_airpurifier", "percentage": pct},
            blocking=True,
        )
        assert client.set_values.call_args.args[0] == {
            "om": om,
            "pwr": "1",
            "mode": "M",
        }


async def test_turn_on_with_preset_from_off_powers_on_first(hass):
    client = await _loaded_off_fan(hass)
    client.set_values.reset_mock()
    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": "fan.philips_airpurifier", "preset_mode": "auto"},
        blocking=True,
    )
    assert [c.args[0] for c in client.set_values.call_args_list] == [
        {"pwr": "1"},
        {"mode": "P"},
    ]


async def test_preset_and_plain_turn_on_from_off(hass):
    client = await _loaded_off_fan(hass)
    await hass.services.async_call(
        "fan",
        "set_preset_mode",
        {"entity_id": "fan.philips_airpurifier", "preset_mode": "allergen"},
        blocking=True,
    )
    assert [c.args[0] for c in client.set_values.call_args_list[-2:]] == [
        {"pwr": "1"},
        {"mode": "A"},
    ]
    await hass.services.async_call(
        "fan", "turn_on", {"entity_id": "fan.philips_airpurifier"}, blocking=True
    )
    assert client.set_values.call_args.args[0] == {"pwr": "1"}
    await hass.services.async_call(
        "fan",
        "turn_on",
        {"entity_id": "fan.philips_airpurifier", "percentage": 100},
        blocking=True,
    )
    assert client.set_values.call_args.args[0] == {"om": "t", "pwr": "1", "mode": "M"}


async def test_features_exposed_as_entities(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        title="Philips AirPurifier",
        data={"host": "192.168.1.60", "mac": MAC},
    )
    entry.add_to_hass(hass)
    status = {
        "pwr": "1",
        "om": "2",
        "mode": "M",
        "pm25": 9,
        "iaql": 3,
        "aqil": 0,
        "uil": "0",
        "cl": False,
        "dt": 0,
        "dtrs": 0,
        "ddp": "1",
    }
    client = fake_client(status=status)
    with patch(f"{P}.connect", return_value=client):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    def state(entity_id):
        return hass.states.get(entity_id)

    assert state("light.philips_airpurifier_light").state == "off"
    assert state("switch.philips_airpurifier_child_lock").state == "off"
    assert state("switch.philips_airpurifier_display_light").state == "off"
    assert state("select.philips_airpurifier_displayed_index").state == "PM2.5"
    assert state("number.philips_airpurifier_off_timer").state == "0"
    assert state("sensor.philips_airpurifier_pm2_5").state == "9"
    assert state("sensor.philips_airpurifier_allergen_index").state == "3"
    assert state("sensor.philips_airpurifier_hepa_filter").state == "100"
    # humidifier-only features and the wick filter aren't reported by this model
    assert state("select.philips_airpurifier_function") is None
    assert state("select.philips_airpurifier_target_humidity") is None
    assert state("sensor.philips_airpurifier_humidity") is None
    assert state("sensor.philips_airpurifier_wick_filter") is None

    async def call(domain, service, entity_id, **data):
        await hass.services.async_call(
            domain, service, {"entity_id": entity_id, **data}, blocking=True
        )
        return client.set_values.call_args.args[0]

    light = "light.philips_airpurifier_light"
    assert await call("light", "turn_on", light, brightness=128) == {
        "aqil": 50,
        "uil": "1",
    }
    assert await call("light", "turn_on", light) == {"aqil": 100, "uil": "1"}
    assert await call("light", "turn_off", light) == {"aqil": 0, "uil": "0"}
    child_lock = "switch.philips_airpurifier_child_lock"
    assert await call("switch", "turn_on", child_lock) == {"cl": True}
    index = "select.philips_airpurifier_displayed_index"
    assert await call("select", "select_option", index, option="IAI") == {"ddp": "0"}
    timer = "number.philips_airpurifier_off_timer"
    assert await call("number", "set_value", timer, value=3) == {"dt": 3}

    # a poll pushes the purifier's new state to the companion entities
    status.update({"aqil": 75, "cl": True, "dt": 3})
    await hass.data["fan.philips_airpurifier"][0].async_update_ha_state(True)
    assert state(light).state == "on"
    assert state(light).attributes["brightness"] == 191
    assert state(child_lock).state == "on"
    assert state(timer).state == "3"

    # and their availability follows the purifier's
    client.get_filters.side_effect = OSError("timed out")
    await hass.data["fan.philips_airpurifier"][0].async_update_ha_state(True)
    assert state(light).state == "unavailable"
    assert state("sensor.philips_airpurifier_pm2_5").state == "unavailable"
