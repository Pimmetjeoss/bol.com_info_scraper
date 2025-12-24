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
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Configuration
INPUT_FILE = Path("links.md")
OUTPUT_DIR = Path("output")
IMAGES_DIR = OUTPUT_DIR / "images"
INDEX_FILE = OUTPUT_DIR / "index.json"
BASE_URL_PREFIX = "https://partnerplatform.bol.com/nl/"

# Rate limiting and browser configuration
MAX_CONCURRENT = 1  # Maximum concurrent browser contexts (ultra-conservative to avoid 429s)
PAGE_TIMEOUT = 30  # Page load timeout in seconds
RETRY_COUNT = 3  # Maximum retries for 429 errors
RETRY_DELAYS = [10, 20, 40]  # Exponential backoff delays in seconds (increased from [2,4,8])


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
        bar = "#" * filled + "-" * (bar_width - filled)
        status = f"\r  [{bar}] {self.completed}/{self.total} ({pct:.1f}%) | OK: {self.successful} FAIL: {self.failed}"
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


# DEPRECATED: Replaced by fetch_page_playwright() for JavaScript rendering support
# Kept for reference only - this function is no longer used in the scraper
#
# async def fetch_page(
#     session: aiohttp.ClientSession,
#     url: str,
#     progress: ProgressTracker | None = None
# ) -> tuple[str, str | None, str | None]:
#     """Fetch a single page asynchronously.
#
#     Args:
#         session: aiohttp ClientSession for making requests.
#         url: URL to fetch.
#         progress: Optional progress tracker for updates.
#
#     Returns:
#         Tuple of (url, html_content, error_message).
#         On success: (url, html_content, None)
#         On failure: (url, None, error_message)
#     """
#     result: tuple[str, str | None, str | None]
#     try:
#         async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
#             if response.status == 404:
#                 result = (url, None, "404 Not Found")
#             elif response.status >= 500:
#                 result = (url, None, f"Server error: {response.status}")
#             elif response.status >= 400:
#                 result = (url, None, f"Client error: {response.status}")
#             else:
#                 html = await response.text()
#                 result = (url, html, None)
#
#     except asyncio.TimeoutError:
#         result = (url, None, "Timeout after 30s")
#     except aiohttp.ClientError as e:
#         result = (url, None, f"Connection error: {type(e).__name__}")
#     except Exception as e:
#         result = (url, None, f"Unexpected error: {type(e).__name__}: {e}")
#
#     if progress:
#         await progress.update(success=(result[2] is None))
#
#     return result


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


# Content selector cascade for main content extraction
CONTENT_SELECTORS = [
    'main article',
    'main',
    'article',
    '.content',
    '.article-content',
    '.help-content',
    '#content',
    '[role="main"]',
]

# Elements to strip from content
UNWANTED_ELEMENTS = [
    'nav', 'header', 'footer', 'aside', 'script', 'style',
    'noscript', 'iframe', 'form', '.cookie-banner', '.popup',
    '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
]


def extract_main_content(html: str) -> BeautifulSoup | None:
    """Extract main content area using selector cascade.

    Tries multiple selectors in order to find the main content area,
    excluding navigation, headers, footers, and other unwanted elements.

    Args:
        html: Raw HTML content of the page.

    Returns:
        BeautifulSoup element containing the main content, or None if not found.
    """
    soup = BeautifulSoup(html, 'lxml')

    # Try each selector in order
    content = None
    for selector in CONTENT_SELECTORS:
        content = soup.select_one(selector)
        if content:
            break

    # Fallback to body if no content found
    if not content:
        content = soup.body

    if not content:
        return None

    return content


def strip_unwanted_elements(content: BeautifulSoup) -> None:
    """Remove unwanted elements from content in-place.

    Removes navigation, headers, footers, scripts, styles, and other
    elements that should not be included in the extracted content.

    Args:
        content: BeautifulSoup element to clean (modified in place).
    """
    for selector in UNWANTED_ELEMENTS:
        for element in content.select(selector):
            element.decompose()


def extract_title(html: str, content: BeautifulSoup | None) -> str:
    """Extract page title from HTML.

    Tries to extract title from:
    1. First <h1> in content
    2. <title> tag
    3. Falls back to "Untitled"

    Args:
        html: Raw HTML content.
        content: Extracted main content BeautifulSoup element.

    Returns:
        Extracted title string.
    """
    # Try h1 in content first
    if content:
        h1 = content.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            if title:
                return title

    # Fall back to <title> tag
    soup = BeautifulSoup(html, 'lxml')
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Clean up common suffixes
        for suffix in [' | Bol.com Partner Platform', ' - Bol.com', ' | Bol.com']:
            if title.endswith(suffix):
                title = title[:-len(suffix)]
        if title:
            return title

    return "Untitled"


def extract_category(url: str) -> list[str]:
    """Extract category hierarchy from URL path.

    Args:
        url: Source URL.

    Returns:
        List of category path segments.
    """
    parsed = urlparse(url)
    path = parsed.path.strip('/')

    # Remove /nl/ prefix if present
    if path.startswith('nl/'):
        path = path[3:]

    if not path:
        return []

    # Split into segments
    segments = [seg for seg in path.split('/') if seg]
    return segments


def html_to_markdown(content: BeautifulSoup) -> str:
    """Convert BeautifulSoup content to Markdown.

    Args:
        content: BeautifulSoup element containing HTML content.

    Returns:
        Markdown string.
    """
    # Convert to markdown with markdownify
    markdown = md(
        str(content),
        heading_style='atx',  # Use # style headings
        bullets='-',  # Use - for unordered lists
        strip=['script', 'style'],  # Extra safety stripping
    )

    # Clean up excessive whitespace
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()

    return markdown


def extract_image_urls(content: BeautifulSoup, page_url: str) -> list[str]:
    """Extract all image URLs from page content.

    Args:
        content: BeautifulSoup element containing the page content.
        page_url: Base URL for resolving relative image URLs.

    Returns:
        List of absolute image URLs.
    """
    if content is None:
        return []

    image_urls = []
    for img in content.find_all('img'):
        src = img.get('src')
        if not src:
            continue

        # Skip data URLs
        if src.startswith('data:'):
            continue

        # Convert relative URLs to absolute
        absolute_url = urljoin(page_url, src)

        # Only include HTTP(S) URLs
        if absolute_url.startswith(('http://', 'https://')):
            image_urls.append(absolute_url)

    return image_urls


def generate_image_filename(url: str, existing_names: set[str]) -> str:
    """Generate unique filename for an image.

    Uses the original filename from URL, adding a hash suffix if needed
    to handle duplicates.

    Args:
        url: Image URL.
        existing_names: Set of already used filenames.

    Returns:
        Unique filename for the image.
    """
    parsed = urlparse(url)
    path = parsed.path

    # Extract filename from path
    original_name = path.split('/')[-1] if path else 'image'

    # Clean up filename
    if not original_name or original_name == '/':
        original_name = 'image'

    # Ensure we have an extension
    if '.' not in original_name:
        original_name += '.jpg'

    # Check if name already exists
    if original_name not in existing_names:
        return original_name

    # Add hash suffix for duplicates
    name_part, ext = original_name.rsplit('.', 1)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    unique_name = f"{name_part}_{url_hash}.{ext}"

    return unique_name


async def download_image(
    session: aiohttp.ClientSession,
    url: str,
    filename: str,
) -> tuple[str, str | None, str | None]:
    """Download a single image asynchronously.

    Args:
        session: aiohttp ClientSession for making requests.
        url: Image URL to download.
        filename: Local filename to save as.

    Returns:
        Tuple of (url, local_path, error_message).
        On success: (url, local_path, None)
        On failure: (url, None, error_message)
    """
    local_path = IMAGES_DIR / filename

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status >= 400:
                return (url, None, f"HTTP {response.status}")

            content = await response.read()
            local_path.write_bytes(content)
            return (url, str(local_path), None)

    except asyncio.TimeoutError:
        return (url, None, "Timeout")
    except aiohttp.ClientError as e:
        return (url, None, f"Connection error: {type(e).__name__}")
    except Exception as e:
        return (url, None, f"Error: {type(e).__name__}")


async def download_all_images(
    session: aiohttp.ClientSession,
    image_urls: list[str],
) -> dict[str, str]:
    """Download all images and return URL to local path mapping.

    Args:
        session: aiohttp ClientSession for making requests.
        image_urls: List of image URLs to download.

    Returns:
        Dict mapping original URL to local relative path.
        Failed downloads are not included in the mapping.
    """
    if not image_urls:
        return {}

    # Ensure images directory exists
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique filenames
    existing_names: set[str] = set()
    url_to_filename: dict[str, str] = {}

    for url in image_urls:
        filename = generate_image_filename(url, existing_names)
        existing_names.add(filename)
        url_to_filename[url] = filename

    # Download all images
    tasks = [
        download_image(session, url, filename)
        for url, filename in url_to_filename.items()
    ]
    results = await asyncio.gather(*tasks)

    # Build URL to local path mapping
    url_to_local: dict[str, str] = {}
    success_count = 0
    fail_count = 0

    for url, local_path, error in results:
        if error:
            fail_count += 1
        else:
            success_count += 1
            # Use relative path from output directory
            url_to_local[url] = f"images/{url_to_filename[url]}"

    if image_urls:
        print(f"  Downloaded {success_count}/{len(image_urls)} images", end="")
        if fail_count > 0:
            print(f" ({fail_count} failed)", end="")
        print()

    return url_to_local


def rewrite_image_references(markdown: str, url_mapping: dict[str, str]) -> str:
    """Rewrite image URLs in markdown to use local paths.

    Args:
        markdown: Markdown content with original image URLs.
        url_mapping: Dict mapping original URL to local relative path.

    Returns:
        Markdown with image URLs replaced with local paths.
    """
    for original_url, local_path in url_mapping.items():
        markdown = markdown.replace(original_url, local_path)

    return markdown


def categorize_error(error_message: str) -> str:
    """Categorize an error message into an error type.

    Args:
        error_message: The error message string.

    Returns:
        Error category: "timeout", "rate_limit", "network", "parse", or "unknown".
    """
    error_lower = error_message.lower()

    if "timeout" in error_lower:
        return "timeout"
    elif "429" in error_message or "rate limit" in error_lower:
        return "rate_limit"
    elif "404" in error_message or "server error" in error_lower or "client error" in error_lower:
        return "network"
    elif "connection" in error_lower or "network" in error_lower:
        return "network"
    elif "parse" in error_lower or "render" in error_lower:
        return "parse"
    else:
        return "unknown"


def generate_index(
    pages: list[dict],
    total_images: int,
    errors: list[dict] | None = None,
) -> dict:
    """Generate index.json structure.

    Args:
        pages: List of page data dictionaries with title, source_url, local_path, category.
        total_images: Total count of downloaded images.
        errors: Optional list of error summaries with url, error_type, retries.

    Returns:
        Dictionary structure for index.json.
    """
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    index_data = {
        "generated_at": generated_at,
        "total_pages": len(pages),
        "total_images": total_images,
        "pages": pages,
    }

    if errors:
        index_data["errors"] = errors

    return index_data


def write_index(index_data: dict) -> None:
    """Write index.json file.

    Args:
        index_data: Index data dictionary to write.
    """
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)


def generate_frontmatter(title: str, source_url: str, category: list[str]) -> str:
    """Generate YAML frontmatter for markdown file.

    Args:
        title: Page title.
        source_url: Original URL.
        category: Category path segments.

    Returns:
        YAML frontmatter string with --- delimiters.
    """
    scraped_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Build category YAML
    if category:
        category_yaml = '\n'.join(f'  - {cat}' for cat in category)
        category_section = f'category:\n{category_yaml}'
    else:
        category_section = 'category: []'

    # Escape title for YAML (handle quotes)
    safe_title = title.replace('"', '\\"')

    frontmatter = f'''---
title: "{safe_title}"
source_url: "{source_url}"
scraped_at: "{scraped_at}"
{category_section}
---'''

    return frontmatter


async def fetch_page_playwright(
    browser: Browser,
    semaphore: asyncio.Semaphore,
    url: str,
    progress: ProgressTracker | None = None
) -> tuple[str, str | None, str | None, int]:
    """Fetch a single page using Playwright with JavaScript rendering.

    Implements rate limiting via semaphore and retry logic for 429 errors.

    Args:
        browser: Playwright Browser instance.
        semaphore: Semaphore for concurrency control.
        url: URL to fetch.
        progress: Optional progress tracker for updates.

    Returns:
        Tuple of (url, html_content, error_message, retry_count).
        On success: (url, html_content, None, retry_count)
        On failure: (url, None, error_message, retry_count)
    """
    result: tuple[str, str | None, str | None, int]
    retry_count = 0

    async with semaphore:
        # Create a new page for this request
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Retry logic for 429 errors
            for attempt in range(RETRY_COUNT):
                retry_count = attempt
                try:
                    # Navigate to the page
                    response = await page.goto(url, timeout=PAGE_TIMEOUT * 1000)

                    if response is None:
                        result = (url, None, "Navigation failed - no response", retry_count)
                        break

                    # Check for rate limiting
                    if response.status == 429:
                        if attempt < RETRY_COUNT - 1:
                            delay = RETRY_DELAYS[attempt]
                            await asyncio.sleep(delay)
                            continue
                        else:
                            result = (url, None, f"429 Too Many Requests after {RETRY_COUNT} retries", RETRY_COUNT)
                            break

                    # Check for other errors
                    if response.status == 404:
                        result = (url, None, "404 Not Found", retry_count)
                        break
                    elif response.status >= 500:
                        result = (url, None, f"Server error: {response.status}", retry_count)
                        break
                    elif response.status >= 400:
                        result = (url, None, f"Client error: {response.status}", retry_count)
                        break

                    # Wait for content to load
                    try:
                        await page.wait_for_load_state('networkidle', timeout=PAGE_TIMEOUT * 1000)
                    except Exception:
                        # Fallback to domcontentloaded if networkidle times out
                        try:
                            await page.wait_for_load_state('domcontentloaded')
                        except Exception as e:
                            result = (url, None, f"Page load timeout: {type(e).__name__}", retry_count)
                            break

                    # Get rendered HTML
                    html = await page.content()

                    # Verify content is not redirect message
                    if "You are being redirected" in html or "wordt doorgestuurd" in html.lower():
                        result = (url, None, "JavaScript rendering failed - redirect page", retry_count)
                        break

                    result = (url, html, None, retry_count)
                    break

                except Exception as e:
                    if attempt < RETRY_COUNT - 1 and "429" in str(e):
                        delay = RETRY_DELAYS[attempt]
                        await asyncio.sleep(delay)
                        continue
                    result = (url, None, f"Error: {type(e).__name__}: {e}", retry_count)
                    break

        except asyncio.TimeoutError:
            result = (url, None, f"Timeout after {PAGE_TIMEOUT}s", retry_count)
        except Exception as e:
            result = (url, None, f"Unexpected error: {type(e).__name__}: {e}", retry_count)
        finally:
            # Clean up
            await page.close()
            await context.close()

    if progress:
        await progress.update(success=(result[1] is not None))

    return result


def extract_page_content(html: str, url: str) -> tuple[str, str, bool, list[str]]:
    """Extract and convert page content to markdown with frontmatter.

    Args:
        html: Raw HTML content.
        url: Source URL.

    Returns:
        Tuple of (markdown_content, title, is_empty, image_urls).
        is_empty is True if no meaningful content was extracted.
        image_urls contains all images found in the content.
    """
    # Extract main content
    content = extract_main_content(html)

    # Extract title before stripping elements
    title = extract_title(html, content)

    # Extract category from URL
    category = extract_category(url)

    # Generate frontmatter
    frontmatter = generate_frontmatter(title, url, category)

    if content is None:
        # No content found at all
        return f"{frontmatter}\n\n<!-- Warning: No content could be extracted from this page -->\n", title, True, []

    # Extract image URLs before stripping elements
    image_urls = extract_image_urls(content, url)

    # Strip unwanted elements
    strip_unwanted_elements(content)

    # Convert to markdown
    markdown = html_to_markdown(content)

    # Check if content is empty after extraction
    if not markdown or len(markdown.strip()) < 10:
        return f"{frontmatter}\n\n<!-- Warning: Page content appears to be empty or minimal -->\n", title, True, image_urls

    # Combine frontmatter and content
    full_content = f"{frontmatter}\n\n{markdown}"

    return full_content, title, False, image_urls


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

    # Fetch all pages with progress tracking using Playwright
    print(f"\nFetching {len(urls)} pages with Playwright...")
    progress = ProgressTracker(len(urls))

    # Process pages in batches of 100 to manage memory
    BATCH_SIZE = 100
    all_results = []

    async with async_playwright() as p:
        for batch_start in range(0, len(urls), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(urls))
            batch_urls = urls[batch_start:batch_end]
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (len(urls) + BATCH_SIZE - 1) // BATCH_SIZE

            if total_batches > 1:
                print(f"\n  Processing batch {batch_num}/{total_batches} ({len(batch_urls)} URLs)...")

            try:
                # Launch browser for this batch
                browser = await p.chromium.launch(headless=True)

                # Create semaphore for rate limiting
                semaphore = asyncio.Semaphore(MAX_CONCURRENT)

                # Fetch batch of pages
                tasks = [fetch_page_playwright(browser, semaphore, url, progress) for url in batch_urls]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Close browser to free memory
                await browser.close()

                all_results.extend(batch_results)

            except Exception as e:
                print(f"\n\nBrowser crashed in batch {batch_num}: {type(e).__name__}: {e}")
                print("Continuing with next batch...")
                # Create error results for URLs in this batch
                for url in batch_urls:
                    all_results.append((url, None, f"Browser crash: {type(e).__name__}", 0))

        results = all_results
        progress.finish()

        # Process results and collect image URLs
        print("\nExtracting content...")
        errors: list[tuple[str, str, int]] = []  # (url, error_message, retry_count)
        empty_pages: list[str] = []
        all_image_urls: set[str] = set()
        # page_data: (url, markdown_content, image_urls, title, category)
        page_data: list[tuple[str, str, list[str], str, list[str]]] = []

        for i, result in enumerate(results):
            # Handle exceptions from gather(return_exceptions=True)
            if isinstance(result, Exception):
                url = urls[i] if i < len(urls) else "unknown"
                errors.append((url, f"Exception: {type(result).__name__}: {result}", 0))
                continue

            url, html, error, retry_count = result

            if error:
                errors.append((url, error, retry_count))
            else:
                # Extract content and convert to markdown
                markdown_content, title, is_empty, image_urls = extract_page_content(html, url)

                # Extract category from URL for index
                category = extract_category(url)

                # Track empty pages
                if is_empty:
                    empty_pages.append(url)

                # Collect image URLs
                all_image_urls.update(image_urls)

                # Store page data for later writing (including title and category for index)
                page_data.append((url, markdown_content, image_urls, title, category))

        # Download all images using aiohttp
        total_images = len(all_image_urls)
        if total_images > 0:
            print(f"\nDownloading {total_images} images...")
            async with await create_session() as session:
                url_to_local = await download_all_images(session, list(all_image_urls))
        else:
            print("\nNo images found to download.")
            url_to_local = {}

    # Write markdown files with rewritten image references and collect index entries
    print("\nWriting markdown files...")
    images_rewritten = 0
    index_entries: list[dict] = []

    for url, markdown_content, image_urls, title, category in page_data:
        # Rewrite image references if we have a mapping
        if url_to_local and image_urls:
            markdown_content = rewrite_image_references(markdown_content, url_to_local)
            images_rewritten += len([u for u in image_urls if u in url_to_local])

        # Write markdown file
        local_path = url_to_path(url)
        local_path.write_text(markdown_content, encoding='utf-8')

        # Collect page data for index (T032)
        # local_path is relative to output dir for the index
        relative_path = str(local_path.relative_to(OUTPUT_DIR))
        index_entries.append({
            "title": title,
            "source_url": url,
            "local_path": relative_path,
            "category": category,
        })

    # Generate and write index.json (T033, T034)
    print("\nGenerating index.json...")
    # Create error summaries for index
    error_summaries = []
    for url, error_message, retry_count in errors:
        error_summaries.append({
            "url": url,
            "error_type": categorize_error(error_message),
            "retries": retry_count,
        })

    index_data = generate_index(index_entries, len(url_to_local), error_summaries if error_summaries else None)
    write_index(index_data)
    print(f"  Index written to: {INDEX_FILE}")

    # Summary
    print(f"\n{'=' * 40}")
    print("Scrape complete!")
    print(f"  Total URLs:      {len(urls)}")
    print(f"  Successful:      {progress.successful}")
    print(f"  Failed:          {progress.failed}")
    print(f"  Empty content:   {len(empty_pages)}")
    print(f"  Images found:    {total_images}")
    print(f"  Images saved:    {len(url_to_local)}")
    print(f"  Index entries:   {len(index_entries)}")

    # Error breakdown by category
    if errors:
        error_categories_count: dict[str, int] = {}
        for url, error_message, retry_count in errors:
            error_type = categorize_error(error_message)
            error_categories_count[error_type] = error_categories_count.get(error_type, 0) + 1

        print(f"\n  Error breakdown:")
        for error_type, count in sorted(error_categories_count.items()):
            print(f"    {error_type}: {count}")

    # Error summary
    if errors:
        print(f"\n{'=' * 40}")
        print("Failed URLs:")

        # Group errors by error category
        error_categories: dict[str, list[tuple[str, str, int]]] = {}
        for url, error_message, retry_count in errors:
            error_type = categorize_error(error_message)
            if error_type not in error_categories:
                error_categories[error_type] = []
            error_categories[error_type].append((url, error_message, retry_count))

        for error_type, error_list in error_categories.items():
            print(f"\n  {error_type.upper()} ({len(error_list)} URLs):")
            for url, error_message, retry_count in error_list[:5]:
                retry_info = f" (after {retry_count} retries)" if retry_count > 0 else ""
                print(f"    - {url}{retry_info}")
                print(f"      {error_message}")
            if len(error_list) > 5:
                print(f"    ... and {len(error_list) - 5} more")

    # Empty content warning
    if empty_pages:
        print(f"\n{'=' * 40}")
        print(f"Pages with empty/minimal content ({len(empty_pages)}):")
        for url in empty_pages[:10]:
            print(f"  - {url}")
        if len(empty_pages) > 10:
            print(f"  ... and {len(empty_pages) - 10} more")

    if not errors and not empty_pages:
        print("\n  All pages scraped successfully with content!")


if __name__ == "__main__":
    asyncio.run(main())
