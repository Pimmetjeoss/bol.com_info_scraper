# Bol.com Partner Platform Help Scraper

Een async Python scraper die help-artikelen van het Bol.com Partner Platform extraheert naar gestructureerde markdown bestanden met lokaal opgeslagen afbeeldingen.

## Features

- **JavaScript Rendering**: Gebruikt Playwright browser automation om JavaScript-rendered content te extracten
- **Rate Limiting**: Gecontroleerde concurrency met retry logic om 429 (Too Many Requests) errors te voorkomen
- **Markdown Output**: Converteert HTML naar schone markdown met YAML frontmatter
- **Image Downloading**: Slaat afbeeldingen lokaal op en werkt markdown referenties bij
- **URL Hierarchy**: Behoudt de URL-structuur in de folder hierarchy
- **Progress Tracking**: Real-time voortgangsindicatie tijdens het scrapen
- **Error Handling**: Graceful degradation met gedetailleerde error logging

## Vereisten

- Python 3.11+
- Playwright browsers (automatisch geïnstalleerd)

## Installatie

1. Clone de repository:
```bash
git clone https://github.com/Pimmetjeoss/bol.com_info_scraper.git
cd bol.com_info_scraper
```

2. Installeer dependencies:
```bash
pip install -r requirements.txt
```

3. Installeer Playwright browsers:
```bash
playwright install
```

## Gebruik

1. Voeg URLs toe aan `links.md` (één URL per regel):
```
https://partnerplatform.bol.com/nl/hulp-nodig/...
https://partnerplatform.bol.com/nl/hulp-nodig/...
```

2. Run de scraper:
```bash
python scraper.py
```

3. Output wordt gegenereerd in de `output/` directory:
```
output/
├── hulp-nodig/
│   ├── aanbod/
│   │   └── artikel-naam.md
│   └── ...
├── images/
│   └── image-hash.jpg
└── index.json
```

## Configuratie

De scraper kan worden geconfigureerd door constanten in `scraper.py` aan te passen:

- `MAX_CONCURRENT`: Maximum aantal gelijktijdige browser contexts (default: 1)
- `PAGE_TIMEOUT`: Page load timeout in seconden (default: 30)
- `RETRY_COUNT`: Maximum aantal retries voor 429 errors (default: 3)
- `RETRY_DELAYS`: Exponential backoff delays in seconden (default: [10, 20, 40])

## Output Formaat

### Markdown Bestanden

Elke gescrapede pagina wordt opgeslagen als markdown met YAML frontmatter:

```markdown
---
title: "Artikel Titel"
url: "https://partnerplatform.bol.com/nl/hulp-nodig/..."
scraped_at: "2025-12-24T10:30:00Z"
---

# Artikel Titel

Artikel content in markdown formaat...

![Afbeelding](../images/hash.jpg)
```

### Index Bestand

`index.json` bevat metadata van alle gescrapede pagina's:

```json
[
  {
    "title": "Artikel Titel",
    "url": "https://...",
    "local_path": "output/hulp-nodig/artikel.md",
    "scraped_at": "2025-12-24T10:30:00Z"
  }
]
```

## Technische Details

### Rate Limiting
- Ultra-conservative approach: 1 concurrent request
- Retry logic met exponential backoff bij 429 errors
- Configurable delays: 10s, 20s, 40s

### Browser Automation
- Playwright async API voor JavaScript rendering
- Wacht tot page content volledig geladen is
- Headless browser mode voor efficientie
- Timeout protection tegen hangende pages

### Content Extractie
- BeautifulSoup voor HTML parsing
- Markdownify voor HTML naar Markdown conversie
- Local image downloading met hash-based naming
- Automatic path rewriting in markdown

## Error Handling

De scraper logt verschillende error types:
- **429 Too Many Requests**: Retry met backoff
- **Timeout**: Pagina niet geladen binnen timeout periode
- **Network errors**: Connectie problemen
- **Parsing errors**: Invalide HTML of content

Alle errors worden gelogd met URL en error details. De scraper gaat door met andere URLs na een error.

## Project Structuur

```
├── scraper.py           # Main scraper script
├── links.md             # Input: URLs om te scrapen
├── requirements.txt     # Python dependencies
├── output/              # Output directory (auto-generated)
│   ├── images/          # Downloaded images
│   └── index.json       # Index van alle pages
└── specs/               # Feature specificaties
    ├── 001-bol-help-scraper/
    └── 002-js-scraper-ratelimit/
```

## Development

### Testing
```bash
cd src
pytest
```

### Code Quality
```bash
ruff check .
```

## Licentie

Dit project is bedoeld voor persoonlijk gebruik en onderzoeksdoeleinden.

## Changelog

### Version 2.0 (2025-12-24)
- Toegevoegd: Playwright browser automation voor JavaScript-rendered content
- Toegevoegd: Rate limiting met retry logic
- Verbeterd: Error handling en graceful degradation
- Verbeterd: Progress tracking

### Version 1.0
- Initiële release met basis scraping functionaliteit
