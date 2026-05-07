# INTENTIONALLY VULNERABLE — AI / training fixture only.
import logging

log = logging.getLogger(__name__)


def record_event(user_msg: str):
    log.warning("event: %s", user_msg)  # unsanitized user input in logs
