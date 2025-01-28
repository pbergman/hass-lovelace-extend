from abc import ABC, abstractmethod
from re import Pattern
from typing import Final
from .const import LOGGER


class CardPropertyMatcher(ABC):
    @abstractmethod
    def match(self, path: str) -> bool:
        pass


class CardPropertyPathMatcher(CardPropertyMatcher):
    def __init__(self, path: str):
        self._path = path

    def match(self, path: str) -> bool:
        return self._path == path

    def __str__(self):
        return self._path


class CardPropertyPatternMatcher(CardPropertyMatcher):
    def __init__(self, regex: Pattern):
        self._regex = regex

    def match(self, path: str) -> bool:
        return self._regex.search(path) is not None

    def __str__(self):
        return f"<{self._regex.pattern}>"


class CardPropertyVoter:
    MATCH_ALL_TYPES:      Final[str] = "*"
    MATCH_NONE:           Final[int] = 0x00
    MATCH_TYPE:           Final[int] = 0x01
    MATCH_PATH:           Final[int] = 0x02
    MATCH_PATH_ALL:       Final[int] = 0x04

    _type: str
    _matcher: CardPropertyMatcher|None = None

    def __init__(self, type: str, matcher: CardPropertyMatcher|None) -> None:
        self._type = type
        self._matcher = matcher

    def __str__(self):
        return f"[{self._type}]{self._matcher}" if self._matcher is not None else f"[{self._type}]"

    def _match_type(self, type: str) -> int:
        return self.MATCH_TYPE if self._type == self.MATCH_ALL_TYPES or self._type == type else self.MATCH_NONE

    def _match_path(self, path: str) -> int:
        if self._matcher is None:
            return self.MATCH_PATH_ALL

        return self.MATCH_PATH if self._matcher.match(path) else self.MATCH_NONE

    def match(self, type: str, path: str) -> int:

        result = (x := self._match_type(type)) | (self._match_path(path) if x is self.MATCH_TYPE else self.MATCH_NONE)

        if 0 < ((self.MATCH_TYPE | self.MATCH_PATH) & result):
            if result == self.MATCH_TYPE and type != self.MATCH_ALL_TYPES:
                return self.MATCH_NONE

        return result


class CardPropertyVoteHandler:
    _voters: [CardPropertyVoter] = []

    def __init__(self, voters: [CardPropertyVoter]):
        self._voters = voters if None is not voters else []

    def register(self, voter: CardPropertyVoter) -> None:
        self._voters.append(voter)

    def __repr__(self):
        return f"[{', '.join(map(lambda card: card.__repr__(), self._voters))}]"

    def is_excluded(self, type: str, path: str) -> int:
        result = CardPropertyVoter.MATCH_NONE

        for voter in self._voters:
            if (result := voter.match(type, path)) is not CardPropertyVoter.MATCH_NONE:
                if CardPropertyVoter.MATCH_PATH_ALL == (CardPropertyVoter.MATCH_PATH_ALL & result):
                    LOGGER.debug(
                        "card type [%s] ignored by rule \"%s\" (match [%s])",
                        type,
                        voter,
                        result_str(result)
                    )
                else:
                    LOGGER.debug(
                        "card path [%s].%s ignored by rule \"%s\" (match [%s])",
                        type,
                        path,
                        voter,
                        result_str(result)
                    )
                return result

        LOGGER.debug("card path [%s].%s not excluded (checked %d voters)", type, path, len(self._voters))

        return result


def result_str(mode: int) -> str:
    ret: list[str] = []

    if CardPropertyVoter.MATCH_TYPE == (CardPropertyVoter.MATCH_TYPE & mode):
        ret.append('type')

    if CardPropertyVoter.MATCH_PATH == (CardPropertyVoter.MATCH_PATH & mode):
        ret.append('path')

    if len(ret) == 0:
        ret.append('none')

    return ', '.join(ret)