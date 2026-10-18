"""Fælles test-hjælpere."""


def notes_page(*days: tuple[str, str]) -> str:
    """Bygger en Lektiebog notes-side (ul.sk-list) ud fra (dato-tekst, indholds-HTML)-par."""
    lis = "".join(
        f"""
        <li>
          <div class="sk-white-box"><b>{dato}:</b></div>
          <div class="sk-user-input">{content}</div>
        </li>"""
        for dato, content in days
    )
    return f'<html><body><ul class="sk-list">{lis}</ul></body></html>'
