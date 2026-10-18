"""days hentes fra både notes/{id} og notes/{id}/NextMonth; items kun fra notes/{id}."""
import asyncio

from custom_components.foraeldreintra.api import Child, ForaldreIntraClient, ForaldreIntraError

BASE = "https://skole.example"
DIARY_URL = f"{BASE}/parent/1/Barnitem/weeklyplansandhomework/diary"
NOTES_URL = f"{DIARY_URL}/notes/291"
NEXT_MONTH_URL = f"{NOTES_URL}/NextMonth"


def _notes_page(*days):
    lis = "".join(
        f'<li><div class="sk-white-box"><b>{dato}:</b></div>'
        f'<div class="sk-user-input">{content}</div></li>'
        for dato, content in days
    )
    return f'<html><body><ul class="sk-list">{lis}</ul></body></html>'


PAGES = {
    DIARY_URL: '<a href="/parent/1/Barnitem/weeklyplansandhomework/diary/291">Lektiebog</a>',
    NOTES_URL: _notes_page(
        ("Mandag, 19. okt. 2026", "<p><strong>Dansk:</strong> Læs side 10.</p>"),
        ("Tirsdag, 20. okt. 2026", "<p>Glosetest</p>"),
    ),
    NEXT_MONTH_URL: _notes_page(
        ("Tirsdag, 20. okt. 2026", "<p>Glosetest flyttet til fredag</p>"),
        ("Mandag, 26. okt. 2026", "<p>Husk idrætstøj</p>"),
    ),
}


def _client(pages):
    client = ForaldreIntraClient(session=None, username="u", password="p", school_url=BASE)
    fetched = []

    async def fake_get_text(url):
        fetched.append(url)
        if url not in pages:
            raise ForaldreIntraError(f"HTTP 500 for {url}")
        return pages[url]

    client._get_text = fake_get_text
    return client, fetched


def _run(client):
    return asyncio.run(client.get_homework_and_days_for_children([Child(id="1", name="Barn")]))


class TestNextMonthDays:
    def test_days_merge_current_and_next_month(self):
        client, fetched = _client(PAGES)
        _items, days = _run(client)
        assert NEXT_MONTH_URL in fetched
        assert [(d["dato"], d["raw_text"]) for d in days["Barn"]] == [
            ("2026-10-19", "**Dansk:** Læs side 10."),
            ("2026-10-20", "Glosetest flyttet til fredag"),
            ("2026-10-26", "Husk idrætstøj"),
        ]

    def test_items_only_from_current_period(self):
        client, _ = _client(PAGES)
        items, _days = _run(client)
        assert {i["dato"] for i in items} == {"2026-10-19", "2026-10-20"}

    def test_failed_next_month_falls_back_to_current(self):
        pages = {k: v for k, v in PAGES.items() if k != NEXT_MONTH_URL}
        client, _ = _client(pages)
        items, days = _run(client)
        assert [d["raw_text"] for d in days["Barn"]] == ["**Dansk:** Læs side 10.", "Glosetest"]
        assert items
