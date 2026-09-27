import json
import logging
import sys
from datetime import datetime, timezone

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.propagate = False
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


def log_event(level: str, event: str, **fields) -> None:
    logger.log(
        logging.getLevelNamesMapping()[level],
        json.dumps({
            "level": level,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": event,
            **fields,
        }),
    )
