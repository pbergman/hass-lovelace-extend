from .const import CARD_PATH_PATTERN
from .dashboard_card import (
    CardPropertyMatcher,
    CardPropertyPathMatcher,
    CardPropertyPatternMatcher,
    CardPropertyVoteHandler,
    CardPropertyVoter,
)
from homeassistant.helpers import config_validation as cv
from re import compile, Pattern
from typing import Any
from voluptuous import Schema, Optional, Required, Invalid


class DashboardConfig:

    _pattern: Pattern
    _data: dict[str, Any]

    def __init__(self, config: dict[str, Any], card_patter: Pattern = CARD_PATH_PATTERN):
        self._pattern = compile(card_patter)
        self._data = self._config_schema(config)

    def _card_path_voter(self, value) -> CardPropertyVoteHandler:

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            Invalid(f"expecting list got {type(value)}")

        voter = CardPropertyVoteHandler(None)

        for v in value:
            voter.register(Schema(self._card_property_matcher)(v))

        return voter

    def _card_property_matcher(self, value: str) -> CardPropertyVoter:

        regex = self._pattern.match(value)

        if regex is None:
            raise Invalid(f"Invalid card path \"{value}\", expecting [card-type]path|<regex>")

        group: dict = regex.groupdict()
        match: CardPropertyMatcher|None = None

        if group['regex'] is not None:
            try:
                match = CardPropertyPatternMatcher(compile(group['regex']))
            except Exception as e:
                raise Invalid(f"Invalid card path pattern \"{group['regex']}\" ({e.__str__()})")

        if group['path'] is not None:
            match = CardPropertyPathMatcher(group['path'])

        return CardPropertyVoter(group['type'], match)

    @staticmethod
    def _slug_name(my_key) -> str:
        return Schema(cv.slug)(my_key)

    def _macro_value(self, data) -> dict[str, str|list]:
        if isinstance(data, str):
            data = {
                'content': data
            }

        return self._macro_schema(data)

    @property
    def _macro_schema(self) -> Schema:
        return Schema({
            Optional('args', default=[]): cv.ensure_list_csv,
            Required('content'):          cv.string,
        })

    @property
    def _config_schema(self) -> Schema:
        return Schema({
            Optional('vars'):                           dict[str, str | int | bool | list | dict],
            Optional('excludes', default=['[*]type']):  self._card_path_voter,
            Optional('templates'):                      {
                self._slug_name: str
            },
            Optional('macros'):                         {
                self._slug_name: self._macro_value
            },
        })

    @property
    def voter(self) -> CardPropertyVoteHandler:
        return self._data['excludes']

    @property
    def vars(self) -> dict[str, Any]|None:
        return self._data['vars'] if 'vars' in self._data else {}

    @vars.setter
    def vars(self, value: dict[str, Any]):
        self._data['vars'] = value

    @property
    def templates(self) -> dict[str, str]:
        return self._data['templates'] if 'templates' in self._data else {}

    @property
    def macros(self) -> dict[str, dict[str, str]]:
        return self._data['macros'] if 'macros' in self._data else {}

    def add_sources(self, source: dict[str, str]):
        for name, template in self.templates.items():
            source[name] = template

    def get_macros(self):
        for name, macro in self.macros.items():
            yield name, f"{{% macro {name}({', '.join(macro['args'])}) %}}{macro['content']}{{% endmacro %}}"