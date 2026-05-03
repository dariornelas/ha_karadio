"""Karadio Media Player integration for Home Assistant."""
import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Karadio"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Karadio from a config entry."""
    host = config_entry.data[CONF_HOST]
    name = config_entry.data[CONF_NAME]

    entity = KaradioMediaPlayer(hass, host, name)
    async_add_entities([entity])

    async def handle_refresh_stations(call):
        """Handle refresh stations service call."""
        await entity.async_refresh_stations()

    hass.services.async_register("karadio", "refresh_stations", handle_refresh_stations)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the Karadio media player platform."""
    host = config[CONF_HOST]
    name = config[CONF_NAME]

    entity = KaradioMediaPlayer(hass, host, name)
    async_add_entities([entity])

    async def handle_refresh_stations(call):
        """Handle refresh stations service call."""
        await entity.async_refresh_stations()

    hass.services.async_register("karadio", "refresh_stations", handle_refresh_stations)


class KaradioMediaPlayer(MediaPlayerEntity):
    """Representation of a Karadio media player."""

    def __init__(self, hass: HomeAssistant, host: str, name: str) -> None:
        """Initialize the media player."""
        self.hass = hass
        self._host = host
        self._name = name
        self._state = MediaPlayerState.IDLE
        self._volume_level = 0.0
        self._media_title = ""
        self._media_artist = ""
        self._current_station = ""
        self._station_number = 0
        self._available = True
        self._source_list = []
        self._stations_fetched = False

    @property
    def name(self) -> str:
        """Return the name of the player."""
        return self._name

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        return self._state

    @property
    def volume_level(self) -> float:
        """Return the volume level."""
        return self._volume_level

    @property
    def media_title(self) -> str:
        """Return the title of current playing media."""
        return self._media_title

    @property
    def media_artist(self) -> str:
        """Return the artist of current playing media."""
        return self._media_artist

    @property
    def source(self) -> str:
        """Return the current source."""
        return self._current_station

    @property
    def source_list(self) -> list[str]:
        """Return the list of available sources."""
        return [name for _, name in self._source_list]

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the supported features."""
        return (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self._available

    async def async_update(self) -> None:
        """Update the state of the player."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self._host}/?infos") as response:
                    if response.status == 200:
                        data = await response.text()
                        self._parse_infos(data)
                        self._available = True
                    else:
                        self._available = False

            if not self._stations_fetched:
                await self._fetch_stations()
                self._stations_fetched = True
        except aiohttp.ClientError:
            self._available = False

    def _parse_infos(self, data: str) -> None:
        """Parse the infos response."""
        lines = data.strip().split('\n')
        for line in lines:
            if line.startswith('vol:'):
                vol = int(line.split(':')[1].strip())
                self._volume_level = vol / 254.0
            elif line.startswith('num:'):
                self._station_number = int(line.split(':')[1].strip())
            elif line.startswith('stn:'):
                self._current_station = line.split(':', 1)[1].strip()
            elif line.startswith('tit:'):
                title = line.split(':', 1)[1].strip()
                # Assuming format "ARTIST - TITLE"
                if ' - ' in title:
                    self._media_artist, self._media_title = title.split(' - ', 1)
                else:
                    self._media_title = title
                    self._media_artist = ""
            elif line.startswith('sts:'):
                sts = int(line.split(':')[1].strip())
                if sts == 1:
                    self._state = MediaPlayerState.PLAYING
                else:
                    self._state = MediaPlayerState.IDLE

    async def async_media_play(self) -> None:
        """Play media."""
        await self._send_command("start")

    async def async_media_stop(self) -> None:
        """Stop media."""
        await self._send_command("stop")

    async def async_media_next_track(self) -> None:
        """Next track."""
        await self._send_command("next")

    async def async_media_previous_track(self) -> None:
        """Previous track."""
        await self._send_command("prev")

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        vol_int = int(volume * 254)
        await self._send_command(f"volume={vol_int}")

    async def async_volume_up(self) -> None:
        """Volume up."""
        current_vol = int(self._volume_level * 254)
        new_vol = min(current_vol + 10, 254)
        await self._send_command(f"volume={new_vol}")

    async def async_select_source(self, source: str) -> None:
        """Select a source."""
        for num, name in self._source_list:
            if name == source:
                await self._send_command(f"play={num}")
                break
        else:
            _LOGGER.warning("Source %s not found in source list", source)

    async def _fetch_stations(self) -> None:
        """Fetch the list of stations."""
        self._source_list = []
        try:
            async with aiohttp.ClientSession() as session:
                for i in range(255):
                    async with session.get(f"http://{self._host}/?list={i}") as response:
                        if response.status == 200:
                            name = await response.text()
                            name = name.strip()
                            if name:
                                self._source_list.append((i, name))
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching stations: %s", err)

    async def async_refresh_stations(self) -> None:
        """Refresh the list of stations."""
        await self._fetch_stations()
        self._stations_fetched = True

    async def _send_command(self, command: str) -> None:
        """Send a command to the radio."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{self._host}/?{command}") as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to send command %s", command)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error sending command %s: %s", command, err)