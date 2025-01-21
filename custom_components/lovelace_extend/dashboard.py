from .const import LOGGER
from .dashboard_card import CardPropertyVoter
from .dashboard_config import DashboardConfig
from .path import Path
from ast import literal_eval
from copy import deepcopy
from homeassistant.components.lovelace.const import ConfigNotFound
from homeassistant.components.lovelace.dashboard import (
    _config_info,
    LovelaceConfig,
    CONF_URL_PATH,
    CONFIG_STORAGE_VERSION
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.json import json_bytes, json_fragment
from jinja2.exceptions import TemplateError
from homeassistant.helpers.storage import Store
from homeassistant.helpers.template import is_template_string, TemplateEnvironment
from typing import Any
import asyncio


class LovelaceWrapper(LovelaceConfig):

    _store: Store
    _inner: LovelaceConfig

    def __init__(self, hass: HomeAssistant, inner: LovelaceConfig) -> None:

        self._store = Store[dict[str, Any]](
            hass, CONFIG_STORAGE_VERSION, f"lovelace_extend.{inner.config['id']}"
        )

        self._inner = inner
        self._data: dict[str, Any] | None = None
        self._json: json_fragment | None = None

        config = deepcopy(inner.config)
        config["mode"] = self.mode

        super().__init__(hass, inner.config[CONF_URL_PATH], config)

    @property
    def inner(self) -> LovelaceConfig:
        return self._inner

    async def unwrap(self, clear: bool = True) -> LovelaceConfig:

        if clear:
            await self._remove()

        return self._inner

    @property
    def mode(self) -> str:
        return self._inner.mode + "+"

    async def async_get_info(self):
        return _config_info(self.mode, self._data or await self._load())

    async def async_load(self, force: bool) -> dict[str, Any]:
        if force:
            await self._store.async_remove()
            self._data: dict[str, Any] | None = None
            self._json: json_fragment | None = None

        return self._data or await self._load()

    async def _remove(self):
        await self._store.async_remove()

    async def _load(self) -> dict[str, Any]:
        """Load the config."""
        config = await self._store.async_load()

        if None is config:
            config = await parse__dashboard(self.hass, self._inner)
            await self._store.async_save(config)

        self._data = config

        return self._data

    async def async_json(self, force: bool) -> json_fragment:
        """Return JSON representation of the config."""
        if force:
            await self.async_load(True)

        if self._data is None:
            await self._load()

        return self._json or self._async_build_json()

    @callback
    def _async_build_json(self) -> json_fragment:
        """Build JSON representation of the config."""
        if self._data is None:
            raise ConfigNotFound

        self._json = json_fragment(json_bytes(self._data))

        return self._json


async def parse__dashboard(hass: HomeAssistant, dashboard: LovelaceConfig) -> dict[str, Any]:

    data = deepcopy(await dashboard.async_load(True))
    config = DashboardConfig(data['lovelace_extend'] if 'lovelace_extend' in data else {})
    templating = new_template_environment(hass, config)
    vars = config.vars

    if 'lovelace_extend' in data:
        del data['lovelace_extend']

    for name, var in vars.items():
        vars[name] = await parse_card_value(var, Path(None, []), templating)

    config.vars = vars

    async with asyncio.TaskGroup() as tg:
        for view in data['views']:
            if 'type' in view:
                tg.create_task(parse_card(Path(view['type'], [], config.voter), view, config, templating))

    return data


def new_template_environment(hass: HomeAssistant, config: DashboardConfig) -> TemplateEnvironment:

    environment = TemplateEnvironment(hass, False, False, LOGGER.debug)

    for name, template in config.get_macros():
        try :
            environment.globals[name] = getattr(environment.from_string(template).module, name)
        except TemplateError as err:
            raise HomeAssistantError(f"Error while parsing macro {name} -> {err.message}")

    config.add_sources(environment.loader.sources)

    return environment


async def parse_card(root: Path, options: dict[str, Any], config: DashboardConfig, env: TemplateEnvironment):

    for name, value in options.items():

        vote = root.next(name).get_excluded()

        if vote == CardPropertyVoter.MATCH_TYPE:
            break

        if CardPropertyVoter.MATCH_PATH == (CardPropertyVoter.MATCH_PATH & vote):
            continue

        options[name] = await parse_card_value(value, root.next(name), env, **config.vars)

    for name, value in options.items():
        # check for nested card
        if isinstance(value, dict) and 'type' in value:
            await parse_card(root.new(value['type']), value, config, env)

        # check for nested cards
        if isinstance(value, list) and len(value) > 0 and 'type' in value[0]:
            for i in range(len(value)):
                await parse_card(root.new(options[name][i]['type']), options[name][i], config, env)


async def parse_card_value(data: Any, root: Path, env: TemplateEnvironment, **kwargs: Any) -> Any:

    if isinstance(data, dict):
        # check for card children
        if 'type' in data:
            return data

        for name, value in data.items():
            path = root.next(name)
            if not path.is_excluded():
                data[name] = await parse_card_value(value, path, env, **kwargs)

    if isinstance(data, list):
        for i in range(len(data)):
            if 'type' in data[i]:
                continue
            path = root.next(i)
            if not path.is_excluded():
                data[i] = await parse_card_value(data[i], path, env, **kwargs)

    if isinstance(data, str) and is_template_string(data) and not root.is_excluded():
        try:
            return literal_eval(env.from_string(data).render(**kwargs))
        except TemplateError as err:
            raise HomeAssistantError(f"Error while parsing template on {root} -> {err.message}")

    return data
