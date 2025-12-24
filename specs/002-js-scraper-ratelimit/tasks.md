# Tasks: JavaScript-Rendered Content Scraping with Rate Limiting

**Input**: Design documents from `/specs/002-js-scraper-ratelimit/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: None (per constitution - manual verification only)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md: Flat single-file approach with `scraper.py` at repo root.

```text
scraper.py               # Main scraper script (single file)
links.md                 # Input: list of URLs to scrape
output/                  # Output directory (created at runtime)
```

---

## Phase 1: Setup (Dependencies & Configuration)

**Purpose**: Add Playwright dependency and configuration constants

- [X] T001 Update `requirements.txt` to add playwright>=1.40.0 in requirements.txt
- [X] T002 Run `pip install playwright && playwright install chromium` to install browser
- [X] T003 Add configuration constants (MAX_CONCURRENT=5, PAGE_TIMEOUT=30, RETRY_DELAYS=[2,4,8]) in scraper.py

---

## Phase 2: Foundational (Playwright Infrastructure)

**Purpose**: Core Playwright browser management that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add playwright imports (from playwright.async_api import async_playwright) in scraper.py
- [X] T005 Implement browser lifecycle management (launch/close in async context) in scraper.py
- [X] T006 Implement browser context pool creation (5 reusable contexts) in scraper.py
- [X] T007 Implement asyncio.Semaphore(5) for concurrency control in scraper.py
- [X] T008 Create new fetch_page_playwright() function replacing aiohttp fetch in scraper.py

**Checkpoint**: Foundation ready - can now fetch pages with Playwright and JS rendering

---

## Phase 3: User Story 1 - Scrape JavaScript-Rendered Pages (Priority: P1) 🎯 MVP

**Goal**: Successfully extract content from JavaScript-rendered pages

**Independent Test**: Run scraper against a single URL, verify markdown contains actual content (not "You are being redirected...")

### Implementation for User Story 1

- [X] T009 [US1] Implement page navigation with page.goto() in scraper.py
- [X] T010 [US1] Implement wait_for_load_state('networkidle', timeout=30000) in scraper.py
- [X] T011 [US1] Implement fallback to 'domcontentloaded' on networkidle timeout in scraper.py
- [X] T012 [US1] Implement page.content() to get rendered HTML in scraper.py
- [X] T013 [US1] Verify content is not redirect message before extraction in scraper.py
- [X] T014 [US1] Connect Playwright output to existing BeautifulSoup extraction pipeline in scraper.py

**Checkpoint**: User Story 1 complete - can fetch and extract JS-rendered content

---

## Phase 4: User Story 2 - Avoid Rate Limiting Errors (Priority: P1)

**Goal**: Control request rate to avoid 429 errors

**Independent Test**: Run scraper against all URLs, verify <5% get 429 errors

### Implementation for User Story 2

- [X] T015 [US2] Implement semaphore wrapper around all page operations in scraper.py
- [X] T016 [US2] Implement 429 detection from page response in scraper.py
- [X] T017 [US2] Implement retry loop with exponential backoff (3 retries, 2-4-8 seconds) in scraper.py
- [X] T018 [US2] Add retry_count tracking to error logging in scraper.py
- [X] T019 [US2] Implement max retry exhaustion handling (log and skip) in scraper.py

**Checkpoint**: User Stories 1+2 complete - JS rendering with rate limiting

---

## Phase 5: User Story 3 - Maintain Existing Functionality (Priority: P2)

**Goal**: Preserve all existing output formats and behaviors

**Independent Test**: Compare output format with v1 scraper, verify identical structure

### Implementation for User Story 3

- [X] T020 [US3] Verify YAML frontmatter generation unchanged in scraper.py
- [X] T021 [US3] Verify folder structure creation unchanged in scraper.py
- [X] T022 [US3] Update image URL extraction to work with Playwright-rendered HTML in scraper.py
- [X] T023 [US3] Keep aiohttp for image downloads (no change needed) in scraper.py
- [X] T024 [US3] Verify index.json generation includes all fields in scraper.py
- [X] T025 [US3] Add errors array to index.json per data-model.md in scraper.py

**Checkpoint**: User Stories 1+2+3 complete - full backward compatibility

---

## Phase 6: User Story 4 - Graceful Degradation (Priority: P3)

**Goal**: Handle errors gracefully, continue processing on failures

**Independent Test**: Add invalid URL to list, verify scraper continues and reports error

### Implementation for User Story 4

- [X] T026 [US4] Implement page load timeout handling (30s) in scraper.py
- [X] T027 [US4] Implement browser crash recovery (restart browser, skip URL) in scraper.py
- [X] T028 [US4] Implement memory management (restart browser after 100 pages) in scraper.py
- [X] T029 [US4] Update error logging with error_type categories in scraper.py
- [X] T030 [US4] Update final summary to show error breakdown by category in scraper.py

**Checkpoint**: All user stories complete - robust error handling

---

## Phase 7: Polish & Validation

**Purpose**: Final cleanup and validation against quickstart.md

- [X] T031 Remove or comment out unused aiohttp page-fetching code in scraper.py
- [X] T032 Run full scrape and verify against quickstart.md expectations
- [X] T033 Verify index.json contains 385+ entries with <5% errors
- [X] T034 Spot-check random .md files for actual content (not redirect messages)
- [X] T035 Verify completion time is under 30 minutes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Setup - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Foundational
- **Phase 4 (US2)**: Depends on US1 (needs page fetch to add rate limiting)
- **Phase 5 (US3)**: Depends on US2 (verify compatibility after all changes)
- **Phase 6 (US4)**: Depends on US3 (error handling builds on complete scraper)
- **Phase 7 (Polish)**: Depends on all user stories complete

### User Story Dependencies

Note: In this single-file project, user stories build on each other sequentially since all code is in scraper.py. The "independent testing" happens at checkpoints, not in parallel development.

- **User Story 1 (P1)**: Foundational → US1 (JS rendering)
- **User Story 2 (P1)**: US1 → US2 (rate limiting wraps around fetch)
- **User Story 3 (P2)**: US2 → US3 (verify compatibility)
- **User Story 4 (P3)**: US3 → US4 (error handling caps the feature)

### Within Each User Story

- Core functionality first
- Error handling after happy path works
- Logging/reporting last

### Parallel Opportunities

Since this is a single-file project, parallelism is limited. However:

- T001, T002 can run in parallel (different tools)
- Within US3: T020, T021, T024 are verification tasks that could run in parallel

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (Playwright infrastructure)
3. Complete Phase 3: User Story 1 (JS rendering)
4. Complete Phase 4: User Story 2 (rate limiting)
5. **STOP and VALIDATE**: Run scraper, verify pages have actual content, <5% 429 errors

At this point you have a working scraper that can fetch JS-rendered content without getting rate-limited.

### Full Feature (Add US3 + US4)

6. Complete Phase 5: User Story 3 (backward compatibility)
7. Complete Phase 6: User Story 4 (error handling)
8. Complete Phase 7: Polish and validate

### Single Developer Timeline

All 35 tasks in a single scraper.py file. Work sequentially through phases.

---

## Notes

- Single file: All implementation goes in `scraper.py`
- No testing infrastructure per constitution - manual verification only
- Per plan.md: Target <30 minutes for ~387 pages
- Per research.md: Use Semaphore(5) for concurrency, restart browser after 100 pages
- Per clarifications: 5 concurrent, 30s timeout, 3 retries with 2-4-8s backoff
- Commit after each phase checkpoint for easy rollback
