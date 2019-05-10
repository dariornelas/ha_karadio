import urllib.parse
import async_timeout
import aiohttp
import asyncio
import re
import math
import logging
import voluptuous as vol
import homeassistant.util as util

from datetime import timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER      = logging.getLogger(__name__)

DOMAIN = "karadio"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=15)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=3)

from homeassistant.helpers import config_validation as cv

from homeassistant.components.media_player import (
  MediaPlayerDevice,
  MEDIA_PLAYER_SCHEMA,
  PLATFORM_SCHEMA
)

from homeassistant.components.media_player.const import (
  MEDIA_TYPE_CHANNEL,
  SUPPORT_TURN_ON, SUPPORT_TURN_OFF,
  SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_SET,
  SUPPORT_PAUSE, SUPPORT_PLAY, SUPPORT_STOP,
  SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK
  #SUPPORT_SELECT_SOURCE
)

from homeassistant.const import (
  CONF_NAME,
  CONF_HOST,
  CONF_PORT,
  STATE_IDLE,
  STATE_PLAYING,
  STATE_OFF
)

DEFAULT_NAME = 'Karadio'
BOOL_OFF = 'off'
BOOL_ON = 'on'
TIMEOUT = 10
SUPPORT_KARADIO = SUPPORT_PAUSE | SUPPORT_PLAY | SUPPORT_STOP |\
                  SUPPORT_VOLUME_SET | SUPPORT_VOLUME_STEP | \
                  SUPPORT_TURN_OFF | SUPPORT_TURN_ON | \
                  SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK
#                  SUPPORT_SELECT_SOURCE

CONF_MAX_VOLUME = 'max_volume'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Required(CONF_HOST, default='127.0.0.1'): cv.string,
  vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
  vol.Optional(CONF_PORT, default='23'): cv.port,
  vol.Optional(CONF_MAX_VOLUME, default='254'): cv.string
})

SCAN_INTERVAL = timedelta(seconds=10)

def setup_platform(hass, config, add_devices, discovery_info=None):
  ip = config.get(CONF_HOST)
  port = config.get(CONF_PORT)
  name = config.get(CONF_NAME)
  max_volume = int(config.get(CONF_MAX_VOLUME))
  session = async_get_clientsession(hass)
  api = KaradioApi(ip, port, session,hass)
  add_devices([KaradioDevice(name, max_volume, api)], True)

class KaradioApi():
  def __init__(self, ip, port, session, hass):
    _LOGGER.info('Initializing KaradioAPI')
    self.session = session
    self.hass = hass
    self.ip = ip
    self.port = port
    self.endpoint = 'http://{0}:{1}'.format(ip, port)

  async def _exec_cmd(self, cmd, key=None):
    url = '{0}?{1}'.format(self.endpoint, cmd)
    _LOGGER.info("Running")
    _LOGGER.info(url)

    with async_timeout.timeout(TIMEOUT, loop=self.hass.loop):
      response = await self.session.get(url)
      data = await response.text()
      if (key is not None):
        result = re.findall(key,data)
        if (result):
          return result[0]
      return None

#  def _telnet_command(self, command, key = None):
#      _LOGGER.info('Initializing telnet command')
#      try:
#          if (key):
#            telnet = telnetlib.Telnet(self.ip, self.port)
#            telnet.write(command.encode('ASCII') + b'\n')
#            response = telnet.read_until(b'\r', timeout=1)
#            responseString = response.decode('ASCII').strip()
#            result = re.findall(key,responseString)
#            if (result):
#                return result[0]
#            else:
#                return None
#          else:
#            telnet = telnetlib.Telnet(self.ip, self.port)
#            telnet.write(command.encode('ASCII') + b'\n')
#      except IOError as error:
#          _LOGGER.error(
#              'Command "%s" failed with exception: %s',
#              command, repr(error))
#      return None

  async def get_state(self):
    return int(await self._exec_cmd('infos', 'sts: (.*?)\n'))

  async def set_command(self, command):
    return await self._exec_cmd(command)

  async def get_volume(self):
    return int(await self._exec_cmd('infos', 'vol: (.*?)\n'))

  async def set_volume(self, volume):
    command = "volume=" + str(volume)
    return await self._exec_cmd(command)

  async def get_media_title(self):
    return str(await self._exec_cmd('infos', 'tit: (.*?)\n'))

#  def get_muted(self):
#    return  self._telnet_command('GetMute', 'mute') == BOOL_ON

#  def set_muted(self, mute):
#    if mute:
#      return  self._telnet_command('SetMute', 'mute', BOOL_ON)
#    else:
#      return  self._telnet_command('SetMute', 'mute', BOOL_OFF)

class KaradioDevice(MediaPlayerDevice):
  def __init__(self, name, max_volume, api):
    _LOGGER.info('Initializing KaradioDevice')
    self._name = name
    self.api = api
    self._state = STATE_OFF
    self._media_title = ''
    self._volume = 0
    self._muted = False
    self._max_volume = max_volume

  @property
  def supported_features(self):
    return SUPPORT_KARADIO

  @property
  def name(self):
    return self._name

  @property
  def media_title(self):
    """Title of current playing media."""
    return self._media_title

  @property
  def state(self):
    return self._state

  @property
  def volume_level(self):
    return self._volume

  async def set_volume_level(self, volume):
     await self.api.set_volume(volume * self._max_volume)
     await self.async_update()

  # @property
  # def source(self):
  #   return self._current_source

  # @property
  # def source_list(self):
  #   return sorted(MULTI_ROOM_SOURCE_TYPE)

  #  def _select_source(self, source):
  #    self.api.set_source(source)
  #    self._update()

#  @property
#  def is_volume_muted(self):
#    return self._muted
#
#  def mute_volume(self, mute):
#    self._muted = mute
#    self.api.set_muted(self._muted)
#    self.update()

  async def volume_up(self):
      """Volume up the media player."""
      await self.set_volume_level(self._volume + 1)

  async def volume_down(self):
      """Volume down media player."""
      await self.set_volume_level(self._volume - 1)

  async def media_next_track(self):
      """Send next track command."""
      await self.api.set_command("next")
      await self.async_update()

  async def media_previous_track(self):
      """Send the previous track command."""
      await self.api.set_command("previous")
      await self.async_update()

  async def turn_off(self):
      """Turn off media player."""
      await self.api.set_command("stop")
      await self.async_update()

  async def turn_on(self):
      """Turn on media player."""
      await self.api.set_command("start")
      await self.async_update()


  async def async_update(self):
    _LOGGER.info('Refreshing state...')
    value =  await self.api.get_state()
    """Check output according to previous state."""
    if (value is None and self._state != STATE_OFF):
      value =  await self.api.get_state()

    """Check if media device is playing."""
    if (value == 1):
      self._state = STATE_PLAYING
      """Check for media device volume"""
      self._volume = '{0:.2f}'.format(await self.api.get_volume() / self._max_volume)
      """Check for media title"""
      self._media_title = await self.api.get_media_title()
    else:
      self._state = STATE_IDLE
      self._media_title = None

   # volume = self.api.get_volume()
   # if (volume is None and self._state != STATE_OFF):
   #   volume =  self.api.get_volume()

   # if (volume):
   #   self._volume =  int(volume) / self._max_volume
      # if (int(volume) == 0):
      #   self._muted =  BOOL_ON
      # else:
      #   self._muted =  BOOL_OFF


