# Feature Specification: JavaScript-Rendered Content Scraping with Rate Limiting

**Feature Branch**: `002-js-scraper-ratelimit`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "Add a rate limiting semaphore to avoid 429 errors and use browser automation to render JavaScript content"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scrape JavaScript-Rendered Pages (Priority: P1)

As a user, I want the scraper to successfully extract content from web pages that render their content using JavaScript, so that I can capture the actual help article text instead of empty redirect pages.

**Why this priority**: This is the core problem - the current scraper returns empty content because the target site uses client-side JavaScript rendering. Without this capability, no meaningful content can be extracted.

**Independent Test**: Run the scraper against a single JavaScript-rendered URL and verify the output markdown file contains the actual page content (not "You are being redirected...").

**Acceptance Scenarios**:

1. **Given** a URL that renders content via JavaScript, **When** the scraper processes this URL, **Then** the output markdown file contains the actual page content including headings, paragraphs, and formatted text.

2. **Given** a page that requires JavaScript to display its main content, **When** the scraper fetches the page, **Then** the scraper waits for the content to fully render before extracting it.

3. **Given** a page with dynamically loaded images, **When** the scraper processes the page, **Then** all visible images are detected and available for download.

---

### User Story 2 - Avoid Rate Limiting Errors (Priority: P1)

As a user, I want the scraper to control the rate of requests to the target server, so that the scraper can complete successfully without being blocked by 429 (Too Many Requests) errors.

**Why this priority**: Currently 255 out of 387 URLs fail due to rate limiting. This is equally critical as JS rendering - both are required for successful scraping.

**Independent Test**: Run the scraper against all URLs and verify that fewer than 5% of requests fail due to rate limiting errors.

**Acceptance Scenarios**:

1. **Given** a list of 387 URLs to scrape, **When** the scraper runs with rate limiting enabled, **Then** at least 95% of URLs are successfully fetched without 429 errors.

2. **Given** rate limiting is configured, **When** processing URLs concurrently, **Then** no more than the configured maximum number of requests are active at any time.

3. **Given** the server returns a 429 error, **When** the scraper encounters this response, **Then** it waits before retrying the request (up to a maximum retry count).

---

### User Story 3 - Maintain Existing Scraper Functionality (Priority: P2)

As a user, I want all existing scraper features to continue working, so that I don't lose any current capabilities when adding the new features.

**Why this priority**: Important for ensuring no regression, but secondary to the core new functionality.

**Independent Test**: Run the enhanced scraper and verify that output format, folder structure, image downloading, and index generation all work as before.

**Acceptance Scenarios**:

1. **Given** the enhanced scraper, **When** processing pages, **Then** markdown files are created with the same YAML frontmatter structure as before.

2. **Given** pages with images, **When** the scraper processes them, **Then** images are downloaded to output/images/ and markdown references are updated to local paths.

3. **Given** a completed scrape, **When** reviewing the output, **Then** index.json is generated with all successfully scraped pages.

---

### User Story 4 - Graceful Degradation (Priority: P3)

As a user, I want the scraper to handle errors gracefully and continue processing other URLs, so that a single page failure doesn't stop the entire scrape.

**Why this priority**: Nice-to-have resilience feature that improves reliability but isn't core functionality.

**Independent Test**: Introduce an invalid URL into the list and verify the scraper continues processing other URLs and reports the failure.

**Acceptance Scenarios**:

1. **Given** a URL that times out during rendering, **When** the timeout is exceeded, **Then** the scraper logs the error and continues with the next URL.

2. **Given** a page that fails to load, **When** the scraper encounters the error, **Then** the error is logged with the URL and reason, and processing continues.

3. **Given** all URLs have been attempted, **When** the scrape completes, **Then** a summary shows total attempted, successful, and failed counts with error categories.

---

### Edge Cases

- What happens when a page takes longer than expected to render JavaScript content? (Configurable timeout with reasonable default)
- How does the system handle pages that never finish loading? (Timeout and skip after configured duration)
- What happens if the browser automation component crashes? (Log error, attempt restart, skip affected URL)
- How does the scraper handle pages that require login/authentication? (Skip and log as "requires authentication")
- What happens when memory usage grows too high with browser automation? (Periodic browser restart after N pages)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render JavaScript content before extracting page content
- **FR-002**: System MUST limit concurrent requests to a configurable maximum number (default: 5)
- **FR-003**: System MUST wait for page content to fully render before extraction
- **FR-004**: System MUST retry failed requests due to rate limiting (429 errors) with exponential backoff (3 retries, 2-4-8 seconds)
- **FR-005**: System MUST timeout page loads after a configurable duration (default: 30 seconds)
- **FR-006**: System MUST continue processing other URLs when a single URL fails
- **FR-007**: System MUST log all errors with URL and error type for debugging
- **FR-008**: System MUST preserve existing output format (YAML frontmatter + markdown content)
- **FR-009**: System MUST preserve existing folder structure mirroring URL hierarchy
- **FR-010**: System MUST preserve existing image downloading functionality
- **FR-011**: System MUST preserve existing index.json generation
- **FR-012**: System MUST provide progress feedback during scraping
- **FR-013**: System MUST report final summary with success/failure counts

### Key Entities

- **ScrapedPage**: Represents a successfully scraped page with title, content, images, source URL, and local path
- **ScrapeError**: Represents a failed scrape attempt with URL, error type, error message, and timestamp
- **RateLimitConfig**: Configuration for rate limiting including max concurrent requests, retry count, and backoff settings
- **RenderConfig**: Configuration for page rendering including timeout duration and wait conditions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of URLs are successfully scraped (compared to ~34% currently)
- **SC-002**: Scraped pages contain actual content (not redirect messages) in at least 90% of successful scrapes
- **SC-003**: Complete scrape of ~387 pages completes within 30 minutes
- **SC-004**: Rate limiting errors (429) occur in fewer than 5% of requests
- **SC-005**: System provides progress updates at least every 10 pages processed
- **SC-006**: All existing output formats remain compatible with previous scraper version
- **SC-007**: Error reports clearly identify failure reasons for troubleshooting

## Clarifications

### Session 2025-12-24

- Q: What should the default concurrent request limit be? → A: 5 concurrent requests (balanced speed/politeness, ~1 hour completion, low memory usage)
- Q: What retry behavior for 429 errors? → A: 3 retries with 2-4-8 second exponential backoff (~14s max wait per URL)
- Q: What page render timeout? → A: 30 seconds (standard timeout, balances completeness with speed)

## Assumptions

- The target website does not require authentication to access help pages
- JavaScript rendering completes within a reasonable timeout (30 seconds default)
- The website's rate limiting can be avoided with controlled concurrency (5 concurrent requests default)
- Browser automation is acceptable for this use case (not blocked by bot detection)
- Local machine has sufficient resources to run browser automation (memory, CPU)
- Network connectivity is stable throughout the scrape operation

## Out of Scope

- Handling websites that require login/authentication
- Bypassing CAPTCHAs or advanced bot detection
- Scraping content from multiple different websites (single target site only)
- Scheduling or automated recurring scrapes
- Real-time content updates or change detection
- API-based content extraction (browser rendering only)
