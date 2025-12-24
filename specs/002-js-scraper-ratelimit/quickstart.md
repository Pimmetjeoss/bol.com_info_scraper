# Quickstart: Bol.com Partner Platform Help Scraper (v2 - Playwright)

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- ~2GB free RAM (for browser instances)

## Installation

```bash
# Install Python dependencies
pip install playwright beautifulsoup4 lxml markdownify aiohttp

# Install Chromium browser for Playwright
playwright install chromium
```

## Usage

```bash
# Run the scraper
python scraper.py
```

That's it. The scraper will:
1. Read URLs from `links.md`
2. Launch Chromium browser (headless)
3. Fetch pages with JavaScript rendering (5 concurrent)
4. Wait for content to load before extraction
5. Retry rate-limited requests (3 attempts)
6. Extract content and convert to markdown
7. Download images
8. Generate `output/index.json`

## Configuration

Default settings (modify in scraper.py if needed):

| Setting | Default | Description |
|---------|---------|-------------|
| MAX_CONCURRENT | 5 | Concurrent browser contexts |
| PAGE_TIMEOUT | 30 | Seconds to wait for page load |
| RETRY_COUNT | 3 | Retries for 429 errors |
| RETRY_DELAYS | [2, 4, 8] | Backoff delays in seconds |

## Output

After running, you'll find:

```
output/
├── index.json           # Index of all scraped pages + error summary
├── images/              # Downloaded images
└── hulp-nodig/          # Markdown files mirroring URL structure
    ├── aanbod/
    ├── automatiseren/
    └── ...
```

## Expected Results

| Metric | Expected |
|--------|----------|
| Success rate | ≥95% (368+ pages) |
| Completion time | ~30 minutes |
| Rate limit errors | <5% |

## Verification

1. Check `output/index.json`:
   - `total_pages` should be ~385+
   - `errors` array should be small (<20 entries)

2. Open a random `.md` file:
   - Should have YAML frontmatter
   - Should contain actual content (not "You are being redirected...")

3. Check `output/images/`:
   - Should contain downloaded images (if any on pages)

## Troubleshooting

**Browser fails to launch**:
```bash
# Reinstall Chromium
playwright install chromium --force
```

**Still getting 429 errors**:
- Reduce MAX_CONCURRENT to 3
- Increase RETRY_DELAYS to [5, 10, 20]

**Pages still show empty content**:
- Some pages may require authentication (logged as errors)
- Check console output for specific error messages

**Memory issues**:
- The scraper restarts the browser every 100 pages
- If still problematic, reduce MAX_CONCURRENT to 3

**Timeout errors**:
- Increase PAGE_TIMEOUT to 45 or 60 seconds
- Network issues may require re-running

## Differences from v1 (aiohttp)

| Feature | v1 (aiohttp) | v2 (Playwright) |
|---------|--------------|-----------------|
| JS rendering | No | Yes |
| Rate limiting | None | 5 concurrent |
| Retry logic | None | 3 retries |
| Expected success | ~34% | ≥95% |
| Speed | Very fast | Moderate |
| Memory | ~100MB | ~1-2GB |
