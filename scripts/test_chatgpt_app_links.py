#!/usr/bin/env python3
"""Offline regression checks for ChatGPT app links in the built site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


SITE = Path(__file__).resolve().parent.parent / "site"
CHATGPT_URL = "https://chatgpt.com/plugins/plugin_asdk_app_6aef6b89f90481919a4b2260f5bb14d1"
CHATGPT_LINE = "Also inside ChatGPT: check any page from a chat."


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.words = []
        self.link = None
        self.hidden = ""
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden = tag
        if tag == "a":
            self.link = (dict(attrs), [])

    def handle_endtag(self, tag):
        if tag == self.hidden:
            self.hidden = ""
        if tag == "a" and self.link is not None:
            attrs, words = self.link
            self.links.append((attrs, " ".join(" ".join(words).split())))
            self.link = None

    def handle_data(self, data):
        if not self.hidden:
            self.words.append(data)
            if self.link is not None:
                self.link[1].append(data)


def main():
    assistants = SITE / "ai-assistants/index.html"
    raw = assistants.read_text(encoding="utf-8")
    assert raw.count(CHATGPT_URL) == 1, "AI assistants must contain the exact ChatGPT URL once"
    page = Page(raw)
    links = [(attrs, text) for attrs, text in page.links if attrs.get("href") == CHATGPT_URL]
    assert len(links) == 1, "the ChatGPT URL must be a link"
    attrs, text = links[0]
    assert text == "Add Check Engine to ChatGPT", text
    assert "btn" in attrs.get("class", "").split(), "use the existing button style"
    assert attrs.get("rel") == "noopener", attrs
    assert attrs.get("target", "_self") == "_self", "open ChatGPT in the same tab"
    assert "Use it inside ChatGPT" in " ".join(page.words)

    for relative in ("index.html", "download/index.html"):
        page = Page((SITE / relative).read_text(encoding="utf-8"))
        links = [attrs for attrs, text in page.links if text == CHATGPT_LINE]
        assert len(links) == 1, f"{relative}: show the ChatGPT line once"
        assert links[0].get("href") == "/ai-assistants/", relative

    count = 0
    for path in SITE.rglob("*.html"):
        for attrs, text in Page(path.read_text(encoding="utf-8")).links:
            hostname = urlsplit(attrs.get("href", "")).hostname or ""
            if hostname == "chatgpt.com" or hostname.endswith(".chatgpt.com"):
                assert path == assistants, f"unexpected ChatGPT link in {path.relative_to(SITE)}"
                assert attrs["href"] == CHATGPT_URL, attrs["href"]
                count += 1
    assert count == 1, "only the AI assistants page may link to ChatGPT"
    print("CHATGPT APP LINKS ok: one app link, two internal links, same tab, no tracking parameters")


if __name__ == "__main__":
    main()
