# Feature Specification: Bol.com Partner Platform Help Scraper

**Feature Branch**: `001-bol-help-scraper`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "Python scraper for ~387 Bol.com Partner Platform help pages for AI knowledge base"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bulk Scrape All Help Pages (Priority: P1)

As a knowledge base builder, I want to run a single command that scrapes all ~387
help pages from the Bol.com Partner Platform so that I have a complete local copy
of all help documentation for my AI knowledge base.

**Why this priority**: This is the core functionality. Without bulk scraping,
there is no product. All other features depend on successfully fetching content.

**Independent Test**: Run the scraper with the full URL list and verify that
markdown files are created for each valid URL, with content extracted.

**Acceptance Scenarios**:

1. **Given** a list of ~387 URLs in links.md, **When** I run the scraper,
   **Then** a markdown file is created for each successfully scraped page.

2. **Given** the scraper is running, **When** a page returns a 404 or error,
   **Then** the error is logged and scraping continues with remaining URLs.

3. **Given** the scraper completes, **When** I check the output directory,
   **Then** the folder structure mirrors the URL hierarchy
   (e.g., `/hulp-nodig/aanbod/` becomes `hulp-nodig/aanbod/`).

---

### User Story 2 - Extract Structured Content (Priority: P1)

As a knowledge base builder, I want each page's content extracted into clean
markdown with YAML frontmatter so that my AI system can easily parse and index
the content.

**Why this priority**: Raw HTML is useless for an AI knowledge base. Structured
extraction is essential for the output to have value.

**Independent Test**: Inspect any scraped markdown file and verify it contains
proper frontmatter (title, URL, date) and readable markdown content.

**Acceptance Scenarios**:

1. **Given** a scraped help page, **When** I view the output file, **Then**
   it has YAML frontmatter with: title, source URL, and scrape date.

2. **Given** a page with paragraphs, **When** scraped, **Then** the main text
   content is converted to clean markdown paragraphs.

3. **Given** a page with numbered/bulleted lists, **When** scraped, **Then**
   the lists are preserved as proper markdown lists.

4. **Given** a page with tables, **When** scraped, **Then** tables are
   converted to markdown table format.

5. **Given** a page with step-by-step instructions, **When** scraped, **Then**
   the steps are preserved with their numbering/ordering.

---

### User Story 3 - Download Images Locally (Priority: P2)

As a knowledge base builder, I want all images from help pages downloaded
locally with references updated in the markdown so that my knowledge base
is fully self-contained and works offline.

**Why this priority**: Images contain critical visual instructions (screenshots,
diagrams). Without them, many help articles lose important context.

**Independent Test**: Find a scraped page that originally had images, verify
images are downloaded to a local folder, and markdown references point to
local paths.

**Acceptance Scenarios**:

1. **Given** a page with images, **When** scraped, **Then** each image is
   downloaded to a local `images/` subfolder.

2. **Given** downloaded images, **When** I view the markdown, **Then** image
   references use relative local paths (not original URLs).

3. **Given** an image that fails to download, **When** the scraper completes,
   **Then** the failure is logged but scraping continues.

---

### User Story 4 - Generate Index File (Priority: P2)

As a knowledge base consumer, I want a JSON index of all scraped content
so that I can programmatically navigate and search the knowledge base.

**Why this priority**: An index enables quick lookups and navigation without
parsing all markdown files. Essential for AI ingestion pipelines.

**Independent Test**: After scraping, verify `index.json` exists and contains
entries for all scraped pages with their paths and titles.

**Acceptance Scenarios**:

1. **Given** scraping is complete, **When** I check the output directory,
   **Then** an `index.json` file exists at the root.

2. **Given** the index file, **When** I parse it, **Then** each entry contains:
   file path, title, source URL, and hierarchy/category.

3. **Given** the index file, **When** I count entries, **Then** the count
   matches the number of successfully scraped pages.

---

### Edge Cases

- What happens when a URL returns 404 or 5xx? Log error, skip, continue.
- What happens when a page has no main content (empty)? Create file with frontmatter only, log warning.
- What happens when an image URL is broken? Log error, continue with text content.
- What happens when the page requires JavaScript rendering? Assume pages are server-rendered (standard for help content). If JS-required pages are found, log and skip.
- What happens when a URL in links.md is malformed (like line 8 with `%hggns_topic_taxonomy%`)? Skip invalid URLs, log warning.
- What happens when duplicate URLs exist? Process only once, skip duplicates.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read URLs from `links.md` file (one URL per line).
- **FR-002**: System MUST fetch each URL concurrently with maximum parallelism.
- **FR-003**: System MUST extract main content area from each page (excluding navigation, headers, footers).
- **FR-004**: System MUST convert extracted HTML to clean markdown format.
- **FR-005**: System MUST generate YAML frontmatter for each page including: title, source_url, scraped_at.
- **FR-006**: System MUST preserve URL hierarchy as folder structure (e.g., `/hulp-nodig/aanbod/foo` becomes `output/hulp-nodig/aanbod/foo.md`).
- **FR-007**: System MUST download all images referenced in page content.
- **FR-008**: System MUST update image references in markdown to use local relative paths.
- **FR-009**: System MUST generate a JSON index file listing all scraped pages with metadata.
- **FR-010**: System MUST log errors and continue processing when individual pages fail.
- **FR-011**: System MUST skip invalid/malformed URLs with a logged warning.
- **FR-012**: System MUST process tables and convert them to markdown table syntax.
- **FR-013**: System MUST preserve ordered and unordered lists.
- **FR-014**: System MUST run locally without external service dependencies.

### Key Entities

- **HelpPage**: Represents a scraped help article with: source URL, title, markdown content, list of images, category hierarchy.
- **Image**: Represents a downloaded image with: original URL, local file path, associated page.
- **Index**: Collection of all scraped pages with: file path, title, source URL, category for each entry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scraper successfully processes at least 95% of valid URLs (allowing for dead links).
- **SC-002**: Total scraping time for ~387 pages is under 5 minutes on a standard connection.
- **SC-003**: Each scraped page contains readable markdown with no raw HTML tags visible.
- **SC-004**: All referenced images (where available) are downloaded locally.
- **SC-005**: The JSON index accurately reflects all scraped content.
- **SC-006**: A single command runs the complete scrape (no manual intervention required).
- **SC-007**: Folder structure matches the original URL hierarchy for easy navigation.

## Assumptions

- Bol.com Partner Platform help pages are server-rendered (no JavaScript required for main content).
- The site does not actively block scraping (no CAPTCHA, no aggressive rate limiting that would cause bans).
- All pages under partnerplatform.bol.com/nl/hulp-nodig/* follow a consistent HTML structure for content extraction.
- Images are hosted on accessible URLs (not behind authentication).
- The ~387 URLs in links.md represent the complete set of pages to scrape.
