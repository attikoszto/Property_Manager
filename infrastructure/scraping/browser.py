"""Shared Playwright browser context with anti-detection measures."""

from __future__ import annotations

import random

from playwright.async_api import Browser, BrowserContext, Playwright

# Rotate through realistic, recent Chrome user-agents so the same fingerprint
# is not sent on every run.
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
]

STEALTH_JS = """
// Hide webdriver flag
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// Fake Chrome runtime
window.chrome = {runtime: {}, loadTimes: () => {}, csi: () => {}};

// Fake plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const arr = [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            {name: 'Native Client', filename: 'internal-nacl-plugin'},
        ];
        arr.length = 3;
        return arr;
    }
});

// Fake languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en', 'de']
});

// Permissions workaround
const origQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (params) =>
    params.name === 'notifications'
        ? Promise.resolve({state: Notification.permission})
        : origQuery(params);

// WebGL vendor
const getParam = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(p) {
    if (p === 37445) return 'Intel Inc.';
    if (p === 37446) return 'Intel Iris OpenGL Engine';
    return getParam.call(this, p);
};
"""


async def create_stealth_browser(
    pw: Playwright,
    *,
    headless: bool = True,
) -> tuple[Browser, BrowserContext]:
    """Launch Chromium with stealth patches and return (browser, context)."""
    browser = await pw.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    context = await browser.new_context(
        user_agent=random.choice(_USER_AGENTS),
        viewport=random.choice(_VIEWPORTS),
        locale=random.choice(["en-US", "de-DE", "en-GB"]),
        timezone_id="Europe/Berlin",
    )
    await context.add_init_script(STEALTH_JS)
    return browser, context
