# Data Model: Bol.com Partner Platform Help Scraper

**Date**: 2025-12-24
**Branch**: 001-bol-help-scraper

## Entities

### HelpPage

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

**Example**:
```python
{
    "source_url": "https://partnerplatform.bol.com/nl/hulp-nodig/aanbod/verkooprechten",
    "title": "Verkooprechten",
    "content_md": "# Verkooprechten\n\nHier lees je over...",
    "images": [...],
    "category": ["hulp-nodig", "aanbod", "verkooprechten"],
    "scraped_at": "2025-12-24T10:30:00Z",
    "local_path": "hulp-nodig/aanbod/verkooprechten.md"
}
```

### Image

Represents a downloaded image asset.

| Field | Type | Description |
|-------|------|-------------|
| original_url | string | Original image URL |
| local_path | string | Downloaded file path relative to output/ |
| page_url | string | URL of page containing the image |

**Example**:
```python
{
    "original_url": "https://partnerplatform.bol.com/images/help/screenshot.png",
    "local_path": "images/screenshot.png",
    "page_url": "https://partnerplatform.bol.com/nl/hulp-nodig/aanbod/verkooprechten"
}
```

### Index

The JSON index file structure (output/index.json).

| Field | Type | Description |
|-------|------|-------------|
| generated_at | datetime | When the index was created |
| total_pages | int | Count of successfully scraped pages |
| total_images | int | Count of downloaded images |
| pages | list[IndexEntry] | List of all pages |

### IndexEntry

Individual entry in the index.

| Field | Type | Description |
|-------|------|-------------|
| title | string | Page title |
| source_url | string | Original URL |
| local_path | string | Markdown file path |
| category | list[string] | Hierarchy/breadcrumbs |

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
    ]
}
```

## Output File Format

### Markdown File Structure

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

## Section Heading

More content with **bold** and *italic* text.

- List item 1
- List item 2

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |

![Image description](../images/screenshot.png)
```

## Directory Structure

```text
output/
├── index.json                              # Master index
├── images/                                 # All downloaded images
│   ├── screenshot-abc123.png
│   └── diagram-def456.jpg
└── hulp-nodig/                            # Mirrored from URL path
    ├── aanbod/
    │   ├── verkooprechten.md
    │   ├── verkooprechten/
    │   │   └── gezondheid.md
    │   └── ...
    ├── automatiseren/
    │   └── ...
    └── ...
```

## State Transitions

This is a one-time batch process with no persistent state.

```
[Start] → [Load URLs] → [Fetch Pages (parallel)] → [Extract Content]
       → [Download Images (parallel)] → [Write Markdown] → [Generate Index] → [Done]
```

**Error States**:
- Page fetch fails → Log error, skip page, continue
- Image download fails → Log error, keep original URL in markdown, continue
- Parse error → Log warning, write partial content, continue
