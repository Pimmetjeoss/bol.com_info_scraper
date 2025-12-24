# Research: JavaScript-Rendered Content Scraping with Rate Limiting

**Date**: 2025-12-24
**Branch**: 002-js-scraper-ratelimit

## Technology Decisions

### 1. Browser Automation: Playwright

**Decision**: Use `playwright` for browser automation and JavaScript rendering.

**Rationale**:
- Native async/await support with `playwright.async_api`
- Built-in support for multiple browser contexts (concurrency)
- Excellent wait conditions (`wait_for_selector`, `wait_for_load_state`)
- Headless mode for server/CI execution
- Active development and strong Python support
- Auto-downloads browser binaries

**Alternatives considered**:
- `Selenium`: Older, more complex setup, slower execution
- `Puppeteer`: Node.js native, requires pyppeteer wrapper for Python
- `requests-html`: Limited JS rendering, uses Chromium under the hood anyway
- `Splash`: Requires separate service/Docker container

### 2. Concurrency Control: asyncio.Semaphore

**Decision**: Use `asyncio.Semaphore(5)` to limit concurrent browser operations.

**Rationale**:
- Native Python asyncio primitive
- Zero additional dependencies
- Simple acquire/release pattern
- Works seamlessly with async/await
- Clarified default: 5 concurrent requests

**Implementation approach**:
```python
semaphore = asyncio.Semaphore(5)
async with semaphore:
    # Browser operation here
```

### 3. Page Wait Strategy

**Decision**: Use Playwright's `wait_for_load_state('networkidle')` with 30s timeout.

**Rationale**:
- `networkidle` waits until no network requests for 500ms
- More reliable than fixed delays for JS-rendered content
- 30-second timeout covers slow pages without blocking forever
- Can fallback to `domcontentloaded` if networkidle hangs

**Wait condition cascade**:
1. `wait_for_load_state('networkidle', timeout=30000)`
2. On timeout: `wait_for_load_state('domcontentloaded')`
3. On failure: Log error, skip page

### 4. Retry Strategy: Exponential Backoff

**Decision**: 3 retries with 2-4-8 second delays for 429 errors.

**Rationale**:
- Exponential backoff is industry standard for rate limiting
- 3 retries sufficient for transient 429s
- Total max wait: ~14 seconds per URL
- Gives server time to reset rate limit counters

**Implementation approach**:
```python
delays = [2, 4, 8]  # seconds
for attempt, delay in enumerate(delays):
    try:
        result = await fetch_page(url)
        if result.status == 429:
            await asyncio.sleep(delay)
            continue
        return result
    except Exception:
        if attempt == len(delays) - 1:
            raise
```

### 5. Browser Context Management

**Decision**: Single browser instance with multiple contexts (not multiple browsers).

**Rationale**:
- One browser process uses less memory than multiple browsers
- Contexts are isolated (separate cookies, storage)
- Contexts share browser cache for efficiency
- Each concurrent task gets its own context

**Memory considerations**:
- Single Chromium: ~300-500MB base
- Each context: ~50-100MB additional
- 5 contexts: ~800MB-1GB total (acceptable)

### 6. Content Extraction: Keep Existing Approach

**Decision**: Reuse existing BeautifulSoup + markdownify pipeline.

**Rationale**:
- Already works correctly for HTML→Markdown conversion
- Playwright provides `page.content()` which returns full rendered HTML
- No need to change extraction logic, only page fetching
- Maintains backward compatibility with output format

### 7. Image Downloading: Playwright for Relative URLs, aiohttp for Downloads

**Decision**: Use Playwright to extract image URLs, keep aiohttp for downloading.

**Rationale**:
- Playwright renders page with all images resolved to absolute URLs
- aiohttp is faster for bulk file downloads (no browser overhead)
- Image downloads don't need JS rendering
- Keep existing image download logic intact

## Content Extraction Strategy

### Wait for Content

Based on Bol.com Partner Platform behavior:
1. Initial load returns redirect/spinner
2. JavaScript loads and renders content
3. Content appears in DOM after JS execution

**Detection approach**:
- Wait for `networkidle` state
- Verify content is not just "You are being redirected..."
- If redirect message found after wait, flag as JS-render failure

### Selector Strategy (unchanged from 001)

Use same content selector cascade:
```python
CONTENT_SELECTORS = [
    'main article',
    'main',
    'article',
    '.content',
    '.article-content',
    '.help-content',
    '#content',
    '[role="main"]',
]
```

## Dependencies Summary

```text
playwright>=1.40.0      # Browser automation (replaces aiohttp for page fetch)
beautifulsoup4>=4.12    # HTML parsing (existing)
lxml>=5.0               # Fast parser backend (existing)
markdownify>=0.11       # HTML to Markdown (existing)
aiohttp>=3.9.0          # Keep for image downloads only
```

**New dependency**: `playwright` (and its browser binaries)
**Installation**: `pip install playwright && playwright install chromium`

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Playwright browser download fails | Low | Document manual install steps |
| 5 concurrent still triggers 429 | Medium | Reduce to 3 concurrent if needed |
| Pages require login after all | Low | Already documented as out of scope |
| Memory exhaustion with browsers | Medium | Restart browser after every 100 pages |
| Bot detection blocks Playwright | Low | Use realistic user agent, normal timing |
| Content still empty after JS wait | Medium | Try alternative wait strategies |

## Implementation Notes

### Migration Path

1. Keep existing code structure
2. Replace `aiohttp.ClientSession.get()` with Playwright page navigation
3. Add semaphore wrapper around page operations
4. Add retry logic for 429 responses
5. Keep all content extraction and output logic unchanged

### Browser Lifecycle

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    # Process all URLs
    await browser.close()
```

### Context Pooling

```python
# Create context pool
contexts = [await browser.new_context() for _ in range(5)]

# Assign URLs to contexts round-robin
for i, url in enumerate(urls):
    context = contexts[i % 5]
    page = await context.new_page()
    # ... process page
    await page.close()
```

## Performance Estimates

| Metric | Estimate |
|--------|----------|
| Pages per minute | ~13 (5 concurrent, ~23s avg per page) |
| Total time for 387 pages | ~30 minutes |
| Memory usage | ~1-2GB |
| Network bandwidth | ~50-100MB (HTML + images) |
