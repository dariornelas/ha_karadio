import io
import telnetlib
import re
import logging
import voluptuous as vol
import homeassistant.util as util

from datetime import timedelta

_LOGGER      = logging.getLogger(__name__)

DOMAIN = "karadio"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=3)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)

from homeassistant.helpers import config_validation as cv

from homeassistant.components.media_player import (
  MediaPlayerDevice,
  PLATFORM_SCHEMA
)

from homeassistant.components.media_player.const import (
  MEDIA_TYPE_CHANNEL,
  SUPPORT_TURN_ON, SUPPORT_TURN_OFF,
  SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET,
  SUPPORT_PAUSE, SUPPORT_PLAY, SUPPORT_STOP
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
                  SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
                  SUPPORT_TURN_OFF
#                  SUPPORT_SELECT_SOURCE

CONF_MAX_VOLUME = 'max_volume'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Required(CONF_HOST, default='127.0.0.1'): cv.string,
  vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
  vol.Optional(CONF_PORT, default='23'): cv.port,
  vol.Optional(CONF_MAX_VOLUME, default='100'): cv.string
})

SCAN_INTERVAL = timedelta(seconds=10)


def setup_platform(hass, config, add_devices, discovery_info=None):
  ip = config.get(CONF_HOST)
  port = config.get(CONF_PORT)
  name = config.get(CONF_NAME)
  max_volume = int(config.get(CONF_MAX_VOLUME))
  #session = _get_clientsession(hass)
  api = KaradioApi(ip, port, hass)
  add_devices([KaradioDevice(name, max_volume, api)], True)

class KaradioApi():
  def __init__(self, ip, port, hass):
    self.hass = hass
    self.ip = ip
    self.port = port
    #self.endpoint = 'http://{0}:{1}'.format(ip, port)

  def _telnet_command(self, command, key):
      try:
          telnet = telnetlib.Telnet(self._resource, self._port)
          telnet.write(command.encode('ASCII') + b'\r')
          response = telnet.read_until(b'\r', timeout=0.2)
          responseString = response.decode('ASCII').strip()
          return re.findall(key,responseString)
      except IOError as error:
          _LOGGER.error(
              'Command "%s" failed with exception: %s',
              command, repr(error))
      return None

  #  def _exec_cmd(self, cmd, key_to_extract):
  #   import xmltodict
  #   query = urllib.parse.urlencode({ "cmd": cmd }, quote_via=urllib.parse.quote)
  #   url = '{0}/UIC?{1}'.format(self.endpoint, query)

  #   with _timeout.timeout(TIMEOUT, loop=self.hass.loop):
  #     _LOGGER.debug("Executing: {} with cmd: {}".format(url, cmd))
  #     response =  self.session.get(url)
  #     data =  response.text()
  #     _LOGGER.debug(data)
  #     response = xmltodict.parse(data)
  #     if key_to_extract in response['UIC']['response']:
  #       return response['UIC']['response'][key_to_extract]
  #     else:
  #       return None

  #  def _exec_get(self, action, key_to_extract):
  #   return  self._exec_cmd('<name>{0}</name>'.format(action), key_to_extract)

  #  def _exec_set(self, action, property_name, value):
  #   if type(value) is str:
  #     value_type = 'str'
  #   else:
  #     value_type = 'dec'
  #   cmd = '<name>{0}</name><p type="{3}" name="{1}" val="{2}"/>'.format(action, property_name, value, value_type)
  #   return  self._exec_cmd(cmd, property_name)

  def get_state(self):
    return self._telnet_command('cli.info', '##CLI.PLAYING(.?)')

  def set_state(self, key):
    return  self._telnet_command('SetPowerStatus', 'powerStatus', key)

  def get_main_info(self):
    return  self._telnet_command('GetMainInfo')

  def get_volume(self):
    return int( self._telnet_command('cli.info', '##CLI.VOL#: (.*?)\n'))

  def set_volume(self, volume):
    return  self._telnet_command('SetVolume', 'volume', int(volume))

  def get_speaker_name(self):
    return  self._telnet_command('GetSpkName', 'spkname')

  def get_muted(self):
    return  self._telnet_command('GetMute', 'mute') == BOOL_ON

  def set_muted(self, mute):
    if mute:
      return  self._telnet_command('SetMute', 'mute', BOOL_ON)
    else:
      return  self._telnet_command('SetMute', 'mute', BOOL_OFF)

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

  def _set_volume_level(self, volume):
     self.api.set_volume(volume * self._max_volume)
     self._update()

  # @property
  # def source(self):
  #   return self._current_source

  # @property
  # def source_list(self):
  #   return sorted(MULTI_ROOM_SOURCE_TYPE)

  #  def _select_source(self, source):
  #    self.api.set_source(source)
  #    self._update()

  @property
  def is_volume_muted(self):
    return self._muted

  def _mute_volume(self, mute):
    self._muted = mute
    self.api.set_muted(self._muted)
    self._update()

  def turn_off(self):
      """Turn off media player."""
      self.api.set_state(0)

  def turn_on(self):
      """Turn on media player."""
      self.api.set_state(1)

  @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
  def _update(self):
    _LOGGER.info('Refreshing state...')
    #self._current_source =  self.api.get_source()
    self._volume =  self.api.get_volume() / self._max_volume
    self._muted =  self.api.get_muted()
    value =  self.api.get_state()
    if value :
      self._state = STATE_PLAYING
    else:
      self._state = STATE_OFF
