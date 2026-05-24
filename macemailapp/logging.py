import logging
import os

logger = logging.getLogger("macemailapp")
_level = os.environ.get("MACEMAILAPP_LOG", "WARNING").upper()
logger.setLevel(getattr(logging, _level, logging.WARNING))
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(name)s %(levelname)s: %(message)s"))
    logger.addHandler(_handler)