from applescript import AppleScript
from .logging import logger
from .macemailapp_applescript import MAIL_APPLESCRIPT

SCRIPT_OBJ = AppleScript(MAIL_APPLESCRIPT)


def run_script(name, *args):
    """Call handler `name` with `*args` from the compiled AppleScript."""
    logger.debug("Running script %s with args %r", name, args)
    return SCRIPT_OBJ.call(name, *args)