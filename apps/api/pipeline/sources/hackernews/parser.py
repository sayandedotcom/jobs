import re
from html.parser import HTMLParser


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("p", "br", "li"):
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts).strip()


def hn_html_to_plain(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


def normalize_plain_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    normalized: list[str] = []
    previous_blank = False

    for line in lines:
        if not line:
            if normalized and not previous_blank:
                normalized.append("")
            previous_blank = True
            continue

        normalized.append(line)
        previous_blank = False

    return "\n".join(normalized).strip()


def extract_header_line(text: str) -> str:
    for line in text.splitlines():
        header_line = re.sub(r"^[\s\-•*|]+", "", line).strip()
        if header_line:
            return header_line
    return ""
