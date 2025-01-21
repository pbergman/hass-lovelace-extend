from .const import LOGGER, DOMAIN
from .dashboard import LovelaceWrapper
from homeassistant.components.lovelace import _register_panel
from homeassistant.components.lovelace.const import DOMAIN as LOVELACE_DOMAIN, MODE_YAML
from homeassistant.components.lovelace.dashboard import LovelaceConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    LOGGER.debug("lovelace extend component removed, reverting all managed dashboards")
    await async_synchronize_dashboards(hass, None)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    LOGGER.info("initializing component lovelace extend.")
    # Overwrite/handle selected dashboards
    await async_synchronize_dashboards(hass, entry)
    # Register listener for updated config
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    LOGGER.debug("disable all dashboard overlays because component is turned-off")
    await async_synchronize_dashboards(hass, None)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Reload entry if options change."""
    LOGGER.info("config entry updated, recheck dashboards")
    await hass.config_entries.async_reload(entry.entry_id)
    await async_synchronize_dashboards(hass, entry)


async def async_synchronize_dashboards(hass: HomeAssistant, entry: ConfigEntry|None) -> None:
    if 'dashboards' in hass.data[DOMAIN]:
        for dashboard in hass.data[DOMAIN]['dashboards']:
            if entry is None or 'dashboards' not in entry.data or dashboard not in entry.data['dashboards']:
                item = hass.data[LOVELACE_DOMAIN]['dashboards'].get(dashboard, None)
                if isinstance(item, LovelaceWrapper) and item is not None:
                    LOGGER.info("reverting dashboard \"%s\" to original config", dashboard)
                    hass.data[LOVELACE_DOMAIN]['dashboards'][dashboard] = await item.unwrap()
                    if hass.data[LOVELACE_DOMAIN]['dashboards'][dashboard].mode != MODE_YAML:
                        await register_panel(hass, hass.data[LOVELACE_DOMAIN]['dashboards'][dashboard])
                elif item is None:
                    LOGGER.info("dashboard %s seems to be removed from lovelace collection")
                else:
                    LOGGER.info("dashboard %s was not extended")

    if entry is not None and 'dashboards' in entry.data:
        for dashboard in entry.data['dashboards']:
            if 'dashboards' not in hass.data[DOMAIN] or dashboard not in hass.data[DOMAIN]['dashboards']:
                inner = hass.data[LOVELACE_DOMAIN]['dashboards'].get(dashboard, None)
                if not isinstance(inner, LovelaceWrapper) and inner is not None:
                    LOGGER.info("extending dashboard \"%s\"", dashboard)
                    hass.data[LOVELACE_DOMAIN]['dashboards'][dashboard] = LovelaceWrapper(hass, inner)
                    # update panel to yaml, so we disable the edit mode and can refresh/rebuild from gui
                    if inner.mode != MODE_YAML:
                        await register_panel(hass, hass.data[LOVELACE_DOMAIN]['dashboards'][dashboard], MODE_YAML)
                elif inner is None:
                    del entry.data['dashboards'][dashboard]
                    LOGGER.info("dashboard %s seems to be removed from lovelace collection")
                else:
                    LOGGER.info("dashboard %s already managed", dashboard)

    hass.data[DOMAIN] = entry.data if entry is not None else {}


async def register_panel(hass: HomeAssistant, conf: LovelaceConfig, mode: str|None = None) -> None:
    _register_panel(hass, conf.url_path, (mode if mode is not None else conf.mode), conf.config, True)