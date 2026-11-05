SDK_URL = 'https://github.com/skytr1x/APS-SDK/archive/refs/heads/main.zip'
SOURCE_URL = 'https://github.com/skytr1x/APS-SDK'

MAX_DOWNLOAD = 8 * 1024 * 1024
MAX_FILES = 256
MAX_UNPACKED = 24 * 1024 * 1024

PLUGIN_EXT = '.apl'
TEMP_PREFIX = '.sdk-'

SDK_NAME = 'aps-sdk'
MANIFEST = 'aps-sdk.json'
ABI_VERSION = 1
HOST_VERSION = 1
HOST_PACKAGE = 'aps_host'
HOST_DIR = 'host'

# files an unpacked sdk must contain
REQUIRED_FILES = ('Cargo.toml', 'src/lib.rs', HOST_DIR + '/' + HOST_PACKAGE + '/__init__.py')
