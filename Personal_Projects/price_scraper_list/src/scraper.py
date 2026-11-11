import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.config import PROJECT_ROOT, AppConfig, ZoneConfig
from src.database import PriceDatabase
from src.parser import ProductParser

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PRODUCT_SELECTOR = '[data-qa^="product-item-cpgs-"]'
STORE_PAGE_SELECTOR = '[data-qa^="product-item-"]'
DEBUG_DIR = PROJECT_ROOT / "logs" / "debug"
CATALOG_QUERY = "[catalogo tienda]"   # search_query value for rows scraped from a store's own pages

# A run is "degraded" (exit code 2) when this share of queries returns nothing,
# or when this share of cards could only be read by the text fallback parser.
DEGRADED_EMPTY_RATIO = 0.5
DEGRADED_FALLBACK_RATIO = 0.5

# Runs in the browser. Rappi groups search results per store; every product
# wrapper carries data-qa="product-item-cpgs-<storeId>_<productId>" and the
# store header carries data-qa="store-item-cpgs-<storeId>".
EXTRACT_JS = r"""
() => {
  const stores = {};
  document.querySelectorAll('[data-qa^="store-item-cpgs-"]').forEach(a => {
    const id = a.getAttribute('data-qa').replace('store-item-cpgs-', '');
    const first = (a.innerText || '').split('\n').map(s => s.trim()).filter(Boolean)[0] || null;
    const slug = ((a.getAttribute('href') || '').split('/')[2] || '').replace(/^\d+-/, '');
    stores[id] = { name: first, slug };
  });
  const txt = (root, qa) => {
    const el = root.querySelector(`[data-qa="${qa}"]`);
    return el ? el.textContent.trim() : null;
  };
  const out = [];
  document.querySelectorAll('[data-qa^="product-item-cpgs-"]').forEach(w => {
    const m = w.getAttribute('data-qa').match(/^product-item-cpgs-(\d+)_(\d+)$/);
    if (!m) return;
    const img = w.querySelector('img[alt]');
    out.push({
      store_id: m[1],
      product_id: m[2],
      store_name: (stores[m[1]] || {}).name,
      store_slug: (stores[m[1]] || {}).slug,
      name: txt(w, 'product-name') || (img ? img.getAttribute('alt') : null),
      price: txt(w, 'product-price'),
      real_price: txt(w, 'product-real-price'),
      discount: txt(w, 'product-discount'),
      pum: txt(w, 'product-pum'),
      text: w.innerText || '',
    });
  });
  return out;
}
"""

# Store sections of a search page in display order (= rank), with the header
# text that holds delivery time and fee, e.g. ['Puppis', 'Hoy, 5 PM', '•', '$ 6.000'].
STORES_JS = r"""
() => [...document.querySelectorAll('[data-qa^="store-item-cpgs-"]')].map((a, i) => {
  const id = a.getAttribute('data-qa').replace('store-item-cpgs-', '');
  const sec = document.querySelector(`[data-testid="search-result-cpgs-${id}"]`);
  const header = sec ? (sec.innerText || '').split('\n').map(s => s.trim()).filter(Boolean).slice(0, 8) : [];
  const first = (a.innerText || '').split('\n').map(s => s.trim()).filter(Boolean)[0] || null;
  return { rank: i + 1, store_id: id, name: first,
           slug: ((a.getAttribute('href') || '').split('/')[2] || '').replace(/^\d+-/, ''), header };
})
"""

# Product cards on a store's own pages carry data-qa="product-item-<productId>".
STORE_PAGE_JS = r"""
() => {
  const txt = (root, qa) => { const el = root.querySelector(`[data-qa="${qa}"]`); return el ? el.textContent.trim() : null; };
  const out = [];
  document.querySelectorAll('[data-qa^="product-item-"]').forEach(w => {
    const m = w.getAttribute('data-qa').match(/^product-item-(\d+)$/);
    if (!m) return;
    const img = w.querySelector('img[alt]');
    out.push({ product_id: m[1], name: txt(w, 'product-name') || (img ? img.getAttribute('alt') : null),
               price: txt(w, 'product-price'), real_price: txt(w, 'product-real-price'),
               discount: txt(w, 'product-discount'), pum: txt(w, 'product-pum'), text: w.innerText || '' });
  });
  return out;
}
"""

STORE_LINKS_JS = (
    "(root) => [...document.querySelectorAll(`a[href^='${root}/']`)]"
    ".map(a => a.getAttribute('href').split('?')[0])"
)


@dataclass
class RunResult:
    saved: int = 0
    queries: int = 0
    cards: int = 0
    fallback_cards: int = 0
    failed: List[str] = field(default_factory=list)
    empty: List[str] = field(default_factory=list)

    @property
    def degraded_reasons(self) -> List[str]:
        reasons = []
        bad = len(self.failed) + len(self.empty)
        if self.queries and bad / self.queries >= DEGRADED_EMPTY_RATIO:
            reasons.append(f"{bad}/{self.queries} queries returned no products or failed")
        if self.cards and self.fallback_cards / self.cards >= DEGRADED_FALLBACK_RATIO:
            reasons.append(
                f"{self.fallback_cards}/{self.cards} cards needed the text fallback parser "
                "(Rappi data-qa markup probably changed)"
            )
        return reasons

    @property
    def exit_code(self) -> int:
        if self.saved == 0:
            return 1
        return 2 if self.degraded_reasons else 0


def store_display_name(raw: Dict[str, Any]) -> str:
    if raw.get("store_name"):
        return raw["store_name"]
    slug = raw.get("store_slug") or ""
    return slug.replace("-", " ").title() if slug else f"Store {raw['store_id']}"


def parse_store_header(header: List[str]) -> Dict[str, Optional[str]]:
    """['Puppis', 'Hoy, 5 PM', '•', '$ 6.000', 'Ir a la tienda'] -> eta / fee text."""
    rest = [h for h in header[1:] if h != "•"]
    fee = next((h for h in rest if h.startswith("$") or "gratis" in h.lower()), None)
    eta = next((h for h in rest if h != fee and re.search(r"\d", h) and not h.startswith("$")), None)
    return {"eta_text": eta, "fee_text": fee}


def raw_to_record(raw: Dict[str, Any], base: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Converts one browser-extracted card into a DB record (None if unparseable).
    The record carries `_fallback=True` when the structured fields were missing
    and the raw-text heuristics had to be used.
    """
    parsed = ProductParser.parse_product(
        raw.get("name"), raw.get("price"), raw.get("real_price"),
        raw.get("discount"), raw.get("pum"), raw.get("text") or "",
    )
    fallback = parsed is None
    if fallback:  # markup changed? fall back to raw text heuristics
        lines = [l.strip() for l in (raw.get("text") or "").splitlines() if l.strip()]
        parsed = ProductParser.parse_card(lines)
    if parsed is None:
        return None
    return {
        "_fallback": fallback,
        **base,
        "store_id": raw["store_id"],
        "store_name": store_display_name(raw),
        "product_id": raw["product_id"],
        **parsed.model_dump(),
    }


class RappiScraper:
    def __init__(self, config: AppConfig, db: Optional[PriceDatabase] = None):
        self.config = config
        self.settings = config.scraper
        self.db = db or PriceDatabase(config.database_file)

    # ------------------------------------------------------------- helpers
    def run_stamp(self) -> Dict[str, Any]:
        local_now = self.config.local_now()
        iso = local_now.isocalendar()
        return {
            "snapshot_date": local_now.date().isoformat(),
            "week_id": f"{iso.year}-W{iso.week:02d}",
            "extracted_at": datetime.now(timezone.utc).replace(tzinfo=None),
        }

    def zone_base(self, zone: ZoneConfig, stamp: Dict[str, Any]) -> Dict[str, Any]:
        return {**stamp, "country": self.config.country.upper(), "city": zone.city,
                "zone_id": zone.id, "zone": zone.name}

    async def new_zone_page(self, browser: Browser, zone: ZoneConfig) -> Tuple[BrowserContext, Page]:
        context = await browser.new_context(
            user_agent=USER_AGENT, locale="es-CO",
            geolocation={"latitude": zone.lat, "longitude": zone.lng}, permissions=["geolocation"],
        )
        await context.add_cookies([zone.to_rappi_cookie(self.config.cookie_domain)])
        return context, await context.new_page()

    async def _goto(self, page: Page, url: str):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.settings.navigation_timeout_ms)
        except Exception as e:  # keep going; the SPA often renders anyway
            print(f"    navigation warning: {e.__class__.__name__}: {str(e).splitlines()[0]}")

    async def _scroll_until_stable(self, page: Page, selector: str) -> int:
        previous = -1
        for _ in range(self.settings.max_scroll_rounds):
            count = await page.locator(selector).count()
            if count == previous:
                break
            previous = count
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
        return await page.locator(selector).count()

    async def _load_results(self, page: Page, url: str) -> int:
        await self._goto(page, url)
        try:
            await page.wait_for_selector(PRODUCT_SELECTOR, timeout=self.settings.results_timeout_ms)
        except Exception:
            return 0
        return await self._scroll_until_stable(page, PRODUCT_SELECTOR)

    async def _dump_debug(self, page: Page, zone: ZoneConfig, query: str):
        """Saves HTML + screenshot of a page that yielded no products."""
        try:
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            slug = re.sub(r"[^a-z0-9]+", "-", query.lower())[:60]
            stem = f"{datetime.now():%Y%m%d_%H%M%S}_{zone.id}_{slug}"
            (DEBUG_DIR / f"{stem}.html").write_text(await page.content(), encoding="utf-8")
            await page.screenshot(path=str(DEBUG_DIR / f"{stem}.png"), full_page=True)
            print(f"    debug page saved: logs/debug/{stem}.html/.png")
        except Exception as e:
            print(f"    could not save debug page: {e}")

    # -------------------------------------------------------------- search
    async def scrape_zone_query(
        self, page: Page, zone: ZoneConfig, query: str, base: Dict[str, Any],
        result: Optional[RunResult] = None,
    ) -> List[dict]:
        """Runs one search, stores the store ranking, returns the relevant product records."""
        url = f"{self.config.base_url}/search?query={urllib.parse.quote_plus(query)}"
        print(f"[{zone.name}] '{query}' -> {url}")

        cards = 0
        for attempt in range(self.settings.retries + 1):
            cards = await self._load_results(page, url)
            if cards:
                break
            if attempt < self.settings.retries:
                print("    no product cards yet, retrying...")
                await page.wait_for_timeout(3000)
        if not cards:
            await self._dump_debug(page, zone, query)
            return []

        stores = await page.evaluate(STORES_JS)
        self.db.insert_store_ranks([
            {**base, "search_query": query, "rank": s["rank"], "store_id": s["store_id"],
             "store_name": store_display_name({"store_name": s["name"], "store_slug": s["slug"],
                                               "store_id": s["store_id"]}),
             **parse_store_header(s["header"])}
            for s in stores
        ])

        raw_cards = await page.evaluate(EXTRACT_JS)
        base = {**base, "search_query": query}
        records, skipped, fallback, irrelevant = [], 0, 0, 0
        for raw in raw_cards:
            rec = raw_to_record(raw, base)
            if not rec:
                skipped += 1
                continue
            fallback += rec.pop("_fallback")
            if ProductParser.is_relevant(query, rec["product_name"]):
                records.append(rec)
            else:
                irrelevant += 1
        if result is not None:
            result.cards += len(raw_cards)
            result.fallback_cards += fallback
        n_stores = len({r["store_id"] for r in records})
        print(f"    {len(raw_cards)} cards, {len(records)} kept from {n_stores} stores"
              + (f", {irrelevant} unrelated to the query" if irrelevant else "")
              + (f", {skipped} unparseable" if skipped else "")
              + (f", {fallback} via text fallback" if fallback else ""))
        if raw_cards and skipped == len(raw_cards):
            await self._dump_debug(page, zone, query)
        return records

    # ------------------------------------------------------- store catalog
    async def scrape_store_catalog(
        self, page: Page, zone: ZoneConfig, store_id: str, slug: str, store_name: str,
        base: Dict[str, Any], max_pages: int = 40,
    ) -> List[dict]:
        """Crawls a store's home, aisles and sub-aisles and returns every listed product."""
        root = f"/tiendas/{slug}"
        queue, seen, raw_by_id = [root], set(), {}
        while queue and len(seen) < max_pages:
            path = queue.pop(0)
            if path in seen:
                continue
            seen.add(path)
            await self._goto(page, self.config.base_url + path)
            try:
                await page.wait_for_selector(STORE_PAGE_SELECTOR, timeout=self.settings.results_timeout_ms)
            except Exception:
                pass
            await self._scroll_until_stable(page, STORE_PAGE_SELECTOR)
            for raw in await page.evaluate(STORE_PAGE_JS):
                raw_by_id.setdefault(raw["product_id"], raw)
            links = await page.evaluate(STORE_LINKS_JS, root)
            # aisles (/tiendas/<slug>/<aisle>) and sub-aisles (/<aisle>/<sub>) only
            queue += [l for l in links if l not in seen and l.count("/") <= 4]
            await page.wait_for_timeout(800)

        base = {**base, "search_query": CATALOG_QUERY}
        records = []
        for raw in raw_by_id.values():
            rec = raw_to_record({**raw, "store_id": store_id, "store_name": store_name}, base)
            if rec:
                rec.pop("_fallback", None)
                records.append(rec)
        print(f"[{zone.name}] catalog of {store_name}: {len(records)} products from {len(seen)} pages")
        return records

    # ------------------------------------------------------------- runs
    async def search_queries(self, zone: ZoneConfig, queries: List[str], headless: bool = True) -> RunResult:
        """Ad-hoc searches in one zone (used for per-product price lookups)."""
        base = self.zone_base(zone, self.run_stamp())
        result = RunResult()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            try:
                context, page = await self.new_zone_page(browser, zone)
                try:
                    for i, query in enumerate(queries, 1):
                        result.queries += 1
                        print(f"  ({i}/{len(queries)})", end=" ")
                        try:
                            records = await self.scrape_zone_query(page, zone, query, base, result)
                        except Exception as e:
                            print(f"    ERROR: {e.__class__.__name__}: {e}")
                            result.failed.append(query)
                            continue
                        if not records:
                            result.empty.append(query)
                        result.saved += self.db.insert_snapshots(records)
                        await page.wait_for_timeout(self.settings.delay_between_queries_ms)
                finally:
                    await context.close()
            finally:
                await browser.close()
        return result

    async def probe_visibility(self, zone: ZoneConfig, store_id: str, store_slug: str, queries: List[str],
                               headless: bool = True) -> List[dict]:
        """
        Hourly visibility check (ADR-013): does her store page open, and where does
        Rappi list her store for each search. Returns probe rows; writes nothing.
        """
        from src import probe
        base = probe.stamp(self.config.local_now().replace(tzinfo=None), zone.id)
        rows = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            try:
                context, page = await self.new_zone_page(browser, zone)
                try:
                    await self._goto(page, f"{self.config.base_url}/tiendas/{store_slug}")
                    try:
                        await page.wait_for_selector(STORE_PAGE_SELECTOR, timeout=self.settings.results_timeout_ms)
                    except Exception:
                        pass
                    products = await page.locator(STORE_PAGE_SELECTOR).count()
                    rows.append(probe.store_page_row(base, products, page.url))
                    print(f"  store page: {products} products" + ("" if products else f" (now at {page.url})"))
                    for query in queries:
                        await page.wait_for_timeout(self.settings.delay_between_queries_ms)
                        url = f"{self.config.base_url}/search?query={urllib.parse.quote_plus(query)}"
                        try:
                            cards = await self._load_results(page, url)
                            if not cards:
                                await page.wait_for_timeout(3000)
                                cards = await self._load_results(page, url)
                            stores = await page.evaluate(STORES_JS) if cards else []
                        except Exception as e:
                            print(f"  '{query}': ERROR {e.__class__.__name__}")
                            stores = []
                        row = probe.search_row(base, query, stores, store_id, parse_store_header)
                        rows.append(row)
                        print(f"  '{query}': {row['n_stores']} stores, "
                              + (f"her store #{row['her_rank']}" if row["her_rank"] else "her store not listed"))
                finally:
                    await context.close()
            finally:
                await browser.close()
        return rows

    async def run(
        self,
        zone_filter: Optional[str] = None,
        query_filter: Optional[str] = None,
        headless: bool = True,
    ) -> RunResult:
        stamp = self.run_stamp()
        zones = self.config.zones
        if zone_filter:
            zf = zone_filter.lower()
            zones = [z for z in zones if z.id.lower() == zf or zf in z.name.lower()]
            if not zones:
                raise ValueError(f"No zone found matching '{zone_filter}'")

        result = RunResult()
        client = self.config.client
        print(f"Snapshot {stamp['snapshot_date']} ({stamp['week_id']}) | zones={len(zones)}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            try:
                for zone in zones:
                    queries = [query_filter] if query_filter else self.config.queries_for(zone)
                    print(f"\n=== Zone: {zone.name} ({zone.city}) | {len(queries)} queries ===")
                    context, page = await self.new_zone_page(browser, zone)
                    base = self.zone_base(zone, stamp)
                    zone_saved = 0
                    try:
                        for query in queries:
                            label = f"{zone.id}:{query}"
                            result.queries += 1
                            try:
                                records = await self.scrape_zone_query(page, zone, query, base, result)
                            except Exception as e:
                                print(f"    ERROR: {e.__class__.__name__}: {e}")
                                result.failed.append(label)
                                continue
                            if not records:
                                print("    WARNING: no products found")
                                result.empty.append(label)
                            # Persist after every query so a crash never loses a whole run
                            zone_saved += self.db.insert_snapshots(records)
                            await page.wait_for_timeout(self.settings.delay_between_queries_ms)
                        if client and client.zone_id == zone.id and not query_filter:
                            try:
                                catalog = await self.scrape_store_catalog(
                                    page, zone, client.store_id, client.store_slug, client.name, base)
                                zone_saved += self.db.insert_snapshots(catalog)
                            except Exception as e:
                                print(f"    ERROR scraping client catalog: {e.__class__.__name__}: {e}")
                                result.failed.append(f"{zone.id}:{CATALOG_QUERY}")
                    finally:
                        await context.close()
                    print(f"[{zone.name}] saved {zone_saved} snapshots")
                    result.saved += zone_saved
            finally:
                await browser.close()

        print(f"\nFinished. Snapshots saved/updated: {result.saved}")
        if result.empty:
            print(f"Queries with no results: {', '.join(result.empty)}")
        if result.failed:
            print(f"Queries that failed: {', '.join(result.failed)}")
        for reason in result.degraded_reasons:
            print(f"DEGRADED RUN: {reason}")
        return result
