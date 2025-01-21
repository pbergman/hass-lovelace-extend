from copy import copy
from typing import Self
from .dashboard_card import CardPropertyVoteHandler, CardPropertyVoter

class Path:

    _path_fmt: str | None = None
    _path: list[str]
    _type: str|None
    _voter: CardPropertyVoteHandler|None = None

    def __init__(self, type: str|None, root: str | list, voter: CardPropertyVoteHandler|None = None):
        self._path = [root] if isinstance(root, str) else root
        self._type = type
        self._voter = voter

    def __str__(self) -> str:
        return '.'.join(self._path)

    def new(self, type: str) -> Self:
        return Path(type, [], self._voter)

    def next(self, x: int|str) -> Self:

        paths = copy(self._path)

        if isinstance(x, int):

            if self._path_fmt is None:
                self._path_fmt = self._path[-1] + "[{idx:n}]"

            paths = paths[:-1]
            paths.append(self._path_fmt.format(idx=x))
        else:

            if self._path_fmt is not None:
                self._path_fmt = None

            paths.append(x)

        return Path(self._type, paths, self._voter)

    def get_excluded(self) -> int|None:
        return self._voter.is_excluded(self._type, str(self)) if self._voter is not None else None

    def is_excluded(self) -> bool:
        return self._voter is not None and (
                self._voter.is_excluded(self._type, str(self)) is not CardPropertyVoter.MATCH_NONE
        )
