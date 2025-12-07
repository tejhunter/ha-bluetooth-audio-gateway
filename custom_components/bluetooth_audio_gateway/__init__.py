"""The Bluetooth Audio Gateway integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bluetooth Audio Gateway from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Forward the setup to the media_player platform
    await hass.config_entries.async_forward_entry_setups(entry, ["media_player"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # CORRECTION : Utiliser la méthode correcte async_unload_platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["media_player"])
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok