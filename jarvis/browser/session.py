"""A visible, isolated browser session.

This phase supports only:
- open a public URL
- perform a public web search
- inspect current page state

It does not support logins, form filling, downloads, payments, or browser
profile reuse.
"""

from dataclasses import dataclass
import ipaddress
from urllib.parse import quote_plus, urljoin, urlparse
from playwright.sync_api import sync_playwright


@dataclass(frozen=True)
class BrowserItem:
    index: int
    role: str
    text: str
    href: str = ""


@dataclass(frozen=True)
class BrowserState:
    url: str
    title: str
    visible_text: str
    links: list[BrowserItem]
    buttons: list[BrowserItem]
    inputs: list[BrowserItem]

    def pretty(self):
        lines = [
            f"Title: {self.title or '(no title)'}",
            f"URL: {self.url}",
        ]

        if self.visible_text:
            lines.append(f"Page summary: {self.visible_text}")

        if self.links:
            lines.append("Visible links:")
            for item in self.links:
                suffix = f" -> {item.href}" if item.href else ""
                lines.append(f"  {item.index}. {item.text}{suffix}")

        if self.buttons:
            lines.append("Visible buttons:")
            for item in self.buttons:
                lines.append(f"  {item.index}. {item.text}")

        if self.inputs:
            lines.append("Visible inputs:")
            for item in self.inputs:
                lines.append(f"  {item.index}. {item.text}")

        return "\n".join(lines)


class BrowserSession:
    """One isolated, visible browser session."""

    def __init__(self, cfg):
        settings = cfg["browser"]

        if not settings["enabled"]:
            raise RuntimeError(
                "Browser support is disabled. Set browser.enabled to true "
                "only while testing this phase."
            )

        self.timeout_ms = int(settings["navigation_timeout_seconds"] * 1000)
        self.max_items = settings["max_visible_items"]
        self.headless = settings["headless"]
        self.channel = settings["channel"]

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Launch an isolated browser with no user cookies or saved sessions."""
        if self.page is not None:
            return

        self.playwright = sync_playwright().start()

        launch_options = {
            "headless": self.headless,
        }

        # "chromium" means Playwright's downloaded browser, not personal Chrome.
        if self.channel != "chromium":
            launch_options["channel"] = self.channel

        self.browser = self.playwright.chromium.launch(**launch_options)
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 850},
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)

    def stop(self):
        """Close the isolated browser and discard its temporary session."""
        try:
            if self.context is not None:
                self.context.close()
        finally:
            self.context = None
            self.page = None

        try:
            if self.browser is not None:
                self.browser.close()
        finally:
            self.browser = None

        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None

    def open_url(self, raw_url):
        """Open one public URL and return observed page state."""
        self._require_started()

        url = self._normalize_public_url(raw_url)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        return self.observe()

    def search(self, query):
        """Search the public web through Google and return actual page state."""
        self._require_started()

        query = query.strip()
        if not query:
            raise ValueError("Search query cannot be empty.")

        url = "https://www.google.com/search?q=" + quote_plus(query)
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        return self.observe()

    def follow_link(self, link_index):
        """Navigate to one currently visible, observed public link.

        This deliberately navigates to the link URL instead of blindly clicking
        the page. It blocks javascript:, file:, mailto:, local-network, and
        hidden/unobserved links.
        """
        self._require_started()

        if not isinstance(link_index, int) or link_index < 1:
            raise ValueError("Link index must be a positive integer.")

        links = self._collect_links()
        selected = next(
            (item for item in links if item.index == link_index),
            None,
        )

        if selected is None:
            raise ValueError(
                f"Link {link_index} is not currently visible on this page."
            )

        if not selected.href:
            raise ValueError(
                f"Link {link_index} has no destination URL."
            )

        destination = urljoin(self.page.url, selected.href)
        return self.open_url(destination)

    def observe(self):
        """Read a compact, real DOM-based description of the current page."""
        self._require_started()

        title = self.page.title()
        url = self.page.url

        body_text = self._safe_text(self.page.locator("body"))
        visible_text = " ".join(body_text.split())[:600]

        links = self._collect_links()
        buttons = self._collect_buttons()
        inputs = self._collect_inputs()

        return BrowserState(
            url=url,
            title=title,
            visible_text=visible_text,
            links=links,
            buttons=buttons,
            inputs=inputs,
        )

    def _collect_links(self):
        items = []
        locator = self.page.locator("a:visible")
        count = min(locator.count(), self.max_items)

        for zero_index in range(count):
            node = locator.nth(zero_index)
            text = self._safe_text(node)
            href = node.get_attribute("href") or ""

            if not text:
                text = href or "(unnamed link)"

            items.append(
                BrowserItem(
                    index=zero_index + 1,
                    role="link",
                    text=" ".join(text.split())[:160],
                    href=href[:300],
                )
            )

        return items

    def _collect_buttons(self):
        items = []
        locator = self.page.locator("button:visible, [role='button']:visible")
        count = min(locator.count(), self.max_items)

        for zero_index in range(count):
            node = locator.nth(zero_index)
            text = self._safe_text(node) or node.get_attribute("aria-label") or ""

            if not text:
                text = "(unnamed button)"

            items.append(
                BrowserItem(
                    index=zero_index + 1,
                    role="button",
                    text=" ".join(text.split())[:160],
                )
            )

        return items

    def _collect_inputs(self):
        items = []
        locator = self.page.locator("input:visible, textarea:visible, select:visible")
        count = min(locator.count(), self.max_items)

        for zero_index in range(count):
            node = locator.nth(zero_index)

            label = (
                node.get_attribute("aria-label")
                or node.get_attribute("placeholder")
                or node.get_attribute("name")
                or node.get_attribute("type")
                or "unnamed input"
            )

            items.append(
                BrowserItem(
                    index=zero_index + 1,
                    role="input",
                    text=" ".join(label.split())[:160],
                )
            )

        return items

    @staticmethod
    def _safe_text(locator):
        try:
            return locator.inner_text(timeout=1000)
        except Exception:
            return ""

    def _require_started(self):
        if self.page is None:
            raise RuntimeError("Browser session has not been started.")

    @staticmethod
    def _normalize_public_url(raw_url):
        """Allow only normal public HTTP(S) destinations in Phase 5."""
        raw_url = raw_url.strip()
        if not raw_url:
            raise ValueError("URL cannot be empty.")

        if "://" not in raw_url:
            raw_url = "https://" + raw_url

        parsed = urlparse(raw_url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only public http and https URLs are allowed.")

        host = parsed.hostname
        if not host:
            raise ValueError("URL must contain a hostname.")

        lowered_host = host.casefold()
        if lowered_host == "localhost" or lowered_host.endswith(".local"):
            raise ValueError("Local-network URLs are not allowed.")

        try:
            address = ipaddress.ip_address(host)
            if (
                address.is_private
                or address.is_loopback
                or address.is_link_local
                or address.is_reserved
            ):
                raise ValueError("Private-network URLs are not allowed.")
        except ValueError as error:
            # Hostname is not an IP address. That is normal and permitted.
            if "not allowed" in str(error):
                raise

        return raw_url