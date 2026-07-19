# Developer Atlas

面向开发者的开源项目导航网站 — 发现优质开源项目。

## Architecture

```
GitHub API
    |
    v
  Fetcher  (fetch/github.py)
    |
    v
 JSON Cache  (cache/json/, cache/readme/)
    |
    v
  Renderer  (render/*.py)
    |
    v
 Static HTML  (dist/)

    v
  Deploy  (Caddy/Nginx)
```

## Directory Structure

```
developer-atlas/
  builder/         # Build system
    build.py       # Main build entry point
    clean.py       # Cache/output cleanup
    deploy.py      # Deployment utilities
  fetch/           # Data fetching layer
    base.py        # Abstract fetcher base class
    github.py      # GitHub REST API implementation
  render/          # HTML rendering modules
    base.py        # Jinja2 environment, filters, utilities
    index.py       # Home page
    projects.py    # Projects list pages
    project_detail.py  # Project detail pages
    topics.py      # Topics pages
    languages.py   # Languages page
    organizations.py  # Organizations page
    collections.py # Collections page
    articles.py    # Articles placeholder
    statistics.py  # Statistics page
    seo.py         # sitemap.xml, robots.txt, RSS feed
  templates/       # Jinja2 HTML templates
    components/    # Reusable template components
  assets/          # Static assets (CSS, JS)
  cache/           # Data cache directory
    json/          # Cached API responses
    readme/        # Cached README files
  dist/            # Build output
  config/          # Configuration files
  scripts/         # Utility scripts
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for TailwindCSS)
- A GitHub personal access token (for API access)

### Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install TailwindCSS
npm install

# 3. Configure
# Edit config/config.yaml: set your GitHub token

# 4. Build the site
python builder/build.py

# 5. (Optional) Watch TailwindCSS during development
npm run watch:css
```

### Build Options

```bash
# Clean build
python builder/build.py --clean

# Use cached data (skip API fetching)
python builder/build.py --skip-fetch

# Skip rendering (fetch only)
python builder/build.py --skip-render

# Verbose logging
python builder/build.py -v
```

## Configuration

Edit `config/config.yaml`:

```yaml
site:
  name: "Developer Atlas"
  description: "面向开发者的开源项目导航网站"
  url: "https://your-domain.com"

github:
  token: "YOUR_GITHUB_TOKEN"  # Required for API access
  per_page: 100
  request_delay: 1.0

cache:
  expire_days: 1  # How often to refresh API data
```

## Deployment

### Caddy/Nginx

The `dist/` directory contains a fully static site. Point your web server to it:

```bash
# Build
python builder/build.py

# Deploy via rsync
python -c "from builder.deploy import deploy_rsync; deploy_rsync('dist', 'user@host', '/var/www/developer-atlas')"
```

Or use the deploy script:

```bash
# Edit deploy: section in config.yaml first
bash scripts/deploy.sh
```

### Performance Budget

| Resource | Target |
|----------|--------|
| Homepage HTML | < 100KB |
| CSS | < 80KB |
| JS | < 80KB |
| Total disk (HTML) | < 300MB |
| Total disk (JSON) | < 300MB |
| Total disk (README) | < 1GB |
| Total disk (Assets) | < 200MB |
| Lighthouse Performance | 95+ |
| Lighthouse SEO | 100 |
| Lighthouse Accessibility | 95+ |

## Technology Stack

- **Python 3.11+** — Build system and rendering
- **Jinja2** — HTML templating
- **TailwindCSS v3** — Utility-first CSS framework
- **GitHub REST API v3** — Data source
- **Caddy/Nginx** — Static hosting

## License

MIT
