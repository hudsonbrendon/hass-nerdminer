# NerdMiner — Home Assistant Integration

[![tests](https://github.com/hudsonbrendon/hass-nerdminer/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/hass-nerdminer/actions/workflows/tests.yml)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Track your [NerdMiner V2](https://github.com/BitMaker-hub/NerdMiner_v2) solo Bitcoin miner stats in Home Assistant via the [Public-Pool](https://web.public-pool.io) API.

<p align="center">
  <img src="https://asicmarketplace.com/wp-content/uploads/2025/05/NERDminer-150.webp" alt="NerdMiner V2" width="320">
</p>

## What it does

NerdMiner V2 is a solo Bitcoin "lottery" miner — it tries to find a block on its own, and if it does, you keep the entire reward (~3 BTC + fees). This integration pulls stats from the pool the miner reports to and turns them into Home Assistant entities you can chart, alert on, and automate against.

## Features

- **6 sensors**: hashrate, best difficulty, session shares accepted, session difficulty, workers count, session start time
- **1 binary sensor**: online/offline (connectivity device class)
- **UI config flow** — no YAML required
- **Options flow** — adjust polling interval (10-3600 seconds)
- **Translations**: English + Portuguese (Brazil)
- **HACS-ready**

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS** → **Integrations**
2. Click the **3-dot menu** (top right) → **Custom repositories**
3. Add the repository:
   - **URL**: `https://github.com/hudsonbrendon/hass-nerdminer`
   - **Category**: `Integration`
4. Click **Add**
5. Search "NerdMiner" in HACS → **Download**
6. **Restart Home Assistant**

### Manual

```bash
cd /config  # your HA config directory
mkdir -p custom_components
git clone https://github.com/hudsonbrendon/hass-nerdminer.git
cp -r hass-nerdminer/custom_components/nerdminer custom_components/
```

Then restart Home Assistant.

## Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **NerdMiner**
3. Enter your **Bitcoin payout address** — the same address configured on the miner (the one you typed into the captive portal at `192.168.4.1` when setting up the device).

   Example: `bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02`

4. The integration validates the address against Public-Pool, then creates the device with 7 entities.

To change the polling interval afterwards: **Settings** → **Devices & Services** → **NerdMiner** → **Configure**.

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.nerdminer_<addr>_hashrate` | Sensor | Current hashrate in kH/s |
| `sensor.nerdminer_<addr>_best_difficulty` | Sensor | Best difficulty ever found by this address |
| `sensor.nerdminer_<addr>_session_accepted` | Sensor | Shares accepted in the current session |
| `sensor.nerdminer_<addr>_session_difficulty` | Sensor | Current pool difficulty |
| `sensor.nerdminer_<addr>_workers_count` | Sensor | Active workers reporting to the pool |
| `sensor.nerdminer_<addr>_start_time` | Sensor (timestamp) | When the current mining session started |
| `binary_sensor.nerdminer_<addr>_online` | Binary | `on` when at least one worker is reporting |

## Example automations

### Notify if you found a block

```yaml
automation:
  - alias: "NerdMiner — block candidate!"
    trigger:
      - platform: numeric_state
        entity_id: sensor.nerdminer_<addr>_best_difficulty
        above: 100000000
    action:
      - service: notify.mobile_app_phone
        data:
          title: "Bitcoin block candidate!"
          message: "Best difficulty reached: {{ trigger.to_state.state }}"
```

### Alert when the miner goes offline

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
          message: "NerdMiner has been offline for 10 minutes."
```

### Daily hashrate snapshot

```yaml
automation:
  - alias: "NerdMiner — daily snapshot"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.mobile_app_phone
        data:
          message: >
            Hashrate: {{ states('sensor.nerdminer_<addr>_hashrate') }} kH/s ·
            Shares: {{ states('sensor.nerdminer_<addr>_session_accepted') }} ·
            Best: {{ states('sensor.nerdminer_<addr>_best_difficulty') }}
```

## Dashboard card

A minimal Lovelace card:

```yaml
type: entities
title: NerdMiner
entities:
  - entity: binary_sensor.nerdminer_<addr>_online
    name: Status
  - entity: sensor.nerdminer_<addr>_hashrate
    name: Hashrate
  - entity: sensor.nerdminer_<addr>_session_accepted
    name: Shares (session)
  - entity: sensor.nerdminer_<addr>_best_difficulty
    name: Best difficulty
  - entity: sensor.nerdminer_<addr>_start_time
    name: Session start
```

## Limitations

- Data comes from Public-Pool's REST API, polled every 30 seconds by default.
- "Workers" only appear in the API while the miner is actively submitting shares — expect short gaps as `offline` when the miner reconnects.
- This integration only supports the **Public-Pool** pool (`public-pool.io`). The miner can point to other pools, but the integration won't pick those up.

## Development

```bash
git clone https://github.com/hudsonbrendon/hass-nerdminer.git
cd hass-nerdminer
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# run tests
pytest -v --cov=custom_components.nerdminer

# lint
ruff check custom_components tests
```

The test suite uses `pytest-homeassistant-custom-component`. 18 tests, ~95% coverage.

## Contributing

Issues and PRs welcome. If you have a different NerdMiner setup (other pool, other hardware variant) and want it supported, open an issue describing the JSON API response from your pool and I'll see what's feasible.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

- [BitMaker-hub/NerdMiner_v2](https://github.com/BitMaker-hub/NerdMiner_v2) — the firmware and hardware design.
- [Public-Pool](https://web.public-pool.io) — solo mining pool that ships the API this integration depends on.
- Photo credit: [ASIC Marketplace](https://asicmarketplace.com).
