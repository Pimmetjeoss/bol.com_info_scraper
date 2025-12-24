# Data Model: JavaScript-Rendered Content Scraping with Rate Limiting

**Date**: 2025-12-24
**Branch**: 002-js-scraper-ratelimit

## Entities

This feature extends the existing scraper. Data model remains largely unchanged,
with additions for rate limiting and retry tracking.

### ScrapedPage (existing, unchanged)

Represents a single scraped help article.

| Field | Type | Description |
|-------|------|-------------|
| source_url | string | Original URL of the page |
| title | string | Page title (from `<title>` or `<h1>`) |
| content_md | string | Extracted content as Markdown |
| images | list[Image] | Images found in content |
| category | list[string] | Hierarchy from URL path |
| scraped_at | datetime | Timestamp of scrape |
| local_path | string | Output file path relative to output/ |

### Image (existing, unchanged)

Represents a downloaded image asset.

| Field | Type | Description |
|-------|------|-------------|
| original_url | string | Original image URL |
| local_path | string | Downloaded file path relative to output/ |
| page_url | string | URL of page containing the image |

### ScrapeError (new)

Represents a failed scrape attempt with retry information.

| Field | Type | Description |
|-------|------|-------------|
| url | string | URL that failed |
| error_type | string | Category: "timeout", "rate_limit", "network", "parse", "unknown" |
| error_message | string | Detailed error description |
| retry_count | int | Number of retry attempts made (0-3) |
| timestamp | datetime | When the final failure occurred |

**Example**:
```python
{
    "url": "https://partnerplatform.bol.com/nl/hulp-nodig/aanbod/verkooprechten",
    "error_type": "rate_limit",
    "error_message": "429 Too Many Requests after 3 retries",
    "retry_count": 3,
    "timestamp": "2025-12-24T10:30:00Z"
}
```

### RateLimitConfig (new, internal)

Configuration for rate limiting behavior. Not persisted, used at runtime.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| max_concurrent | int | 5 | Maximum concurrent browser contexts |
| retry_count | int | 3 | Maximum retries for 429 errors |
| retry_delays | list[int] | [2, 4, 8] | Exponential backoff delays in seconds |
| page_timeout | int | 30 | Page load timeout in seconds |

### Index (existing, extended)

The JSON index file structure (output/index.json).

| Field | Type | Description |
|-------|------|-------------|
| generated_at | datetime | When the index was created |
| total_pages | int | Count of successfully scraped pages |
| total_images | int | Count of downloaded images |
| pages | list[IndexEntry] | List of all pages |
| errors | list[ErrorSummary] | **NEW**: Summary of failed URLs |

### ErrorSummary (new)

Summary entry for index.json errors section.

| Field | Type | Description |
|-------|------|-------------|
| url | string | Failed URL |
| error_type | string | Error category |
| retries | int | Retry attempts made |

**Full Index Example**:
```json
{
    "generated_at": "2025-12-24T10:45:00Z",
    "total_pages": 385,
    "total_images": 142,
    "pages": [
        {
            "title": "Verkooprechten",
            "source_url": "https://partnerplatform.bol.com/nl/hulp-nodig/aanbod/verkooprechten",
            "local_path": "hulp-nodig/aanbod/verkooprechten.md",
            "category": ["hulp-nodig", "aanbod", "verkooprechten"]
        }
    ],
    "errors": [
        {
            "url": "https://partnerplatform.bol.com/nl/hulp-nodig/some-page",
            "error_type": "timeout",
            "retries": 3
        }
    ]
}
```

## Output File Format

### Markdown File Structure (unchanged)

Each scraped page produces a `.md` file with this structure:

```markdown
---
title: "Page Title Here"
source_url: "https://partnerplatform.bol.com/nl/hulp-nodig/..."
scraped_at: "2025-12-24T10:30:00Z"
category:
  - hulp-nodig
  - aanbod
  - subcategory
---

# Page Title Here

Main content converted to markdown...
```

### Directory Structure (unchanged)

```text
output/
├── index.json                              # Master index (with new errors field)
├── images/                                 # All downloaded images
│   ├── screenshot-abc123.png
│   └── diagram-def456.jpg
└── hulp-nodig/                            # Mirrored from URL path
    ├── aanbod/
    │   ├── verkooprechten.md
    │   └── ...
    └── ...
```

## State Transitions

### Page Scraping State Machine

```
[Pending] → [Fetching] → [Rendering] → [Extracting] → [Success]
              ↓             ↓              ↓
           [Retry]       [Retry]        [Failed]
              ↓             ↓
           (429?)       (timeout?)
              ↓             ↓
         [Wait 2-4-8s]   [Skip]
              ↓
        [Max retries?]
              ↓
           [Failed]
```

### Retry Logic

```
attempt = 0
while attempt < 3:
    result = fetch_page(url)
    if result.status == 429:
        attempt += 1
        wait(delays[attempt])  # 2, 4, 8 seconds
    else:
        break
if attempt == 3:
    mark_failed(url, "rate_limit")
```

## Concurrency Model

### Semaphore-Based Throttling

```
                    ┌─────────────────┐
                    │  URL Queue      │
                    │  (387 URLs)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Semaphore(5)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │Context 1│          │Context 2│          │Context N│
   │ (page)  │          │ (page)  │    ...   │ (page)  │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Results Queue  │
                    └─────────────────┘
```

### Browser Resource Management

- Single Chromium browser instance
- Up to 5 browser contexts (isolated sessions)
- Each URL processed in dedicated page within context
- Pages closed after extraction
- Browser restart after 100 pages (memory management)
