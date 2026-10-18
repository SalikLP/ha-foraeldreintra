"""last_success: sættes ved vellykket hentning, flytter sig ikke ved fejl."""
import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from custom_components.foraeldreintra.api import ForaldreIntraAuthError, HomeworkResult
from custom_components.foraeldreintra.coordinator import ForaldreIntraCoordinator


class _FakeClient:
    def __init__(self):
        self.fail_login = False
        self.fail_next_month = False

    async def login(self):
        if self.fail_login:
            raise ForaldreIntraAuthError("Ingen SAML form fundet efter login POST")

    async def get_children(self):
        # Udløbet session: ingen børn → coordinator logger ind igen
        if self.fail_login:
            return []
        return [SimpleNamespace(id="1", name="Barn")]

    async def get_homework_and_days_for_children(self, children):
        items = [{"barn": "Barn", "dato": "2026-10-19", "fag": "Dansk", "tekst": "Læs"}]
        days = {"Barn": [{"dato": "2026-10-19", "raw_text": "Læs", "links": []}]}
        return HomeworkResult(items=items, days=days, complete=not self.fail_next_month)

    async def get_weekplans_for_children(self, children):
        return {}


def _make_coordinator():
    entry = MagicMock(data={"username": "u", "password": "p", "school_url": "https://x"})
    coord = ForaldreIntraCoordinator(hass=MagicMock(), entry=entry)
    coord.client = _FakeClient()
    return coord


class TestLastSuccess:
    def test_set_on_success(self):
        coord = _make_coordinator()
        before = datetime.now().astimezone()
        data = asyncio.run(coord._async_update_data())
        ts = datetime.fromisoformat(data["last_success"])
        assert ts.tzinfo is not None
        assert ts >= before

    def test_unchanged_after_failed_login(self):
        coord = _make_coordinator()
        first = asyncio.run(coord._async_update_data())
        coord.client.fail_login = True
        second = asyncio.run(coord._async_update_data())
        assert second["last_success"] == first["last_success"]
        assert second["items"] == first["items"]

    def test_unchanged_when_next_month_fails(self):
        coord = _make_coordinator()
        first = asyncio.run(coord._async_update_data())
        coord.client.fail_next_month = True
        second = asyncio.run(coord._async_update_data())
        assert second["last_success"] == first["last_success"]
        assert second["days"] == first["days"]
        assert "days_complete" not in second

    def test_none_when_next_month_fails_on_first_fetch(self):
        coord = _make_coordinator()
        coord.client.fail_next_month = True
        data = asyncio.run(coord._async_update_data())
        assert data["last_success"] is None
        assert data["days"]["Barn"]
