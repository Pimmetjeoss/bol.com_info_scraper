# Tasks: Bol.com Partner Platform Help Scraper

**Input**: Design documents from `/specs/001-bol-help-scraper/`
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

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project structure and install dependencies

- [X] T001 Create `requirements.txt` with dependencies: aiohttp>=3.9.0, beautifulsoup4>=4.12, lxml>=5.0, markdownify>=0.11
- [X] T002 Create empty `scraper.py` file at repository root with module docstring
- [X] T003 Verify `links.md` exists with URL list (input file)

---

## Phase 2: Foundational (Core Async Infrastructure)

**Purpose**: Core async HTTP infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement async main entry point with `asyncio.run()` in scraper.py
- [X] T005 Implement URL loading function to read and validate URLs from links.md in scraper.py
- [X] T006 Implement aiohttp ClientSession creation with connection pooling in scraper.py
- [X] T007 Implement async page fetcher with error handling (404, 5xx, connection errors) in scraper.py
- [X] T008 Implement URL-to-path mapping function (URL hierarchy → local folder structure) in scraper.py
- [X] T009 Implement output directory creation logic in scraper.py

**Checkpoint**: Foundation ready - can now fetch pages and map URLs to paths

---

## Phase 3: User Story 1 - Bulk Scrape All Help Pages (Priority: P1) 🎯 MVP

**Goal**: Run a single command that fetches all ~387 help pages concurrently

**Independent Test**: Run `python scraper.py`, verify markdown files are created for each valid URL

### Implementation for User Story 1

- [X] T010 [US1] Implement concurrent page fetching with asyncio.gather() for all URLs in scraper.py
- [X] T011 [US1] Implement folder structure creation mirroring URL hierarchy in scraper.py
- [X] T012 [US1] Implement basic markdown file writing (content placeholder) per page in scraper.py
- [X] T013 [US1] Implement progress logging showing pages fetched/total in scraper.py
- [X] T014 [US1] Implement error summary at end (failed URLs, skip counts) in scraper.py
- [X] T015 [US1] Add duplicate URL detection and skip logic in scraper.py
- [X] T016 [US1] Add malformed URL detection and skip logic in scraper.py

**Checkpoint**: User Story 1 complete - can bulk fetch all pages and create file structure

---

## Phase 4: User Story 2 - Extract Structured Content (Priority: P1)

**Goal**: Extract clean markdown with YAML frontmatter from each page

**Independent Test**: Open any scraped .md file, verify YAML frontmatter and readable markdown content

### Implementation for User Story 2

- [ ] T017 [US2] Implement HTML content extraction using BeautifulSoup (main content selector cascade) in scraper.py
- [ ] T018 [US2] Implement unwanted element stripping (nav, header, footer, aside, script, style) in scraper.py
- [ ] T019 [US2] Implement HTML-to-markdown conversion using markdownify in scraper.py
- [ ] T020 [US2] Implement YAML frontmatter generation (title, source_url, scraped_at, category) in scraper.py
- [ ] T021 [US2] Implement title extraction (from `<title>` or `<h1>`) in scraper.py
- [ ] T022 [US2] Implement category extraction from URL path segments in scraper.py
- [ ] T023 [US2] Update file writing to use extracted content with frontmatter in scraper.py
- [ ] T024 [US2] Handle empty content pages (frontmatter only with warning) in scraper.py

**Checkpoint**: User Stories 1+2 complete - full content extraction with clean markdown output

---

## Phase 5: User Story 3 - Download Images Locally (Priority: P2)

**Goal**: Download all images and update markdown references to local paths

**Independent Test**: Find a page with images, verify images downloaded to output/images/, markdown references use local paths

### Implementation for User Story 3

- [ ] T025 [US3] Implement image URL extraction from page content in scraper.py
- [ ] T026 [US3] Implement image filename generation (handle duplicates with hash suffix) in scraper.py
- [ ] T027 [US3] Implement async image downloading with aiohttp in scraper.py
- [ ] T028 [US3] Implement output/images/ directory creation in scraper.py
- [ ] T029 [US3] Implement markdown image reference rewriting to use local relative paths in scraper.py
- [ ] T030 [US3] Implement image download error handling (log failure, keep original URL) in scraper.py
- [ ] T031 [US3] Add image download progress logging in scraper.py

**Checkpoint**: User Stories 1+2+3 complete - fully self-contained output with local images

---

## Phase 6: User Story 4 - Generate Index File (Priority: P2)

**Goal**: Generate JSON index of all scraped content for programmatic access

**Independent Test**: Verify output/index.json exists with entries matching scraped page count

### Implementation for User Story 4

- [ ] T032 [US4] Implement page data collection during scrape (title, url, path, category) in scraper.py
- [ ] T033 [US4] Implement index.json structure creation (generated_at, total_pages, total_images, pages) in scraper.py
- [ ] T034 [US4] Implement index.json file writing with json.dump() in scraper.py
- [ ] T035 [US4] Add index generation summary to final output logging in scraper.py

**Checkpoint**: All user stories complete - full scraper functionality

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and any improvements

- [ ] T036 Run full scrape and verify output against quickstart.md expectations
- [ ] T037 Verify index.json contains ~385+ entries
- [ ] T038 Verify folder structure matches URL hierarchy
- [ ] T039 Spot-check random .md files for content quality
- [ ] T040 Verify images are downloaded and referenced correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Setup - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Foundational
- **Phase 4 (US2)**: Depends on US1 (needs page fetch infrastructure)
- **Phase 5 (US3)**: Depends on US2 (needs content extraction infrastructure)
- **Phase 6 (US4)**: Depends on US2 (needs page data collection)
- **Phase 7 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundational → US1 (bulk fetching)
- **User Story 2 (P1)**: US1 → US2 (content extraction builds on fetching)
- **User Story 3 (P2)**: US2 → US3 (image handling builds on content extraction)
- **User Story 4 (P2)**: US2 → US4 (index needs extracted metadata)

Note: US3 and US4 could run in parallel after US2 completes, but since this is a single-file script, sequential is simpler.

### Within Each User Story

- Core functionality first
- Error handling after happy path works
- Logging/reporting last

### Parallel Opportunities

Since this is a single-file project, most parallelism happens at runtime (async fetching), not at development time. However:

- T001, T002, T003 can be done in parallel (different files)
- Within each phase, tasks marked [P] could be split if multiple developers

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (async infrastructure)
3. Complete Phase 3: User Story 1 (bulk fetching)
4. Complete Phase 4: User Story 2 (content extraction)
5. **STOP and VALIDATE**: Run scraper, verify markdown files with content

At this point you have a working scraper that fetches and extracts content.

### Full Feature (Add US3 + US4)

6. Complete Phase 5: User Story 3 (image downloading)
7. Complete Phase 6: User Story 4 (index generation)
8. Complete Phase 7: Polish and validate

### Single Developer Timeline

All 40 tasks in a single scraper.py file. Work sequentially through phases.

---

## Notes

- Single file: All implementation goes in `scraper.py`
- No testing infrastructure per constitution - manual verification only
- Per plan.md: Target <5 minutes for ~387 pages
- Per research.md: Use Semaphore(50-100) fallback if connection exhaustion occurs
- Commit after each phase checkpoint for easy rollback
