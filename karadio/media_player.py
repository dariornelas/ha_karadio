import io
import telnetlib
import re
import logging
import voluptuous as vol
import homeassistant.util as util

from datetime import timedelta

_LOGGER      = logging.getLogger(__name__)

DOMAIN = "karadio"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=2)

from homeassistant.helpers import config_validation as cv

from homeassistant.components.media_player import (
  MediaPlayerDevice,
  PLATFORM_SCHEMA
)

from homeassistant.components.media_player.const import (
  MEDIA_TYPE_CHANNEL,
  SUPPORT_TURN_ON, SUPPORT_TURN_OFF,
  SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_SET,
  SUPPORT_PAUSE, SUPPORT_PLAY, SUPPORT_STOP,
  SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK
  #SUPPORT_SELECT_SOURCE SUPPORT_VOLUME_MUTE, 
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
                  SUPPORT_NEXT_TRACK | SUPPORT_PREVIOUS_TRACK
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
  api = KaradioApi(ip, port, hass)
  add_devices([KaradioDevice(name, max_volume, api)], True)

class KaradioApi():
  def __init__(self, ip, port, hass):
    _LOGGER.info('Initializing KaradioAPI')
    self.hass = hass
    self.ip = ip
    self.port = port

  def _telnet_command(self, command, key = None):
      try:
          if (key):
            telnet = telnetlib.Telnet(self.ip, self.port)
            telnet.write(command.encode('ASCII') + b'\n')
            response = telnet.read_until(b'\r', timeout=1)
            responseString = response.decode('ASCII').strip()
            result = re.findall(key,responseString)
            if (result):
                return result[0]
            else:
                return None
          else:
            telnet = telnetlib.Telnet(self.ip, self.port)
            telnet.write(command.encode('ASCII') + b'\n')
      except IOError as error:
          _LOGGER.error(
              'Command "%s" failed with exception: %s',
              command, repr(error))
      return None

  def get_state(self):
    return  self._telnet_command('cli.info', '##CLI.ICY0#: (.*?)\n')

  def set_state(self, key):
    command = "cli." + key
    return  self._telnet_command(command)

  def get_main_info(self):
    return  self._telnet_command('GetMainInfo')

  def get_volume(self):
    return self._telnet_command('cli.vol', '##CLI.VOL#: (.*?)\n')

  def set_volume(self, volume):
    command = "cli.vol(\"" + str(volume) + "\""
    return  self._telnet_command(command)

  def volume_up(self):
    """Volume up the media player."""
    return  self._telnet_command('cli.vol+')

  def volume_down(self):
    """Volume down media player."""
    return  self._telnet_command('cli.vol-')

  def next_track(self):
    """Send next track command."""
    return  self._telnet_command('cli.next')

  def previous_track(self):
    """Send previous track command."""
    return  self._telnet_command('cli.prev')

  def get_speaker_name(self):
    return  self._telnet_command('GetSpkName', 'spkname')

  # def get_muted(self):
  #   return  self._telnet_command('GetMute', 'mute') == BOOL_ON

  # def set_muted(self, mute):
  #   if mute:
  #     return  self.set_volume(0)
  #   else:
  #     return  self.set_volume(volume)

class KaradioDevice(MediaPlayerDevice):
  def __init__(self, name, max_volume, api):
    _LOGGER.info('Initializing KaradioDevice')
    self._name = name
    self.api = api
    self._state = STATE_OFF
    #self._current_source = None
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
  def state(self):
    return self._state

  @property
  def volume_level(self):
    return self._volume

  def set_volume_level(self, volume):
     self.api.set_volume(volume * self._max_volume)
     self.update()

  # @property
  # def source(self):
  #   return self._current_source

  # @property
  # def source_list(self):
  #   return sorted(MULTI_ROOM_SOURCE_TYPE)

  #  def _select_source(self, source):
  #    self.api.set_source(source)
  #    self._update()

  # @property
  # def is_volume_muted(self):
  #   return self._muted

  # def mute_volume(self, mute):
  #   self._muted = mute
  #   self.api.set_muted(self._muted)
  #   self.update()

  def volume_up(self):
      """Volume up the media player."""
      self.api.volume_up()

  def volume_down(self):
      """Volume down media player."""
      self.api.volume_down()

  def media_next_track(self):
      """Send next track command."""
      self.api.next_track()

  def media_previous_track(self):
      """Send the previous track command."""
      self.api.previous_track()

  def turn_off(self):
      """Turn off media player."""
      self.api.set_state("stop")

  def turn_on(self):
      """Turn on media player."""
      self.api.set_state("start")


  @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
  def update(self):
    _LOGGER.info('Refreshing state...')
    #self._current_source =  self.api.get_source()
    value =  self.api.get_state()
    volume = self.api.get_volume()
    _LOGGER.info(value)
    if (volume):
      self._volume =  int(volume) / self._max_volume
      # if (int(volume) == 0):
      #   self._muted =  BOOL_ON
      # else:
      #   self._muted =  BOOL_OFF

    if value:
      self._state = STATE_PLAYING
    else:
      self._state = STATE_OFF
