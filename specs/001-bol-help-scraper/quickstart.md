# Quickstart: Bol.com Partner Platform Help Scraper

## Prerequisites

- Python 3.11+
- pip (Python package manager)

## Installation

```bash
# Install dependencies
pip install aiohttp beautifulsoup4 lxml markdownify
```

## Usage

```bash
# Run the scraper
python scraper.py
```

That's it. The scraper will:
1. Read URLs from `links.md`
2. Fetch all pages concurrently
3. Extract content and convert to markdown
4. Download images
5. Generate `output/index.json`

## Output

After running, you'll find:

```
output/
├── index.json           # Index of all scraped pages
├── images/              # Downloaded images
└── hulp-nodig/          # Markdown files mirroring URL structure
    ├── aanbod/
    ├── automatiseren/
    └── ...
```

## Verification

1. Check `output/index.json` - should list ~385+ pages
2. Open a random `.md` file - should have YAML frontmatter and readable content
3. Check `output/images/` - should contain downloaded images

## Troubleshooting

**Connection errors**: The scraper uses aggressive concurrency. If you see many
connection errors, the site may be rate limiting. Edit `scraper.py` and reduce
the semaphore value (search for `Semaphore`).

**Empty content**: Some pages may have JavaScript-rendered content. These will
have frontmatter but minimal content. This is expected for a small percentage.

**Missing images**: If images fail to download, the markdown will contain the
original URL instead of a local path. Check the console output for errors.
