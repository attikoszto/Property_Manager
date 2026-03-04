"""
Booking.com scraper using Playwright headless browser.

Infinite-scrolls each page and paginates through all result pages to
capture the full inventory for a region.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
from datetime import date, timedelta

from playwright.async_api import Page, Response, async_playwright

from core.logging import logger
from infrastructure.scraping.browser import create_stealth_browser
from infrastructure.scraping.models import ScrapedListing, classify_property_type

# Safety cap on pages
MAX_PAGES = 20


class BookingScraper:
    """Scrapes Booking.com listings with infinite-scroll + page pagination."""

    def __init__(self, center_lat: float, center_lng: float, radius_km: float):
        self.center_lat = center_lat
        self.center_lng = center_lng
        self.radius_km = radius_km

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape_listings(self) -> list[ScrapedListing]:
        logger.info(
            "Scraping Booking.com around (%.4f, %.4f) r=%.1f km",
            self.center_lat, self.center_lng, self.radius_km,
        )

        all_listings: list[ScrapedListing] = []
        seen_ids: set[str] = set()

        checkin = (date.today() + timedelta(days=14)).isoformat()
        checkout = (date.today() + timedelta(days=16)).isoformat()

        base_url = (
            "https://www.booking.com/searchresults.html"
            f"?ss=Berchtesgaden%2C+Germany"
            f"&dest_type=city"
            f"&checkin={checkin}&checkout={checkout}"
            "&group_adults=2&no_rooms=1&group_children=0"
            "&selected_currency=EUR"
        )

        async with async_playwright() as pw:
            browser, ctx = await create_stealth_browser(pw)
            page = await ctx.new_page()

            # ---- intercept API responses --------------------------------
            api_payloads: list[dict] = []

            async def _on_response(resp: Response) -> None:
                url = resp.url
                if any(k in url for k in ("graphql", "sr_ajax", "SearchResultsQuery")):
                    try:
                        api_payloads.append(await resp.json())
                    except Exception:
                        pass

            page.on("response", _on_response)

            for page_num in range(MAX_PAGES):
                offset = page_num * 25
                url = f"{base_url}&offset={offset}" if offset else base_url

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                except Exception as exc:
                    logger.warning("Booking page.goto timeout (page %d): %s", page_num + 1, exc)
                    break

                # Cloudflare challenge resolve
                try:
                    await page.wait_for_load_state("networkidle", timeout=30_000)
                except Exception:
                    pass
                await asyncio.sleep(random.uniform(3, 6))

                if page_num == 0:
                    await self._dismiss_cookie(page)

                # wait for property cards
                try:
                    await page.wait_for_selector(
                        '[data-testid="property-card"]',
                        timeout=20_000,
                    )
                except Exception:
                    logger.info("Booking page %d: no property cards found – stopping", page_num + 1)
                    break

                # infinite scroll within the page until no new cards appear
                await self._scroll_until_stable(page)

                # extract from this page
                api_payloads_copy = list(api_payloads)
                api_payloads.clear()

                page_listings = await self._extract_dom(page)
                if not page_listings:
                    for payload in api_payloads_copy:
                        page_listings.extend(self._parse_api(payload))
                if not page_listings:
                    html = await page.content()
                    page_listings = self._parse_embedded_json(html)

                new_count = 0
                for li in page_listings:
                    if li.external_id not in seen_ids:
                        seen_ids.add(li.external_id)
                        all_listings.append(li)
                        new_count += 1

                logger.info(
                    "Booking page %d (offset=%d): %d cards, %d new",
                    page_num + 1, offset, len(page_listings), new_count,
                )

                # If no new listings found, we've exhausted all results
                if new_count == 0:
                    break

                # human-like delay between pages
                await asyncio.sleep(random.uniform(3, 6))

            await browser.close()

        logger.info("Booking.com: %d unique listings total", len(all_listings))
        return all_listings

    async def scrape_prices(self, listing_ids: list[str]) -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _scroll_until_stable(page: Page, max_scrolls: int = 20) -> None:
        """Keep scrolling until no new property cards appear."""
        prev_count = 0
        stable_rounds = 0
        for _ in range(max_scrolls):
            await page.evaluate(
                "window.scrollBy(0, %d)" % random.randint(600, 1000)
            )
            await asyncio.sleep(random.uniform(1.0, 2.5))

            # Click "Load more results" button if present
            try:
                btn = page.locator('button:has-text("Load more results"), button:has-text("Mehr Ergebnisse")')
                if await btn.first.is_visible(timeout=1_000):
                    await btn.first.click()
                    await asyncio.sleep(random.uniform(2, 4))
            except Exception:
                pass

            cards = await page.query_selector_all('[data-testid="property-card"]')
            current_count = len(cards)
            if current_count == prev_count:
                stable_rounds += 1
                if stable_rounds >= 3:
                    break
            else:
                stable_rounds = 0
            prev_count = current_count

    # ------------------------------------------------------------------
    # Cookie banner
    # ------------------------------------------------------------------

    @staticmethod
    async def _dismiss_cookie(page: Page) -> None:
        for sel in (
            "#onetrust-accept-btn-handler",
            "button#b2indexPage\\.onetrust-accept-btn-handler",
            "button:has-text('Accept')",
            "button:has-text('Akzeptieren')",
        ):
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=3_000):
                    await loc.click()
                    await asyncio.sleep(0.5)
                    return
            except Exception:
                continue

    # ------------------------------------------------------------------
    # Method 1 – DOM extraction
    # ------------------------------------------------------------------

    async def _extract_dom(self, page: Page) -> list[ScrapedListing]:
        listings: list[ScrapedListing] = []

        cards = await page.query_selector_all('[data-testid="property-card"]')
        if not cards:
            cards = await page.query_selector_all("[data-hotelid]")

        logger.info("Booking DOM: found %d property cards", len(cards))

        for card in cards[:80]:
            try:
                # -- hotel ID -------------------------------------------------
                hotel_id = await card.get_attribute("data-hotelid")
                if not hotel_id:
                    inner = await card.query_selector("[data-hotelid]")
                    if inner:
                        hotel_id = await inner.get_attribute("data-hotelid")
                if not hotel_id:
                    link = await card.query_selector('a[href*="/hotel/"]')
                    if link:
                        href = await link.get_attribute("href") or ""
                        m = re.search(r"/hotel/\w+/([a-z0-9_-]+)\.html", href, re.I)
                        hotel_id = m.group(1) if m else None
                if not hotel_id:
                    continue

                # -- title ----------------------------------------------------
                title = await self._text(card, '[data-testid="title"]')
                if not title:
                    title = await self._text(card, "span.sr-hotel__name")
                title = title or f"Booking {hotel_id}"

                # -- price ----------------------------------------------------
                price_text = await self._text(
                    card, '[data-testid="price-and-discounted-price"]'
                )
                if not price_text:
                    price_text = await self._text(card, 'span.prco-valign-middle-helper')
                price = self._parse_price(price_text)

                # -- rating ---------------------------------------------------
                score_text = await self._text(
                    card,
                    '[data-testid="review-score"] div:first-child',
                )
                raw_rating = float(
                    re.sub(r"[^\d.]", "", (score_text or "0").replace(",", ".")) or 0
                )
                rating = raw_rating / 2.0 if raw_rating > 5 else raw_rating

                # -- review count ---------------------------------------------
                review_text = await self._text(
                    card,
                    '[data-testid="review-score"] div:nth-child(2) div:last-child',
                )
                review_count = 0
                if review_text:
                    rm = re.search(r"([\d.,]+)", review_text.replace(".", ""))
                    review_count = int(rm.group(1).replace(",", "").replace(".", "")) if rm else 0

                listings.append(
                    ScrapedListing(
                        external_id=f"booking_{hotel_id}",
                        platform="booking",
                        property_type=classify_property_type(
                            title.strip(), platform_hint="booking"
                        ),
                        title=title.strip(),
                        location="Berchtesgaden",
                        lat=self.center_lat,
                        lng=self.center_lng,
                        capacity=2,
                        bedrooms=1,
                        bathrooms=1,
                        square_meters=40.0,
                        rating=rating,
                        review_count=review_count,
                        amenities=[],
                        base_price=price,
                    )
                )
            except Exception as exc:
                logger.debug("Booking card parse error: %s", exc)
                continue

        return listings

    # ------------------------------------------------------------------
    # Method 2 – intercepted API / GraphQL
    # ------------------------------------------------------------------

    def _parse_api(self, data: dict) -> list[ScrapedListing]:
        listings: list[ScrapedListing] = []
        found = self._find_property_dicts(data)
        for prop in found:
            parsed = self._dict_to_scraped(prop)
            if parsed:
                listings.append(parsed)
        return listings

    # ------------------------------------------------------------------
    # Method 3 – embedded JSON in raw HTML
    # ------------------------------------------------------------------

    def _parse_embedded_json(self, html: str) -> list[ScrapedListing]:
        listings: list[ScrapedListing] = []

        # application/ld+json
        for m in re.finditer(
            r'<script\s+type="application/ld\+json">(.*?)</script>', html, re.S
        ):
            try:
                d = json.loads(m.group(1))
                listings.extend(self._parse_ld_json(d))
            except Exception:
                continue

        # window.__BOOKING_CONTEXT__ or similar
        for pattern in (
            r"window\.__BOOKING_CONTEXT__\s*=\s*({.*?});",
            r"b_search_results_jsonData\s*=\s*({.*?});",
        ):
            m = re.search(pattern, html, re.S)
            if m:
                try:
                    data = json.loads(m.group(1))
                    found = self._find_property_dicts(data)
                    for prop in found:
                        parsed = self._dict_to_scraped(prop)
                        if parsed:
                            listings.append(parsed)
                except Exception:
                    continue

        return listings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _text(parent, selector: str) -> str | None:
        el = await parent.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()
        return None

    @staticmethod
    def _parse_price(raw: str | None) -> float:
        if not raw:
            return 0.0
        cleaned = re.sub(r"[^\d.]", "", raw.replace(",", ".").replace("€", ""))
        return float(cleaned) if cleaned else 0.0

    def _find_property_dicts(self, data, depth: int = 0) -> list[dict]:
        if depth > 8:
            return []
        results: list[dict] = []
        if isinstance(data, dict):
            if any(k in data for k in ("hotel_id", "hotel_name", "property_name")):
                results.append(data)
            else:
                for v in data.values():
                    if isinstance(v, (dict, list)):
                        results.extend(self._find_property_dicts(v, depth + 1))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    results.extend(self._find_property_dicts(item, depth + 1))
        return results

    def _dict_to_scraped(self, prop: dict) -> ScrapedListing | None:
        try:
            hid = str(prop.get("hotel_id") or prop.get("id") or prop.get("property_id") or "")
            if not hid:
                return None
            name = prop.get("hotel_name") or prop.get("property_name") or prop.get("name") or "Unknown"
            lat = float(prop.get("latitude") or prop.get("lat") or 0)
            lng = float(prop.get("longitude") or prop.get("lng") or 0)
            if lat == 0 and lng == 0:
                lat, lng = self.center_lat, self.center_lng
            price = float(
                prop.get("min_total_price")
                or prop.get("price")
                or prop.get("composite_price_breakdown", {}).get("gross_amount", {}).get("value", 0)
                or 0
            )
            raw_rating = float(prop.get("review_score") or prop.get("rating") or 0)
            rating = raw_rating / 2.0 if raw_rating > 5 else raw_rating
            review_count = int(prop.get("review_nr") or prop.get("review_count") or 0)

            return ScrapedListing(
                external_id=f"booking_{hid}",
                platform="booking",
                property_type=classify_property_type(name, platform_hint="booking"),
                title=name,
                location="Berchtesgaden",
                lat=lat,
                lng=lng,
                capacity=int(prop.get("max_persons") or 2),
                bedrooms=int(prop.get("bedrooms") or 1),
                bathrooms=int(prop.get("bathrooms") or 1),
                square_meters=float(prop.get("size") or 40.0),
                rating=rating,
                review_count=review_count,
                amenities=[],
                base_price=price,
            )
        except Exception as exc:
            logger.debug("Booking dict parse error: %s", exc)
            return None

    def _parse_ld_json(self, data) -> list[ScrapedListing]:
        if isinstance(data, list):
            out: list[ScrapedListing] = []
            for item in data:
                out.extend(self._parse_ld_json(item))
            return out
        if not isinstance(data, dict):
            return []
        t = data.get("@type", "")
        if t not in ("Hotel", "LodgingBusiness", "VacationRental", "Apartment"):
            return []
        geo = data.get("geo", {})
        lat = float(geo.get("latitude", 0))
        lng = float(geo.get("longitude", 0))
        if lat == 0 and lng == 0:
            lat, lng = self.center_lat, self.center_lng
        name = data.get("name", "Unknown")
        offers = data.get("offers", {})
        price = float(offers.get("price", 0)) if isinstance(offers, dict) else 0.0
        agg = data.get("aggregateRating", {})
        raw_rating = float(agg.get("ratingValue", 0))
        rating = raw_rating / 2.0 if raw_rating > 5 else raw_rating
        url = data.get("url", "")
        m = re.search(r"hotel/[^/]*?\.([^.]+)\.html", url)
        ext_id = m.group(1) if m else str(hash(name))[:10]
        return [
            ScrapedListing(
                external_id=f"booking_{ext_id}",
                platform="booking",
                property_type=classify_property_type(name, platform_hint="booking"),
                title=name,
                location="Berchtesgaden",
                lat=lat,
                lng=lng,
                capacity=2,
                bedrooms=1,
                bathrooms=1,
                square_meters=40.0,
                rating=rating,
                review_count=int(agg.get("reviewCount", 0)),
                amenities=[],
                base_price=price,
            )
        ]
