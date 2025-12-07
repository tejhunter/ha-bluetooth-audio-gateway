"""Config flow for Bluetooth Audio Gateway."""
import logging
import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data):
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data.get(CONF_PORT, DEFAULT_PORT)
    
    # Test connection to the add-on API
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(5):
                async with session.get(f"http://{host}:{port}/api/status") as resp:
                    if resp.status != 200:
                        raise CannotConnect("API non disponible")
                    result = await resp.json()
                    if result.get("status") != "ok":
                        raise CannotConnect("Réponse API invalide")
    except Exception as err:
        raise CannotConnect(f"Impossible de se connecter: {err}")
    
    return {"title": f"Bluetooth Audio Gateway ({host})"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bluetooth Audio Gateway."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
        
        # Show the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="localhost"): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }),
            errors=errors
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""