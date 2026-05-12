"""Home Assistant sensors for Nova Poshta — трекінг по ТТН."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, TRACKING_STATUSES
from .coordinator import NovaPoshtaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Створити сенсори Nova Poshta."""
    coordinator: NovaPoshtaCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Чотири фіксованих сенсори — по одному на групу статусів
    async_add_entities([
        NovaPoshtaGroupSensor(
            coordinator, entry,
            key="in_transit",
            name="В дорозі",
            icon="mdi:truck-delivery",
            parcels_attr="in_transit",
        ),
        NovaPoshtaGroupSensor(
            coordinator, entry,
            key="arrived",
            name="Чекає у відділенні",
            icon="mdi:package-down",
            parcels_attr="arrived",
        ),
        NovaPoshtaGroupSensor(
            coordinator, entry,
            key="delivered",
            name="Отримано",
            icon="mdi:package-check",
            parcels_attr="delivered",
        ),
        NovaPoshtaGroupSensor(
            coordinator, entry,
            key="problem",
            name="Потребує уваги",
            icon="mdi:alert-circle-outline",
            parcels_attr="problem",
        ),
    ])


def _format_parcel(p: dict) -> dict[str, Any]:
    """Форматує посилку для атрибутів сенсора."""
    status_code = str(p.get("StatusCode", ""))
    return {
        "ttn":           p.get("Number", ""),
        "status":        TRACKING_STATUSES.get(status_code, p.get("Status", "")),
        "description":   p.get("CargoDescriptionString", ""),
        "sender":        p.get("CounterpartySenderDescription", ""),
        "from":          p.get("CitySender", ""),
        "to":            p.get("CityRecipient", ""),
        "warehouse":     p.get("WarehouseRecipient", ""),
        "weight_kg":     p.get("FactualWeight", p.get("DocumentWeight", "")),
        "cost_uah":      p.get("DocumentCost", ""),
        "announced_uah": p.get("AnnouncedPrice", ""),
        "scheduled":     p.get("ScheduledDeliveryDate", ""),
        "received":      p.get("RecipientDateTime", ""),
        "additional":    p.get("AdditionalInformationEW", ""),
    }


class NovaPoshtaGroupSensor(CoordinatorEntity[NovaPoshtaCoordinator], SensorEntity):
    """Сенсор для групи посилок (в дорозі / у відділенні / отримано / проблема)."""

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: NovaPoshtaCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        parcels_attr: str,
    ) -> None:
        super().__init__(coordinator)
        self._parcels_attr = parcels_attr
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_name = f"Nova Poshta {name}"
        self._attr_device_info = DeviceInfo(
            name=entry.title,
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _parcels(self) -> list[dict]:
        return getattr(self.coordinator, self._parcels_attr, [])

    @property
    def native_value(self) -> int:
        """Кількість посилок у цій групі."""
        return len(self._parcels)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Деталі кожної посилки."""
        return {
            "parcels": [_format_parcel(p) for p in self._parcels],
            "total": len(self._parcels),
        }
