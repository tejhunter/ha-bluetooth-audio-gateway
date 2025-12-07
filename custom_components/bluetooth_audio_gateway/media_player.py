"""Media player support for Bluetooth Audio Gateway."""
import logging
import aiohttp
import async_timeout
from datetime import timedelta

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    host = config_entry.data[CONF_HOST]
    port = config_entry.data.get(CONF_PORT, 3000)
    
    coordinator = BluetoothAudioGatewayCoordinator(hass, host, port)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([BluetoothAudioGatewayMediaPlayer(coordinator, host, port)])

class BluetoothAudioGatewayCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from the add-on."""
    
    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Bluetooth Audio Gateway",
            update_interval=timedelta(seconds=10),
        )
        self.host = host
        self.port = port
        self.devices = []
        self.connected_device = None
    
    async def _async_update_data(self):
        """Fetch data from the add-on."""
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(5):
                    async with session.get(f"http://{self.host}:{self.port}/api/devices") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                self.devices = data.get("devices", [])
                                # Find connected device
                                for device in self.devices:
                                    if device.get("connected"):
                                        self.connected_device = device
                                        return self.connected_device
                                self.connected_device = None
                                return None
                            else:
                                raise UpdateFailed(f"API error: {data.get('error')}")
                        else:
                            raise UpdateFailed(f"HTTP error: {resp.status}")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

class BluetoothAudioGatewayMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a Bluetooth Audio Gateway media player."""
    
    def __init__(self, coordinator, host, port):
        """Initialize the media player."""
        super().__init__(coordinator)
        self._host = host
        self._port = port
        self._attr_name = "Bluetooth Audio Gateway"
        self._attr_unique_id = f"{DOMAIN}_{host}_{port}"
        
        # Supported features
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY_MEDIA |
            MediaPlayerEntityFeature.SELECT_SOURCE |
            MediaPlayerEntityFeature.TURN_ON |
            MediaPlayerEntityFeature.TURN_OFF
        )
        
        # Initial state
        self._attr_state = MediaPlayerState.OFF
        self._attr_source_list = []
    
    @property
    def state(self):
        """Return the state of the player."""
        if self.coordinator.connected_device:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF
    
    @property
    def source_list(self):
        """Return the list of available sources (Bluetooth devices)."""
        return [device["name"] for device in self.coordinator.devices]
    
    @property
    def source(self):
        """Return the current source (connected device)."""
        if self.coordinator.connected_device:
            return self.coordinator.connected_device["name"]
        return None
    
    async def async_select_source(self, source):
        """Select a Bluetooth device to connect to."""
        # Find device by name
        device = None
        for dev in self.coordinator.devices:
            if dev["name"] == source:
                device = dev
                break
        
        if device:
            try:
                async with aiohttp.ClientSession() as session:
                    async with async_timeout.timeout(30):
                        async with session.post(
                            f"http://{self._host}:{self._port}/api/connect",
                            json={"address": device["address"]}
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if not data.get("success"):
                                    _LOGGER.error(f"Failed to connect: {data.get('error')}")
                            else:
                                _LOGGER.error(f"HTTP error: {resp.status}")
            except Exception as err:
                _LOGGER.error(f"Error connecting to device: {err}")
            
            # Refresh data
            await self.coordinator.async_request_refresh()
    
    async def async_play_media(self, media_type, media_id, **kwargs):
        """Play media from a URL or TTS."""
        # For now, we'll just implement TTS via a simple method
        # This will be expanded later
        _LOGGER.info(f"Would play media: {media_id} of type {media_type}")
        
        # Here you would:
        # 1. Download the audio file (if URL)
        # 2. Send it to your add-on to play on Bluetooth speaker
        # This requires additional API endpoints in your add-on
    
    async def async_turn_on(self):
        """Turn the media player on."""
        # Connect to the first available device
        if self.coordinator.devices:
            await self.async_select_source(self.coordinator.devices[0]["name"])
    
    async def async_turn_off(self):
        """Turn the media player off."""
        # Disconnect from current device
        if self.coordinator.connected_device:
            try:
                async with aiohttp.ClientSession() as session:
                    async with async_timeout.timeout(10):
                        async with session.post(
                            f"http://{self._host}:{self._port}/api/disconnect",
                            json={"address": self.coordinator.connected_device["address"]}
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if not data.get("success"):
                                    _LOGGER.error(f"Failed to disconnect: {data.get('error')}")
                            else:
                                _LOGGER.error(f"HTTP error: {resp.status}")
            except Exception as err:
                _LOGGER.error(f"Error disconnecting device: {err}")
            
            # Refresh data
            await self.coordinator.async_request_refresh()