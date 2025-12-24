<!--
SYNC IMPACT REPORT
==================
Version change: N/A → 1.0.0 (initial)
Modified principles: N/A (initial creation)
Added sections:
  - Core Principles (4 principles)
  - Project Scope
  - Development Workflow
  - Governance
Removed sections: N/A
Templates status:
  - .specify/templates/plan-template.md: ✅ Compatible (no updates required)
  - .specify/templates/spec-template.md: ✅ Compatible (no updates required)
  - .specify/templates/tasks-template.md: ✅ Compatible (testing is optional per template)
Follow-up TODOs: None
-->

# Bol-scraper Constitution

## Core Principles

### I. Simplicity First

Working code takes priority over perfect code. Every implementation MUST use the
simplest approach that achieves the goal.

- Favor direct, readable code over abstractions
- No premature optimization
- No over-engineering for hypothetical future needs
- If it works and is readable, it ships

**Rationale**: This is a one-time scraper. Maintainability debt is irrelevant.

### II. No Testing Required

This project explicitly opts out of automated testing. Manual verification is
sufficient.

- No unit tests
- No integration tests
- No test infrastructure
- Validation happens by running the scraper and inspecting output

**Rationale**: One-time execution means test investment has zero ROI.

### III. Maximum Performance

Speed is the primary optimization target. The scraper MUST be as fast as possible
with aggressive concurrency.

- No rate limiting unless absolutely required to avoid bans
- Maximum concurrent requests within system/target limits
- Async/parallel processing everywhere applicable
- Memory usage is secondary to speed

**Rationale**: Faster execution = faster results. Time is the constraint.

### IV. Pragmatic Execution

Get it done. Ship working output over polished process.

- Skip ceremony: no extensive documentation, no elaborate Git workflows
- Direct problem-solving over process adherence
- Fix issues by whatever means necessary
- "Good enough" is the quality bar

**Rationale**: Results matter. Process exists only to serve results.

## Project Scope

This is a one-time web scraper for Bol.com data extraction.

- **Purpose**: Extract product/listing data from Bol.com
- **Lifecycle**: Single execution, not a maintained product
- **Output**: Structured data (likely JSON/CSV)
- **Success criteria**: Complete data extraction that runs to completion

## Development Workflow

Given the pragmatic nature of this project:

- **Commits**: As needed, no enforced message format
- **Branches**: Optional; direct main commits acceptable
- **Code review**: Not required
- **Documentation**: Inline comments only where code is non-obvious

## Governance

This constitution defines the development approach for the Bol-scraper project.

- Principles apply to all code in this repository
- Deviations allowed when explicitly justified by practical necessity
- No formal amendment process—update directly as needs change

**Version**: 1.0.0 | **Ratified**: 2025-12-24 | **Last Amended**: 2025-12-24
