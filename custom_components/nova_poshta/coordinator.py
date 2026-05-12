"""DataUpdateCoordinator for the Nova Poshta integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.httpx_client import get_async_client

import httpx
from novaposhta.client import NovaPoshtaApi, InvalidAPIKeyError, APIRequestError

from .const import (
    API_KEY,
    DOMAIN,
    HTTP_TIMEOUT,
    PHONE,
    TRACKING_NUMBERS,
    UPDATE_INTERVAL,
    STATUSES_IN_TRANSIT,
    STATUSES_ARRIVED,
    STATUSES_DELIVERED,
    STATUSES_PROBLEM,
)

_LOGGER = logging.getLogger(__name__)


class NovaPoshtaCoordinator(DataUpdateCoordinator[list[dict]]):
    """Nova Poshta Coordinator — трекає посилки через getStatusDocuments."""

    def __init__(self, data: dict[str, Any], hass: HomeAssistant) -> None:
        """Initialize."""
        self._api_key = data[API_KEY]
        self._phone = data[PHONE]
        self._tracking_numbers: list[str] = data[TRACKING_NUMBERS]

        async_http_client = AsyncHttpClientWrapper(get_async_client(hass))
        self._client = NovaPoshtaApi(
            self._api_key,
            timeout=HTTP_TIMEOUT,
            async_mode=True,
            raise_for_errors=True,
            http_client=async_http_client,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def async_shutdown(self) -> None:
        """Close the client."""
        await super().async_shutdown()
        await self._client.close_async()

    async def _send(self, client_lambda) -> Any:
        try:
            return await client_lambda()
        except httpx.HTTPError as err:
            raise ConnectionError from err
        except InvalidAPIKeyError as err:
            raise InvalidAuth from err
        except APIRequestError as err:
            raise ConnectionError from err

    async def async_validate_input(self) -> None:
        """Перевіряє що API ключ валідний."""
        await self._send(self._client.common.get_cargo_types)

    def update_tracking_numbers(self, ttns: list[str]) -> None:
        """Оновити список ТТН (викликається з options flow)."""
        self._tracking_numbers = ttns

    async def _async_update_data(self) -> list[dict]:
        """Отримати статуси всіх відстежуваних посилок."""
        if not self._tracking_numbers:
            return []

        # getStatusDocuments приймає до 100 ТТН за раз
        all_parcels: list[dict] = []
        chunks = [
            self._tracking_numbers[i:i + 100]
            for i in range(0, len(self._tracking_numbers), 100)
        ]

        for chunk in chunks:
            documents = [
                {"DocumentNumber": ttn, "Phone": self._phone}
                for ttn in chunk
            ]
            try:
                result = await self._send(
                    lambda d=documents: self._client.tracking_document.get_status_documents(
                        documents=d
                    )
                )
                if result and result.get("data"):
                    all_parcels.extend(result["data"])
            except ConnectionError as err:
                raise UpdateFailed(f"Помилка підключення до Nova Poshta API: {err}") from err

        _LOGGER.debug("Nova Poshta: отримано %d посилок", len(all_parcels))
        return all_parcels

    @property
    def parcels(self) -> list[dict]:
        """Всі посилки з останнього оновлення."""
        return self.data or []

    def parcels_by_status(self, status_codes: tuple[str, ...]) -> list[dict]:
        """Фільтрує посилки за групою статусів."""
        return [
            p for p in self.parcels
            if str(p.get("StatusCode", "")) in status_codes
        ]

    @property
    def in_transit(self) -> list[dict]:
        """Посилки в дорозі (статуси 4, 5, 6)."""
        return self.parcels_by_status(STATUSES_IN_TRANSIT)

    @property
    def arrived(self) -> list[dict]:
        """Посилки у відділенні — чекають забрати (статуси 7, 8)."""
        return self.parcels_by_status(STATUSES_ARRIVED)

    @property
    def delivered(self) -> list[dict]:
        """Отримані посилки (статус 9)."""
        return self.parcels_by_status(STATUSES_DELIVERED)

    @property
    def problem(self) -> list[dict]:
        """Проблемні посилки (статуси 10, 11, 12)."""
        return self.parcels_by_status(STATUSES_PROBLEM)


class AsyncHttpClientWrapper:
    def __init__(self, client):
        self._client = client

    def AsyncClient(self, *args, **kwargs):
        return self._client


class InvalidAuth(HomeAssistantError):
    """Невірний API ключ."""
