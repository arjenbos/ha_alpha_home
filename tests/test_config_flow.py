"""Test the Alpha Home config flow."""
import json
from unittest.mock import patch
from homeassistant import config_entries, setup
from custom_components.alpha_innotec.const import DOMAIN
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import load_fixture

from . import MODULE

VALID_CONFIG = {
    "gateway_ip": "127.0.0.1",
    "gateway_password": "verysafe",
    "controller_ip": "127.0.0.2",
    "controller_username": "testing",
    "controller_password": "alsoverysafe"
}

async def test_setup_config(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        target=f"{MODULE}.config_flow.validate_input",
        return_value=json.loads(load_fixture("systeminformation.json")),
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Heatpump"

    mock_setup_entry.assert_called_once()
