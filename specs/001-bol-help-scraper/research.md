# Research: Bol.com Partner Platform Help Scraper

**Date**: 2025-12-24
**Branch**: 001-bol-help-scraper

## Technology Decisions

### 1. HTTP Client: aiohttp

**Decision**: Use `aiohttp` for async HTTP requests.

**Rationale**:
- Native async/await support for maximum concurrency
- Connection pooling built-in
- Handles hundreds of concurrent requests efficiently
- Mature, well-maintained library

**Alternatives considered**:
- `httpx`: Good async support, but aiohttp is faster for high-concurrency scraping
- `requests`: Synchronous only, would require threading for parallelism
- `urllib3`: Lower-level, more boilerplate needed

### 2. HTML Parsing: BeautifulSoup4 with lxml

**Decision**: Use `beautifulsoup4` with `lxml` parser.

**Rationale**:
- Fast parsing with lxml backend
- Excellent CSS selector support for content extraction
- Handles malformed HTML gracefully
- Well-documented, familiar API

**Alternatives considered**:
- `lxml` directly: Faster but less forgiving of malformed HTML
- `html5lib`: More standards-compliant but slower
- `selectolax`: Faster but less mature ecosystem

### 3. HTML to Markdown: markdownify

**Decision**: Use `markdownify` for HTML→Markdown conversion.

**Rationale**:
- Purpose-built for HTML to Markdown
- Handles tables, lists, headers automatically
- Configurable output (heading style, bullet characters)
- Lightweight, single-purpose

**Alternatives considered**:
- `html2text`: Older, less actively maintained
- `pypandoc`: Overkill, requires Pandoc installation
- Custom implementation: Unnecessary when library exists

### 4. Image Downloading: aiohttp (same client)

**Decision**: Reuse `aiohttp` session for image downloads.

**Rationale**:
- Already a dependency for page fetching
- Async downloading in parallel with other operations
- Single connection pool for all HTTP traffic

### 5. YAML Frontmatter: Manual string formatting

**Decision**: Generate YAML frontmatter with simple string formatting.

**Rationale**:
- Frontmatter is simple (3-4 fields)
- Avoids adding a YAML library dependency
- Full control over output format

**Alternatives considered**:
- `pyyaml`: Adds dependency for trivial use case
- `ruamel.yaml`: Overkill for simple frontmatter

### 6. JSON Index: Built-in json module

**Decision**: Use Python's built-in `json` module.

**Rationale**:
- Standard library, no additional dependency
- Sufficient for writing index.json
- `json.dump()` with `indent=2` for readability

### 7. Concurrency Model: asyncio.gather with Semaphore

**Decision**: Use `asyncio.gather()` for parallel execution, with optional Semaphore
if needed to prevent connection exhaustion.

**Rationale**:
- Per constitution: "maximum concurrent requests"
- asyncio.gather runs all tasks truly in parallel
- Semaphore available as escape hatch if site blocks

**Implementation approach**:
- Start with unbounded concurrency (all 387 requests at once)
- If connection errors occur, add Semaphore(50-100) as fallback

## Content Extraction Strategy

### Target: Main Content Area

Based on typical CMS help page structure, the main content is likely in:
- `<main>` element
- `<article>` element
- `div.content` or similar class
- Exclude: `<header>`, `<footer>`, `<nav>`, `<aside>`

**Approach**: Try selectors in order until content found:
1. `main article`
2. `main`
3. `article`
4. `.content`, `.article-content`, `.help-content`

### Content Elements to Preserve

| Element | Markdown Output |
|---------|-----------------|
| `<h1>` - `<h6>` | `#` - `######` |
| `<p>` | Plain paragraph |
| `<ul>`, `<ol>` | Markdown lists |
| `<table>` | Markdown table |
| `<img>` | `![alt](local-path)` |
| `<a>` | `[text](url)` |
| `<strong>`, `<b>` | `**bold**` |
| `<em>`, `<i>` | `*italic*` |
| `<code>` | `` `code` `` |

### Elements to Strip

- Navigation (`<nav>`)
- Headers (`<header>`)
- Footers (`<footer>`)
- Sidebars (`<aside>`)
- Scripts (`<script>`)
- Styles (`<style>`)
- Cookie banners, popups

## File Naming Convention

**URL to Path Mapping**:
```
https://partnerplatform.bol.com/nl/hulp-nodig/aanbod/verkooprechten
→ output/hulp-nodig/aanbod/verkooprechten.md
```

**Rules**:
1. Strip domain and `/nl/` prefix
2. Each path segment becomes a directory
3. Final segment becomes `.md` filename
4. Handle trailing slashes (strip before processing)

**Image Path Mapping**:
```
https://partnerplatform.bol.com/images/help/screenshot.png
→ output/images/screenshot.png (or hashed filename if duplicates)
```

## Dependencies Summary

```text
aiohttp>=3.9.0      # Async HTTP client
beautifulsoup4>=4.12 # HTML parsing
lxml>=5.0           # Fast parser backend for BS4
markdownify>=0.11   # HTML to Markdown conversion
```

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Site blocks aggressive scraping | Medium | Start with 50ms delay between batches if needed |
| JavaScript-rendered content | Low | Help pages typically server-rendered |
| Inconsistent HTML structure | Medium | Multiple selector fallbacks |
| Very large images | Low | Accept as-is, no resizing needed |
| Connection exhaustion | Medium | Semaphore fallback ready |
