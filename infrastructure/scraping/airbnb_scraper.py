"""
Airbnb scraper using Playwright headless browser.

Paginates through all search result pages (~18 listings per page) to capture
the full inventory for a region. Uses network interception, __NEXT_DATA__
parsing, and DOM extraction as layered fallbacks.
"""

from __future__ import annotations

import asyncio
import json
import random
import re

from playwright.async_api import Page, Response, async_playwright

from core.logging import logger
from infrastructure.scraping.browser import create_stealth_browser
from infrastructure.scraping.models import ScrapedListing, classify_property_type

# Maximum pages to scrape (safety cap)
MAX_PAGES = 35


class AirbnbScraper:
    """Scrapes Airbnb listings with full pagination."""

    def __init__(self, center_lat: float, center_lng: float, radius_km: float):
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.radius_km = radius_km

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape_listings(self) -> list[ScrapedListing]:
        logger.info(
            "Scraping Airbnb around (%.4f, %.4f) r=%.1f km",
            self.center_lat, self.center_lng, self.radius_km,
        )

        all_listings: list[ScrapedListing] = []
        seen_ids: set[str] = set()

        async with async_playwright() as pw:
            browser, ctx = await create_stealth_browser(pw)
            page = await ctx.new_page()

            # ---- intercepted API payloads (accumulated across pages) ----
            api_payloads: list[dict] = []

            async def _on_response(resp: Response) -> None:
                url = resp.url
                if any(k in url for k in ("StaysSearch", "ExploreSearch")):
                    try:
                        api_payloads.append(await resp.json())
                    except Exception:
                        pass

            page.on("response", _on_response)

            # ---- page 1 ------------------------------------------------
            search_url = (
                "https://www.airbnb.com/s/Berchtesgaden--Germany/homes"
                "?refinement_paths%5B%5D=%2Fhomes"
                "&search_type=filter_change&tab_id=home_tab"
            )
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45_000)
            except Exception as exc:
                logger.warning("Airbnb page.goto timeout: %s", exc)

            await self._dismiss_cookie(page)
            await asyncio.sleep(random.uniform(4, 7))

            # scroll full first page
            await self._scroll_page(page)

            # extract first page
            page_listings = await self._extract_page(page, api_payloads)
            for li in page_listings:
                if li.external_id not in seen_ids:
                    seen_ids.add(li.external_id)
                    all_listings.append(li)
            api_payloads.clear()

            logger.info("Airbnb page 1: %d listings", len(page_listings))

            # ---- paginate through remaining pages -----------------------
            for page_num in range(2, MAX_PAGES + 1):
                # Click "Next" button
                next_clicked = await self._click_next(page)
                if not next_clicked:
                    logger.info("Airbnb: no more pages after page %d", page_num - 1)
                    break

                await asyncio.sleep(random.uniform(3, 6))
                await self._scroll_page(page)

                page_listings = await self._extract_page(page, api_payloads)
                api_payloads.clear()

                new_count = 0
                for li in page_listings:
                    if li.external_id not in seen_ids:
                        seen_ids.add(li.external_id)
                        all_listings.append(li)
                        new_count += 1

                logger.info(
                    "Airbnb page %d: %d listings (%d new)",
                    page_num, len(page_listings), new_count,
                )

                # Stop if we get no new listings (end of results)
                if new_count == 0:
                    break

                # Human-like delay between pages
                await asyncio.sleep(random.uniform(2, 5))

            await browser.close()

        logger.info("Airbnb: %d unique listings total", len(all_listings))
        return all_listings

    async def scrape_prices(self, listing_ids: list[str]) -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Pagination helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _click_next(page: Page) -> bool:
        """Click the Next page button. Returns True if found and clicked."""
        for sel in (
            'a[aria-label="Next"]',
            'nav[aria-label*="pagination"] a:last-child',
            'a[aria-label="Weiter"]',
        ):
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=3_000):
                    await loc.click()
                    await asyncio.sleep(2)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10_000)
                    except Exception:
                        pass
                    return True
            except Exception:
                continue
        return False

    @staticmethod
    async def _scroll_page(page: Page) -> None:
        """Scroll down the page to trigger lazy-loading."""
        for _ in range(4):
            await page.evaluate(
                "window.scrollBy(0, %d)" % random.randint(600, 1000)
            )
            await asyncio.sleep(random.uniform(0.6, 1.5))

    async def _extract_page(
        self, page: Page, api_payloads: list[dict]
    ) -> list[ScrapedListing]:
        """Extract listings from the current page using all methods."""
        listings: list[ScrapedListing] = []

        # Method 1: intercepted API data
        for payload in api_payloads:
            listings.extend(self._parse_api_payload(payload))

        # Method 2: __NEXT_DATA__
        if not listings:
            try:
                nd = await page.evaluate(
                    "(() => {"
                    "  const el = document.getElementById('__NEXT_DATA__');"
                    "  return el ? JSON.parse(el.textContent) : null;"
                    "})()"
                )
                if nd:
                    listings = self._parse_deep(nd)
            except Exception:
                pass

        # Method 3: DOM cards
        if not listings:
            listings = await self._extract_dom(page)

        return listings
    # Cookie / consent helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _dismiss_cookie(page: Page) -> None:
        for sel in (
            'button[data-testid="accept-btn"]',
            "button:has-text('Accept')",
            "button:has-text('OK')",
            "button:has-text('Akzeptieren')",
        ):
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2_000):
                    await loc.click()
                    await asyncio.sleep(0.5)
                    return
            except Exception:
                continue

    # ------------------------------------------------------------------
    # Method 1 – parse intercepted API payloads
    # ------------------------------------------------------------------

    def _parse_api_payload(self, data: dict) -> list[ScrapedListing]:
        listings: list[ScrapedListing] = []
        # navigate typical Airbnb StaysSearch response shapes
        for path in (
            ("data", "presentation", "staysSearch", "results", "searchResults"),
            ("data", "presentation", "explore", "sections", "sections"),
        ):
            node = data
            for key in path:
                node = node.get(key, {}) if isinstance(node, dict) else {}
            if isinstance(node, list) and node:
                for section in node:
                    items = section.get("items", [section]) if isinstance(section, dict) else [section]
                    for item in items:
                        obj = item.get("listing", item) if isinstance(item, dict) else {}
                        parsed = self._to_scraped(obj, item)
                        if parsed:
                            listings.append(parsed)
                if listings:
                    return listings

        # deep-search fallback
        return self._parse_deep(data)

    # ------------------------------------------------------------------
    # Method 2 – deep recursive search for listing-shaped dicts
    # ------------------------------------------------------------------

    def _parse_deep(self, data, depth: int = 0) -> list[ScrapedListing]:
        if depth > 12:
            return []
        results: list[ScrapedListing] = []
        if isinstance(data, dict):
            if "listing" in data and isinstance(data["listing"], dict):
                p = self._to_scraped(data["listing"], data)
                if p:
                    results.append(p)
            elif self._looks_like_listing(data):
                p = self._to_scraped(data, data)
                if p:
                    results.append(p)
            else:
                for v in data.values():
                    if isinstance(v, (dict, list)):
                        results.extend(self._parse_deep(v, depth + 1))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    results.extend(self._parse_deep(item, depth + 1))
        return results

    @staticmethod
    def _looks_like_listing(d: dict) -> bool:
        has_id = any(k in d for k in ("id", "listingId", "roomId"))
        has_name = any(k in d for k in ("name", "title"))
        has_loc = any(k in d for k in ("lat", "coordinate", "location"))
        return has_id and has_name and has_loc

    # ------------------------------------------------------------------
    # Method 3 – DOM extraction
    # ------------------------------------------------------------------

    async def _extract_dom(self, page: Page) -> list[ScrapedListing]:
        listings: list[ScrapedListing] = []
        try:
            cards = await page.query_selector_all(
                '[itemprop="itemListElement"], [data-testid="card-container"]'
            )
            if not cards:
                cards = await page.query_selector_all('div[id^="listing_"]')

            logger.info("Airbnb DOM: found %d card elements", len(cards))

            for card in cards[:60]:
                try:
                    link = await card.query_selector('a[href*="/rooms/"]')
                    if not link:
                        continue
                    href = await link.get_attribute("href") or ""
                    m = re.search(r"/rooms/(\d+)", href)
                    if not m:
                        continue
                    lid = m.group(1)

                    # Title – use card text lines; title is usually line 3-4
                    title_el = await card.query_selector(
                        '[data-testid="listing-card-title"], [id*="title"]'
                    )
                    title = (await title_el.inner_text()) if title_el else None
                    if not title:
                        # Fallback: 3rd non-empty line is often the listing type
                        full_text = await card.inner_text()
                        lines = [l.strip() for l in full_text.split("\n") if l.strip()]
                        # Find first line starting with "Room|Apartment|Place|Home|Cabin"
                        for line in lines:
                            if re.match(
                                r"(Room|Apartment|Place|Home|Cabin|Entire|Villa|Cottage)",
                                line, re.I,
                            ):
                                title = line
                                break
                        if not title and len(lines) >= 3:
                            title = lines[2]

                    # Price – find span with € or $ that is NOT "total"
                    price = 0.0
                    all_spans = await card.query_selector_all("span")
                    for span in all_spans:
                        txt = (await span.inner_text()).strip()
                        if ("€" in txt or "$" in txt) and "total" not in txt.lower():
                            m2 = re.search(r"[\d,.]+", txt.replace("\xa0", ""))
                            if m2:
                                cleaned = m2.group().replace(",", "")
                                price = float(cleaned)
                                break

                    # Rating – look for aria-label with "rating"
                    rating = 0.0
                    rating_el = await card.query_selector(
                        '[role="img"][aria-label*="rating"]'
                    )
                    if rating_el:
                        lbl = await rating_el.get_attribute("aria-label") or ""
                        rm = re.search(r"([\d.]+)", lbl)
                        if rm:
                            rating = float(rm.group(1))
                    if not rating:
                        # Fallback: look for small numeric span (4.xx etc)
                        for span in all_spans:
                            txt = (await span.inner_text()).strip()
                            if re.fullmatch(r"\d\.\d{1,2}", txt):
                                rating = float(txt)
                                break

                    listings.append(
                        ScrapedListing(
                            external_id=f"airbnb_{lid}",
                            platform="airbnb",
                            property_type=classify_property_type(
                                title or "", platform_hint="airbnb"
                            ),
                            title=(title or f"Airbnb {lid}").strip(),
                            location="Berchtesgaden",
                            lat=self.center_lat,
                            lng=self.center_lng,
                            capacity=2,
                            bedrooms=1,
                            bathrooms=1,
                            square_meters=40.0,
                            rating=rating,
                            review_count=0,
                            amenities=[],
                            base_price=price,
                        )
                    )
                except Exception:
                    continue
        except Exception as exc:
            logger.warning("Airbnb DOM extraction error: %s", exc)
        return listings

    # ------------------------------------------------------------------
    # Shared listing builder
    # ------------------------------------------------------------------

    def _to_scraped(self, listing: dict, context: dict | None = None) -> ScrapedListing | None:
        """Convert a raw dict to ScrapedListing or None."""
        context = context or listing
        try:
            lid = str(
                listing.get("id")
                or listing.get("listingId")
                or listing.get("roomId")
                or ""
            )
            if not lid:
                return None

            title = listing.get("name") or listing.get("title") or "Unknown"

            # coordinates
            lat = float(listing.get("lat") or listing.get("latitude") or 0)
            lng = float(listing.get("lng") or listing.get("longitude") or 0)
            if lat == 0 or lng == 0:
                coord = listing.get("coordinate", {})
                if isinstance(coord, dict):
                    lat = float(coord.get("latitude", 0))
                    lng = float(coord.get("longitude", 0))
            if lat == 0 and lng == 0:
                lat, lng = self.center_lat, self.center_lng

            # price
            price = self._extract_price(context)

            capacity = int(listing.get("personCapacity") or listing.get("guests") or 2)
            bedrooms = int(listing.get("bedrooms") or listing.get("bedroomCount") or 1)
            bathrooms = int(float(listing.get("bathrooms") or listing.get("bathroomCount") or 1))

            raw_rating = float(
                listing.get("avgRating")
                or listing.get("starRating")
                or listing.get("guestSatisfactionOverall")
                or 0
            )
            rating = raw_rating / 20.0 if raw_rating > 5 else raw_rating
            review_count = int(listing.get("reviewsCount") or listing.get("reviews_count") or 0)

            return ScrapedListing(
                external_id=f"airbnb_{lid}",
                platform="airbnb",
                property_type=classify_property_type(title, platform_hint="airbnb"),
                title=title,
                location="Berchtesgaden",
                lat=lat,
                lng=lng,
                capacity=capacity,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_meters=float(bedrooms) * 25.0,
                rating=rating,
                review_count=review_count,
                amenities=[],
                base_price=price,
            )
        except Exception as exc:
            logger.debug("Cannot convert listing dict: %s", exc)
            return None

    @staticmethod
    def _extract_price(data: dict) -> float:
        for key in ("price", "priceString", "priceLabel"):
            val = data.get(key)
            if val:
                cleaned = re.sub(r"[^\d.]", "", str(val).replace(",", "."))
                if cleaned:
                    return float(cleaned)
        pricing = data.get("pricingQuote") or data.get("pricing") or {}
        if isinstance(pricing, dict):
            structured = pricing.get("structuredStayDisplayPrice", {})
            primary = structured.get("primaryLine", {})
            raw = primary.get("price", "") or str(pricing.get("price", 0))
            cleaned = re.sub(r"[^\d.]", "", str(raw).replace(",", "."))
            if cleaned and float(cleaned) > 0:
                return float(cleaned)
        return 0.0
