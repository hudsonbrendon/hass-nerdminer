"""Constants for the NerdMiner integration."""

DOMAIN = "nerdminer"
DEFAULT_SCAN_INTERVAL = 30  # seconds
API_BASE_URL = "https://public-pool.io:40557/api/client"
CONF_BTC_ADDRESS = "btc_address"
CONF_SCAN_INTERVAL = "scan_interval"

# Attribution shown in HA UI
ATTRIBUTION = "Data provided by Public-Pool"

# Entity keys (used as unique_id suffixes)
SENSOR_HASHRATE = "hashrate"
SENSOR_BEST_DIFFICULTY = "best_difficulty"
SENSOR_SESSION_ACCEPTED = "session_accepted"
SENSOR_SESSION_DIFFICULTY = "session_difficulty"
SENSOR_WORKERS_COUNT = "workers_count"
SENSOR_START_TIME = "start_time"
BINARY_SENSOR_ONLINE = "online"
