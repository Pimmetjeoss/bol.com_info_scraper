# Implementation Plan: JavaScript-Rendered Content Scraping with Rate Limiting

**Branch**: `002-js-scraper-ratelimit` | **Date**: 2025-12-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-js-scraper-ratelimit/spec.md`

## Summary

Enhance the existing Bol.com Partner Platform Help Scraper to handle JavaScript-rendered
content using browser automation (Playwright) and implement rate limiting to avoid 429
errors. The current scraper fails because: (1) the target site uses client-side JS rendering,
returning only redirect pages to static HTTP requests, and (2) aggressive concurrency triggers
rate limiting on 66% of requests. This update replaces aiohttp with Playwright for page
fetching while preserving all existing output formats.

## Technical Context

**Language/Version**: Python 3.11+ (existing project)
**Primary Dependencies**: Playwright (browser automation), asyncio (concurrency control), beautifulsoup4 (HTML parsing), markdownify (HTML→MD)
**Storage**: Local filesystem (markdown files + images)
**Testing**: None (per constitution - manual verification only)
**Target Platform**: Windows (local execution)
**Project Type**: Single script/module (existing scraper.py)
**Performance Goals**: ~387 pages in under 30 minutes with 5 concurrent browser contexts
**Constraints**: 5 concurrent requests, 30s page timeout, 3 retries with 2-4-8s backoff
**Scale/Scope**: ~387 URLs, one-time execution, ~2-3GB RAM for browser instances

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | ✅ PASS | Single file modification, replace HTTP client with Playwright |
| II. No Testing Required | ✅ PASS | No test infrastructure, manual verification |
| III. Maximum Performance | ✅ PASS | 5 concurrent browser contexts, async processing |
| IV. Pragmatic Execution | ✅ PASS | Direct problem-solving, minimal ceremony |

**Gate Status**: PASS - All principles satisfied.

**Note on Principle III**: The constitution states "No rate limiting unless absolutely required
to avoid bans." Rate limiting IS absolutely required here - 66% of requests currently fail
with 429 errors. The 5-concurrent limit is the minimum necessary to avoid bans while
maintaining reasonable performance.

## Project Structure

### Documentation (this feature)

```text
specs/002-js-scraper-ratelimit/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # N/A (no API)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
scraper.py               # Main scraper script (modified in place)
links.md                 # Input: list of URLs to scrape
output/                  # Output directory
├── hulp-nodig/          # Mirrored URL hierarchy
│   ├── aanbod/
│   │   └── *.md
│   └── ...
├── images/              # Downloaded images
└── index.json           # Generated index
```

**Structure Decision**: Continue with flat single-file approach. Modify existing `scraper.py`
to use Playwright instead of aiohttp for page fetching. No structural changes to the codebase.

## Complexity Tracking

> No violations. Design follows all constitution principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
