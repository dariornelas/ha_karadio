# ha_karadio

Ka-Radio (https://github.com/karawin/Ka-Radio) and Ka-Radio32 https://github.com/karawin/Ka-Radio32 custom integration for Home-Assistant 

## Installation

1. You can install it using HACS or manually.

  1.1. HACS

     [![Add HACS repository.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dariornelas&repository=ha_karadio&category=integration)

    \* or add custom repository `dariornelas/ha_karadio` to HACS with **Type: integration**

  1.2. Manually
     Copy the `custom_components/karadio/` directory to your Home Assistant's `homeassistant/custom_components/` directory.

2. Restart Home Assistant.

## Setup Methods

### Web UI Setup (Recommended)

1. Go to **Settings → Devices & Services**.
2. Click **+ Add integration** (bottom right).
3. Search for "Karadio Media Player".
4. Enter your Karadio's IP address and optionally a custom name.
5. Click **Create**.

### YAML Setup (Legacy)

Add the following to your `configuration.yaml`:

```yaml
media_player:
  - platform: karadio
    host: 192.168.1.253  # Replace with your Karadio IP
    name: Karadio        # Optional, defaults to "Karadio"
```

Restart Home Assistant.

## Features

- Play/Pause (Stop)
- Next/Previous station
- Volume control
- Station selection from a list of available stations
- Manual refresh of station list
- Display current station and track info

## Services

- `karadio.refresh_stations`: Manually refresh the list of available stations
