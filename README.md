# Developer Atlas

面向开发者的开源项目导航网站 — 发现优质开源项目。

## 网络资源规则

由于网站面向中国大陆用户，**禁止**在页面中引用以下外部资源：
- Google Fonts（`fonts.googleapis.com`、`fonts.gstatic.com`）
- Google APIs（`*.googleapis.com`）
- 其他在中国大陆无法访问的 CDN 或服务

字体必须使用系统默认字体，不得依赖外部字体服务。

## Architecture

### 构建流程（每站独立更新）

每台站点独立持有 GitHub Token，直连 GitHub API 抓取数据并构建，站点之间互不依赖。

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
  Renderer  (render/*.py) → Static HTML (dist/)
    |
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

# 3. Configure secrets (required!)
cp config/secret.yaml.example config/secret.yaml
# Edit config/secret.yaml: add your GitHub token

# 4. Configure site (optional)
# Edit config/config.yaml: update site name, URL, topics, etc.

# 5. Build the site
python builder/build.py

# 6. (Optional) Watch TailwindCSS during development
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

项目使用**双配置文件**：

| 文件 | 内容 | 是否提交到仓库 |
|------|------|:---:|
| `config/config.yaml` | 公开配置（站点信息、topics 等） | ✅ |
| `config/secret.yaml` | 敏感配置（GitHub token） | ❌ |

`load_config` 会自动合并两个文件，`secret.yaml` 的值会覆盖 `config.yaml`。

**首次部署**：
```bash
cp config/secret.yaml.example config/secret.yaml
# 编辑 secret.yaml，填入 GitHub token
```

**config.yaml 示例**：
```yaml
site:
  name: "Developer Atlas"
  description: "面向开发者的开源项目导航网站"
  url: "https://your-domain.com"

github:
  # token 放在 config/secret.yaml 中，不要写在这里
  per_page: 100
  request_delay: 1.0

cache:
  expire_days: 1
```

**secret.yaml 示例**：
```yaml
github:
  token: "ghp_YourTokenHere"
```

## Deployment

### VPS 部署（推荐）

在 VPS 上克隆仓库，本地构建，用 Caddy/Nginx 直接服务 `dist/`：

```bash
# 1. 克隆仓库
git clone <repo-url> /opt/fake_tech_web
cd /opt/fake_tech_web

# 2. 安装依赖
pip install -r requirements.txt
npm install

# 3. 配置密钥
cp config/secret.yaml.example config/secret.yaml
# 编辑 secret.yaml，填入 GitHub token

# 4. 构建
python builder/build.py

# 5. 配置 Caddy/Nginx 指向 dist/ 目录
# 见下方 Caddy 配置示例

# 6. 设置定时更新（可选）
# crontab -e
# 0 6 * * * cd /opt/fake_tech_web && python builder/build.py >> /var/log/build.log 2>&1
```

### Caddy 配置

```caddy
your-domain.com {
    root * /opt/fake_tech_web/dist
    file_server
    encode gzip
}
```

### rsync 远程部署

从本地构建后推送到远程服务器：

```bash
# 编辑 config.yaml 中的 deploy 部分
# deploy:
#   remote_host: "user@host"
#   remote_path: "/var/www/site"

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
