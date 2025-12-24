"""
Bol.com Partner Platform Help Scraper

Fetches help pages from Bol.com Partner Platform, extracts main content as
markdown with YAML frontmatter, downloads images locally, and generates a
JSON index.

Usage:
    python scraper.py

Input:
    links.md - List of URLs to scrape (one per line)

Output:
    output/ - Directory containing:
        - Markdown files mirroring URL hierarchy
        - images/ - Downloaded images
        - index.json - Index of all scraped pages
"""

import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

# Configuration
INPUT_FILE = Path("links.md")
OUTPUT_DIR = Path("output")
BASE_URL_PREFIX = "https://partnerplatform.bol.com/nl/"


class ProgressTracker:
    """Track and display scraping progress."""

    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self._lock = asyncio.Lock()

    async def update(self, success: bool) -> None:
        """Update progress counters and display."""
        async with self._lock:
            self.completed += 1
            if success:
                self.successful += 1
            else:
                self.failed += 1
            self._display()

    def _display(self) -> None:
        """Display progress bar."""
        pct = (self.completed / self.total) * 100 if self.total > 0 else 0
        bar_width = 30
        filled = int(bar_width * self.completed / self.total) if self.total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        status = f"\r  [{bar}] {self.completed}/{self.total} ({pct:.1f}%) | ✓ {self.successful} ✗ {self.failed}"
        sys.stdout.write(status)
        sys.stdout.flush()

    def finish(self) -> None:
        """Print newline after progress bar."""
        print()


def load_urls(filepath: Path) -> list[str]:
    """Load and validate URLs from input file.

    Reads URLs from a markdown file, extracting valid URLs and skipping
    comments, empty lines, and malformed URLs.

    Args:
        filepath: Path to the input file containing URLs.

    Returns:
        List of valid, unique URLs.
    """
    if not filepath.exists():
        print(f"Error: Input file not found: {filepath}")
        return []

    urls = []
    seen = set()
    url_pattern = re.compile(r'https?://[^\s<>\[\]()]+')

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and markdown headers/comments
            if not line or line.startswith('#') or line.startswith('<!--'):
                continue

            # Extract URLs from the line
            matches = url_pattern.findall(line)
            for url in matches:
                # Clean up URL (remove trailing punctuation)
                url = url.rstrip('.,;:)')

                # Validate URL structure
                try:
                    parsed = urlparse(url)
                    if not parsed.scheme or not parsed.netloc:
                        print(f"Warning: Malformed URL on line {line_num}: {url}")
                        continue
                except Exception:
                    print(f"Warning: Invalid URL on line {line_num}: {url}")
                    continue

                # Check for duplicates
                if url in seen:
                    print(f"Warning: Duplicate URL on line {line_num}: {url}")
                    continue

                seen.add(url)
                urls.append(url)

    print(f"Loaded {len(urls)} unique URLs from {filepath}")
    return urls


def url_to_path(url: str) -> Path:
    """Convert URL to local file path.

    Maps URL hierarchy to local folder structure.
    Example: https://partnerplatform.bol.com/nl/hulp-nodig/aanbod/verkooprechten
          -> output/hulp-nodig/aanbod/verkooprechten.md

    Args:
        url: The source URL.

    Returns:
        Local Path for the markdown file.
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')

    # Remove /nl/ prefix if present
    if path.startswith('nl/'):
        path = path[3:]

    # Handle empty path
    if not path:
        path = "index"

    # Convert to Path and add .md extension
    local_path = OUTPUT_DIR / f"{path}.md"
    return local_path


def create_output_dirs(urls: list[str]) -> None:
    """Create output directory structure based on URLs.

    Args:
        urls: List of URLs to create directories for.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Create images directory
    (OUTPUT_DIR / "images").mkdir(exist_ok=True)

    # Create directories for each URL
    created_dirs = set()
    for url in urls:
        local_path = url_to_path(url)
        parent_dir = local_path.parent
        if parent_dir not in created_dirs:
            parent_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.add(parent_dir)


async def fetch_page(
    session: aiohttp.ClientSession,
    url: str,
    progress: ProgressTracker | None = None
) -> tuple[str, str | None, str | None]:
    """Fetch a single page asynchronously.

    Args:
        session: aiohttp ClientSession for making requests.
        url: URL to fetch.
        progress: Optional progress tracker for updates.

    Returns:
        Tuple of (url, html_content, error_message).
        On success: (url, html_content, None)
        On failure: (url, None, error_message)
    """
    result: tuple[str, str | None, str | None]
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 404:
                result = (url, None, "404 Not Found")
            elif response.status >= 500:
                result = (url, None, f"Server error: {response.status}")
            elif response.status >= 400:
                result = (url, None, f"Client error: {response.status}")
            else:
                html = await response.text()
                result = (url, html, None)

    except asyncio.TimeoutError:
        result = (url, None, "Timeout after 30s")
    except aiohttp.ClientError as e:
        result = (url, None, f"Connection error: {type(e).__name__}")
    except Exception as e:
        result = (url, None, f"Unexpected error: {type(e).__name__}: {e}")

    if progress:
        await progress.update(success=(result[2] is None))

    return result


async def create_session() -> aiohttp.ClientSession:
    """Create aiohttp ClientSession with connection pooling.

    Returns:
        Configured ClientSession ready for concurrent requests.
    """
    connector = aiohttp.TCPConnector(
        limit=100,  # Max concurrent connections
        limit_per_host=50,  # Max connections per host
        ttl_dns_cache=300,  # DNS cache TTL in seconds
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    return aiohttp.ClientSession(connector=connector, headers=headers)


async def main() -> None:
    """Main entry point for the scraper."""
    print("Bol.com Partner Platform Help Scraper")
    print("=" * 40)

    # Load URLs from input file
    urls = load_urls(INPUT_FILE)
    if not urls:
        print("No URLs to process. Exiting.")
        return

    # Create output directory structure
    print("\nCreating output directories...")
    create_output_dirs(urls)
    print(f"Output directory: {OUTPUT_DIR.absolute()}")

    # Fetch all pages with progress tracking
    print(f"\nFetching {len(urls)} pages...")
    progress = ProgressTracker(len(urls))

    async with await create_session() as session:
        tasks = [fetch_page(session, url, progress) for url in urls]
        results = await asyncio.gather(*tasks)

    progress.finish()

    # Process results and write markdown files
    errors: list[tuple[str, str]] = []

    for url, html, error in results:
        if error:
            errors.append((url, error))
        else:
            # Write markdown file with basic content
            # (Will be enhanced with proper extraction in Phase 4)
            local_path = url_to_path(url)
            local_path.write_text(f"# Placeholder\n\nSource: {url}\n", encoding='utf-8')

    # Summary
    print(f"\n{'=' * 40}")
    print("Scrape complete!")
    print(f"  Total URLs:  {len(urls)}")
    print(f"  Successful:  {progress.successful}")
    print(f"  Failed:      {progress.failed}")
    print(f"  Skip (dup):  0")  # Duplicates already filtered in load_urls

    # Error summary
    if errors:
        print(f"\n{'=' * 40}")
        print("Failed URLs:")

        # Group errors by type
        error_types: dict[str, list[str]] = {}
        for url, error in errors:
            if error not in error_types:
                error_types[error] = []
            error_types[error].append(url)

        for error_type, urls_with_error in error_types.items():
            print(f"\n  {error_type} ({len(urls_with_error)} URLs):")
            for url in urls_with_error[:5]:
                print(f"    - {url}")
            if len(urls_with_error) > 5:
                print(f"    ... and {len(urls_with_error) - 5} more")
    else:
        print("\n  No errors encountered!")


if __name__ == "__main__":
    asyncio.run(main())
