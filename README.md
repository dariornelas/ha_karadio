# ha_karadio
Ka-Radio (https://github.com/karawin/Ka-Radio) integration for Home-Assistant 

## Installation

You can install it using HACS or manually.

HACS
- [![Add HACS repository.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dariornelas&repository=ha_karadio&category=integration)
  
or
- Add custom repository **dariornelas/ha_karadio** to **HACS** with **Type: integration**
- Edit **/homeassistant/configuration.yaml** to add the integration:
```
media_player:
  - platform: karadio
    host: <karadio host>
```
- Restart Home-Assistant

Manually
- Copy folder **karadio/** to **/homeassistant/custom_components/**
- Edit **/homeassistant/configuration.yaml** to add the integration:
```
media_player:
  - platform: karadio
    host: <karadio host>
```
- Restart Home-Assistant

## Configuration
Replace **/homeassistant/custom_components/karadio/WebStations.txt** with your **WebStations.txt** file.
