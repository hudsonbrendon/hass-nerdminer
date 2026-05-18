# NerdMiner — Home Assistant Integration

Track your [NerdMiner V2](https://github.com/BitMaker-hub/NerdMiner_v2) solo Bitcoin miner stats in Home Assistant via the [Public-Pool](https://web.public-pool.io) API.

## Features

- Hashrate (kH/s)
- Session shares accepted
- Best difficulty (chance of finding a block)
- Workers count
- Session start time
- Online/offline binary sensor

## Installation

### HACS (recommended)

1. Add this repo as a custom repository in HACS (Integrations → ⋮ → Custom repositories).
2. Search "NerdMiner" → Download.
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → "NerdMiner".

### Manual

```bash
cd ~/.homeassistant
git clone https://github.com/hudsonbrendon/hass-nerdminer
cp -r hass-nerdminer/custom_components/nerdminer custom_components/
```

Restart HA and add the integration via Settings.

## Configuration

You only need your **Bitcoin payout address** (the one configured on the miner). Example: `bc1qddj…`

## Sensors created

| Entity | Description |
|--------|-------------|
| `sensor.nerdminer_<addr>_hashrate` | Current hashrate (kH/s) |
| `sensor.nerdminer_<addr>_best_difficulty` | Best difficulty ever found by this address |
| `sensor.nerdminer_<addr>_session_accepted` | Shares accepted this session |
| `sensor.nerdminer_<addr>_session_difficulty` | Current pool difficulty |
| `sensor.nerdminer_<addr>_workers_count` | Active workers |
| `sensor.nerdminer_<addr>_start_time` | Session start timestamp |
| `binary_sensor.nerdminer_<addr>_online` | True when at least one worker is reporting |

## Example automations

### Notify on block found (lottery!)

```yaml
automation:
  - alias: "NerdMiner — block found"
    trigger:
      - platform: numeric_state
        entity_id: sensor.nerdminer_<addr>_best_difficulty
        above: 100000000
    action:
      - service: notify.mobile_app_phone
        data:
          title: "Bitcoin block found!"
          message: "Difficulty: {{ trigger.to_state.state }}"
```

### Alert when offline

```yaml
automation:
  - alias: "NerdMiner — offline alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.nerdminer_<addr>_online
        to: "off"
        for: "00:10:00"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Miner offline for 10 minutes."
```

## Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## License

MIT
