import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = "abusecode.router"
APP_VERSION = "1.0.0"

DATA_DIR = os.environ.get("ABUSECODE_DATA", os.path.join(BASE_DIR, "data"))
DB_PATH = os.environ.get("ABUSECODE_DB", os.path.join(DATA_DIR, "abusecode.db"))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

UPSTREAM = os.environ.get("OPENCODE_API_BASE", "https://opencode.ai/inference").rstrip("/")
USER_AGENT = os.environ.get(
    "OPENCODE_USER_AGENT",
    "opencode/1.18.35 ai-sdk/provider-utils/4.0.40 runtime/bun/1.3.14",
)
DEFAULT_SESSION = os.environ.get("OPENCODE_SESSION", "")

FAILOVER_STATUS = {401, 403, 429, 500, 502, 503, 504}
MAX_CAPTURE_BYTES = 4_000_000
