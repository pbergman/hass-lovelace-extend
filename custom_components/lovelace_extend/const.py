from typing import Final
import logging

DOMAIN: Final = 'lovelace_extend'
LOGGER: logging.Logger = logging.getLogger(__package__)
CARD_PATH_PATTERN: str = r"^\[(?P<type>[^\]]+)\](?:<(?P<regex>.+)>|(?P<path>.+))?$"
