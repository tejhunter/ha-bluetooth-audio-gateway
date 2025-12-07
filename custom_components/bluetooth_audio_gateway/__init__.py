"""The Bluetooth Audio Gateway integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bluetooth Audio Gateway from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # CORRECTION : Appeler directement async_forward_entry_setups avec await
    await hass.config_entries.async_forward_entry_setups(entry, ["media_player"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Mise à jour pour correspondre à la nouvelle API (avec 's')
    unload_ok = await hass.config_entries.async_unload_entry_setups(entry, ["media_player"])
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)  # Utilisation de .pop avec valeur par défaut pour sécurité
    
    return unload_ok