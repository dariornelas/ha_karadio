# ha_karadio
Ka-Radio (https://github.com/karawin/Ka-Radio) integration for Home-Assistant 

## Installation

HACS
- Add custom repository **dariornelas/ha_karadio** to **HACS**

Manual
- Copy folder **karadio/** to **/homeassistant/custom_components/**
- Edit **/homeassistant/configuration.yaml** and add the integration:
```
media_player:
  - platform: karadio
    host: <karadio host>
```

## Stations
Replace **/homeassistant/custom_components/karadio/WebStations.txt** with your **WebStations.txt** file.
