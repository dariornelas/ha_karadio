"""Config flow for Karadio integration."""
import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "karadio"

VERSION = '0.1.0'
MINOR_VERSION = '0'

async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{host}/?version", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    raise CannotConnect
                version = await response.text()
    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to karadio: %s", err)
        raise CannotConnect from err

    return {"title": data[CONF_NAME], "version": version.strip()}


class KaradioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Karadio."""


    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                #return self.async_create_entry(title=info["title"], data=user_input)
                return self.async_create_entry(title=info["title"], 
                                               data={
                                                    CONF_HOST: user_input[CONF_HOST], 
                                                    CONF_NAME: user_input[CONF_NAME],
                                                    CONF_ID: user_input[CONF_HOST]
                                                }
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_NAME, default="Karadio"): str,
                }
            ),
            errors=errors,
            description_placeholders={},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
