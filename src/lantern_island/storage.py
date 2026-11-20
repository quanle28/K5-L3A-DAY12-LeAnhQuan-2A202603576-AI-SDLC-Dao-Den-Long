"""User-local data directory, overridable for tests/export without touching real saves."""
import os
from pathlib import Path


def data_dir():
    return Path(os.environ['LANTERN_DATA_DIR']).expanduser() if os.environ.get('LANTERN_DATA_DIR') else Path.home()/'.lantern_island'
