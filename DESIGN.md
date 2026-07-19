# Potatodev's Developer Atlas — 网站开发需求文档 & 操作手册

> 版本：V2 | 更新日期：2026-07-19

---

## 项目简介

Potatodev's Developer Atlas 是一个面向开发者的**开源项目导航网站**，全英文界面。

整个网站采用**静态网站生成**模式，最终输出纯静态文件（HTML + CSS + JavaScript + JSON），部署后无需数据库、无需 PHP、无需 Node Server、无需 Python Web Server，由 **Caddy / Nginx** 直接托管。

构建系统每天自动从 GitHub API 抓取数据，生成页面，更新网站内容。

---

## 一、总体目标

构建一个**长期运营、内容丰富、专业、可信、具有真实浏览价值的开发者门户**。

要求：

- 看起来像真正有人维护的网站
- 页面丰富
- 内容每天自动更新
- 不保存源码
- 占用磁盘极小
- 所有页面全部静态生成

---

## 二、技术要求

**禁止：**

- WordPress
- 数据库（MySQL / Postgres）
- Redis
- Elasticsearch
- Vue SSR
- React SSR

**推荐技术栈：**

| 组件 | 选型 |
|------|------|
| 构建语言 | **Python 3.11+** |
| 模板引擎 | **Jinja2** |
| 内容格式 | **Markdown** |
| CSS 框架 | **TailwindCSS v3** |
| 前端交互 | 原生 JavaScript（无框架） |
| 数据源 | **GitHub REST API v3** |
| 托管 | Caddy / Nginx |

**最终输出目录结构（dist/）：**

```
dist/
  index.html
  projects/        # 项目列表 & 详情页
  topics/          # 主题相关页
  languages/       # 语言页
  organizations/   # 组织页
  collections/     # 精选合集
  articles/        # 文章（预留）
  assets/          # CSS + JS
  json/            # 搜索索引等数据
```

---

## 三、整体架构

```
GitHub API
    │
    ▼
  Fetcher (fetch/github.py)
    │
    ▼
  Normalizer (数据标准化)
    │
    ▼
  JSON Cache (cache/json/)
  README Cache (cache/readme/)
    │
    ▼
  Renderer (render/*.py)
    │
    ▼
  Static HTML (dist/)

    │
    ▼
  Deploy (rsync / git push)
    │
    ▼
  Caddy / Nginx
```

**构建流程：**

```
python builder/build.py
  │
  ├── 1. Fetch ─── GitHub API → 归一化 → 缓存 (cache/)
  ├── 2. Render ── Jinja2 模板 → 生成 HTML (dist/)
  ├── 3. SEO ───── sitemap.xml + robots.txt + RSS
  ├── 4. Search ── search.json 搜索索引
  └── 5. Assets ── CSS/JS 复制到 dist/
```

### V2 扩展方向：开源发现引擎

未来可升级为 **Open Source Discovery Engine**，核心模型为：

```
Fetcher（采集）→ Normalizer（标准化）→ Cache（缓存）
    → Index（建立关系）→ Renderer（生成静态页面）
```

一个 GitHub 仓库会自动关联：
- 同一 Topic 的其他项目
- 同一组织维护的项目
- 相同编程语言的项目
- 同类替代项目（如 PhotoPrism ↔ Immich）
- 所属 Awesome List
- 最新 Release

---

## 四、项目目录结构

```
fake_tech_web/                  # 项目根目录
├── builder/                    # 构建系统
│   ├── __init__.py
│   ├── build.py                # 主构建入口（编排 fetch → render → seo）
│   ├── clean.py                # 缓存/输出清理
│   └── deploy.py               # rsync/git 部署工具
│
├── fetch/                      # 数据抓取层
│   ├── __init__.py
│   ├── base.py                 # BaseFetcher 抽象基类（缓存、重试、归一化）
│   └── github.py               # GitHub REST API v3 实现
│
├── render/                     # HTML 渲染模块
│   ├── __init__.py
│   ├── base.py                 # Jinja2 环境、过滤器、工具函数
│   ├── index.py                # 首页渲染
│   ├── projects.py             # 项目列表（分页 + 排序）
│   ├── project_detail.py       # 项目详情（README、关联项目、search.json）
│   ├── topics.py               # 主题列表 & 详情
│   ├── languages.py            # 语言页
│   ├── organizations.py        # 组织页
│   ├── collections.py          # 精选合集
│   ├── articles.py             # 文章（预留占位）
│   ├── statistics.py           # 统计页
│   └── seo.py                  # sitemap.xml / robots.txt / RSS
│
├── templates/                  # Jinja2 HTML 模板
│   ├── base.html               # 基础布局（Dark Mode、SEO meta、响应式）
│   ├── index.html              # 首页（Hero、Trending、Releases、Stats）
│   ├── projects.html           # 项目列表（筛选、排序、分页）
│   ├── project_detail.html     # 项目详情页
│   ├── topics.html             # 主题列表
│   ├── topic_detail.html       # 主题详情
│   ├── languages.html          # 语言列表
│   ├── organizations.html      # 组织列表
│   ├── collections.html        # 合集页
│   ├── articles.html           # 文章（Coming Soon）
│   ├── statistics.html         # 统计页
│   ├── 404.html                # 404 页面
│   └── components/             # 可复用组件
│       ├── header.html         # 导航栏（Dark Mode toggle、移动端菜单）
│       ├── footer.html         # 页脚
│       ├── project_card.html   # 项目卡片
│       ├── pagination.html     # 分页组件
│       ├── stats_card.html     # 统计卡片
│       └── topic_badge.html    # 主题标签
│
├── assets/                     # 静态资源
│   ├── css/
│   │   └── input.css           # TailwindCSS 输入文件
│   └── js/
│       ├── main.js             # Dark Mode、复制代码、移动端菜单
│       └── search.js           # 前端搜索（search.json）
│
├── cache/                      # 数据缓存
│   ├── json/                   # API 响应缓存（JSON）
│   └── readme/                 # README 缓存（Markdown）
│
├── config/                     # 配置文件
│   └── config.yaml             # 主配置（站点、GitHub、缓存、部署）
│
├── scripts/                    # 运维脚本
│   ├── setup.sh                # 环境初始化
│   └── deploy.sh               # 部署脚本
│
├── dist/                       # 构建输出（生成目录）
├── requirements.txt            # Python 依赖
├── package.json                # TailwindCSS 构建配置
├── tailwind.config.js          # TailwindCSS 主题配置
├── .gitignore
├── README.md                   # 快速上手
└── DESIGN.md                   # 本文档（完整设计方案 + 操作手册）
```

---

## 五、数据来源

**第一阶段仅支持 GitHub**，以后预留扩展接口：

| 数据源 | 状态 | 扩展方式 |
|--------|------|----------|
| GitHub | ✅ 已实现 | `fetch/github.py` |
| GitLab | 🔲 预留 | 新增 `fetch/gitlab.py` |
| Codeberg | 🔲 预留 | 新增 `fetch/codeberg.py` |
| Docker Hub | 🔲 预留 | 新增 `fetch/dockerhub.py` |
| PyPI | 🔲 预留 | 新增 `fetch/pypi.py` |
| crates.io | 🔲 预留 | 新增 `fetch/crates.py` |
| npm | 🔲 预留 | 新增 `fetch/npm.py` |
| Homebrew | 🔲 预留 | 新增 `fetch/homebrew.py` |

扩展时只需新增对应的 `fetch/{source}.py` 和 `render/{source}.py`，无需修改其他模块。

---

## 六、抓取内容

对于 GitHub Repository，抓取以下字段：

| 字段 | 说明 | 来源 |
|------|------|------|
| name | 仓库名 | API |
| owner | 所有者登录名 | API |
| full_name | owner/name | API |
| description | 项目描述 | API |
| stars | Star 数 | API |
| forks | Fork 数 | API |
| language | 主语言 | API |
| license | SPDX 许可证 ID | API |
| topics | 主题标签列表 | API |
| homepage | 项目主页 | API |
| created_at | 创建时间 | API |
| updated_at | 更新时间 | API |
| default_branch | 默认分支 | API |
| open_issues | Open Issue 数 | API |
| latest_release | 最新 Release 信息 | API |
| readme | README 内容（Markdown） | API |

**禁止：**
- git clone
- 下载源码
- 下载图片（README 中的图片保留远程链接）

---

## 七、README 策略

- 只保存 Markdown 原文，最大 100KB
- 图片全部保留远程链接，禁止下载
- 缓存 7 天，过后重新抓取
- 渲染时由 Markdown 库转为 HTML

---

## 八、更新策略

| 数据类别 | 更新频率 | 保留期限 |
|----------|----------|----------|
| Trending | 每天 | 180 天 |
| Latest Release | 每天 | 180 天 |
| Recently Updated | 每天 | 180 天 |
| Editor's Pick | 每天 | 180 天 |
| README 缓存 | 7 天刷新 | 180 天 |

---

## 九、页面设计

### 首页

| 版块 | 内容 |
|------|------|
| Hero | 网站标题、描述、搜索框 |
| Statistics | 项目数、主题数、语言数、Star 总数等 |
| Trending Today | 近期热门项目（按 Stars 排序） |
| Latest Releases | 最近版本更新列表 |
| Popular Topics | 热门主题标签网格 |
| Featured Collections | 精选合集展示 |
| Weekly Picks | 编辑精选项目 |
| Latest Projects | 最新收录项目 |

### Projects 页面

- 分页（每页 30 个项目）
- 搜索框（前端实时搜索）
- 语言筛选（下拉菜单）
- 排序：Stars / Forks / Recently Updated / Recently Added

### Project Detail 页面

- 仓库名称、Owner
- Description
- 元数据：Stars、Forks、License、Language、Issues、Updated
- README（Markdown 渲染为 HTML）
- Latest Release 信息
- Related Projects（相同 Topics）
- Topics 标签
- Repository Link（跳转 GitHub）

### Topics 页面

预定义主题列表，每个主题展示项目数量，点击进入主题详情。

目前支持的主题：

| 主题 | 颜色 |
|------|------|
| AI | 紫色 |
| Database | 蓝色 |
| Docker | 天蓝 |
| CLI | 绿色 |
| Security | 红色 |
| Networking | 橙色 |
| Linux | 灰色 |
| Web | 青色 |
| Self-hosted | 青绿 |
| DevOps | 紫色 |
| Editor | 靛蓝 |
| Testing | 黄绿 |
| Media | 粉色 |
| Game | 玫红 |
| Learning | 浅蓝 |

### Languages 页面

列出所有抓取到的编程语言及项目数量，点击跳转到对应语言的筛选结果。

### Organizations 页面

列出所有组织及项目数量，显示组织头像（从 GitHub 获取）。

### Collections 页面

精选合集，每个合集包含一系列相关项目。

目前定义的合集：
- Awesome AI
- Awesome Docker
- Awesome Rust
- Awesome Linux
- Awesome Self-hosted
- Awesome CLI
- Awesome Security
- Awesome Web

### Statistics 页面

自动生成：
- Top Languages（按项目数量排序，带进度条）
- Most Active Organizations
- Fastest Growing Projects
- Newest Projects
- Largest Projects

全部静态生成，无实时图表依赖。

### Articles 页面

预留，显示 "Coming Soon"。

---

## 十、搜索

**不使用后端搜索服务。**

构建时生成 `dist/json/search.json`，包含所有项目的轻量索引。

前端 JavaScript 在浏览器中实时搜索：
- 匹配字段：名称、Owner、描述、Topics
- 不区分大小写
- 按相关性排序（名称匹配 > Owner > 描述 > Topics）
- 结果上限 20 条
- 键盘上下箭头导航 + Enter 选择
- ESC / 点击外部关闭

---

## 十一、缓存策略

```
GitHub API 响应 → cache/json/（JSON 格式）
README 内容    → cache/readme/（Markdown 格式）
```

**判断逻辑：**
- JSON 缓存有效期：1 天（可配置）
- README 缓存有效期：7 天（可配置）
- 未过期直接使用缓存，跳过 API 请求
- 过期重新抓取，更新缓存

---

## 十二、页面风格

**参考设计：**
- GitHub
- Vercel
- Cloudflare Docs
- Tailwind UI

**设计原则：**
- 极简主义
- 大量留白
- 浅色模式为主
- 支持 Dark Mode（class="dark" 切换，localStorage 持久化）
- 完全响应式（Mobile-first）
- 加载速度快

**禁止：**
- 花哨动画
- 轮播图
- 广告
- 弹窗
- 外部跟踪器

**颜色方案：（V2 暖色调柔和版）**

| 令牌 | 浅色模式 | 深色模式 |
|------|----------|----------|
| 背景 | amber-50/30 | gray-950 |
| 文字 | stone-700 | gray-100 |
| 次要文字 | stone-600/80 | gray-400 |
| 导航栏 | stone-800/90 | gray-950/95 |
| 页脚 | stone-800 | gray-950 |
| 强调色（brand） | orange-600 | orange-400 |
| 卡片 | white/60 + stone-200/50 边框 | gray-900/80 |
| 彩色卡片底 | *-50/60（15色轮换） | *-950/30 |
| 统计卡片 | *-50/60（6色） | *-950/30 |
| 边框 | stone-200/50 | gray-800 |
| 交替 Section | amber-50/40 / orange-50/40 / white/40 | gray-950/90 |

---

## 十三、SEO

构建时自动生成：

| 文件 | 路径 | 说明 |
|------|------|------|
| robots.txt | dist/robots.txt | 搜索引擎爬虫规则 |
| sitemap.xml | dist/sitemap.xml | 全站 URL 索引 |
| feed.xml | dist/feed.xml | RSS Feed（最新 50 个项目） |
| OpenGraph | 模板内嵌 | og:title, og:description, og:image |
| Twitter Card | 模板内嵌 | summary_large_image |

---

## 十四、性能要求

| 指标 | 目标 |
|------|------|
| 首页 HTML | < 100KB |
| CSS | < 80KB |
| JS | < 80KB |
| Lighthouse Performance | 95+ |
| Lighthouse SEO | 100 |
| Lighthouse Accessibility | 95+ |

---

## 十五、磁盘控制（长期运行目标）

| 类别 | 目标上限 |
|------|----------|
| HTML | < 300MB |
| JSON | < 300MB |
| README | < 1GB |
| Assets | < 200MB |
| **整个网站** | **< 2GB** |

---

## 十六、安装指南

### 前置要求

- Python 3.11+
- Node.js 18+（仅用于 TailwindCSS 构建）
- pip（Python 包管理器）
- npm（Node 包管理器）
- GitHub Personal Access Token（[创建教程](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)）

### 安装步骤

```bash
# 1. 进入项目目录
cd /path/to/fake_tech_web

# 2. 创建 Python 虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 安装 TailwindCSS
npm install
```

或一键运行：

```bash
bash scripts/setup.sh
```

---

## 十七、配置指南

编辑 `config/config.yaml`：

```yaml
site:
  name: "Potatodev's Developer Atlas"      # 网站名称
  description: "Discover the best open source projects."  # 网站描述
  url: "https://your-domain.com"          # 部署后的域名
  language: "en"                          # 语言
  author: "Potatodev"                     # 作者
  copyright: "Potatodev's Developer Atlas" # 版权信息

github:
  token: "YOUR_GITHUB_TOKEN"              # 必填：GitHub API Token
  api_base: "https://api.github.com"      # API 地址（无需修改）
  per_page: 100                           # 每页请求数（最大 100）
  request_delay: 1.0                      # 请求间隔（秒）

cache:
  json_dir: "cache/json"                  # JSON 缓存路径
  readme_dir: "cache/readme"              # README 缓存路径
  expire_days: 1                          # 缓存过期天数

render:
  output_dir: "dist"                      # 输出目录
  max_readme_size: 102400                 # README 最大字节数
  readme_cache_days: 7                    # README 缓存天数

deploy:
  remote_host: "user@your-server.com"     # 部署服务器
  remote_path: "/var/www/developer-atlas" # 部署路径
```

### GitHub Token 获取

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `public_repo` 和 `read:user` 权限
4. 复制 Token 填入 `config.yaml` 的 `github.token` 字段

> 无需付费。免费账号每日有 5000 次 API 请求额度，足够本网站使用。

---

## 十八、构建命令

### 完整构建

```bash
python builder/build.py
```

自动执行：
1. Fetch — 从 GitHub API 抓取数据
2. Cache — 写入缓存
3. Render — 生成所有 HTML 页面
4. Generate sitemap — 生成 sitemap.xml
5. Generate RSS — 生成 RSS feed
6. Generate search.json — 生成搜索索引
7. Copy assets — 复制 CSS/JS 到 dist/
8. Output dist/ — 输出到 dist 目录

### 构建选项

```bash
# 清理缓存和输出后构建
python builder/build.py --clean

# 跳过 API 抓取（使用缓存数据）
python builder/build.py --skip-fetch

# 跳过渲染（只抓取数据）
python builder/build.py --skip-render

# 指定配置文件
python builder/build.py --config /path/to/config.yaml

# 指定输出目录
python builder/build.py --output /path/to/output

# 详细日志
python builder/build.py -v
```

### TailwindCSS 构建

```bash
# 开发模式（监听文件变化自动编译）
npm run watch:css

# 生产构建（压缩）
npm run build:css
```

> 注意：`npm run build:css` 需要先完成 `python builder/build.py` 的渲染步骤，
> 因为它会输出到 `dist/assets/css/output.css`。

---

## 十九、部署指南

### 方式一：Caddy / Nginx 直接托管

构建完成后，`dist/` 目录就是一个完整的静态网站。

**Nginx 配置示例：**

```nginx
server {
    listen 80;
    server_name developer-atlas.example.com;
    root /var/www/developer-atlas;

    # 静态文件直接服务
    location / {
        try_files $uri $uri/ /index.html =404;
    }

    # 压缩
    gzip on;
    gzip_types text/html text/css application/javascript application/json;

    # 缓存
    location /assets/ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Caddy 配置示例：**

```caddyfile
developer-atlas.example.com {
    root * /var/www/developer-atlas
    file_server
    encode gzip

    @static {
        path /assets/*
    }
    header @static Cache-Control "public, immutable"
}
```

### 方式二：rsync 部署

```bash
# 一键构建 + 部署
bash scripts/deploy.sh
```

或手动：

```bash
# 先构建
python builder/build.py

# 再同步
rsync -avz --delete dist/ user@your-server.com:/var/www/developer-atlas
```

### 方式三：Git 部署

```bash
# 将 dist/ 内容同步到另一个 git 仓库
python
>>> from builder.deploy import deploy_git
>>> deploy_git('dist', '/path/to/deploy-repo')
```

---

## 二十、定时更新（Crontab）

每天自动更新网站内容：

```bash
# 每天凌晨 3 点执行
0 3 * * * cd /path/to/fake_tech_web && source venv/bin/activate && python builder/build.py --clean >> /var/log/developer-atlas.log 2>&1
```

配合 rsync 自动部署：

```bash
0 4 * * * cd /path/to/fake_tech_web && source venv/bin/activate && python builder/build.py --clean && rsync -avz --delete dist/ user@server:/var/www/developer-atlas
```

---

## 二十一、模块化扩展

整个项目高度模块化，未来增加新数据源只需：

1. 在 `fetch/` 下新增抓取器（如 `fetch/gitlab.py`），继承 `BaseFetcher`
2. 在 `render/` 下新增渲染器（如 `render/gitlab.py`）
3. 无需修改其他模块

所有页面由统一模板系统 (`templates/`) 生成，保证视觉一致性。

---

## 二十二、数据模型

核心数据统一格式（Python dict，序列化为 JSON）：

```python
{
    "id": int,                    # GitHub Repo ID
    "name": str,                  # 仓库名
    "owner": str,                 # Owner 登录名
    "owner_url": str,             # https://github.com/owner
    "owner_avatar": str,          # 头像 URL
    "full_name": str,             # owner/name
    "description": str,           # 描述
    "url": str,                   # https://github.com/owner/name
    "stars": int,                 # Star 数
    "forks": int,                 # Fork 数
    "language": str,              # 主语言
    "license_name": str | None,   # SPDX 许可证 ID
    "topics": [str],              # 主题标签列表
    "homepage": str | None,       # 项目主页
    "created_at": str,            # ISO 8601
    "updated_at": str,            # ISO 8601
    "default_branch": str,        # 默认分支
    "open_issues": int,           # Open Issue 数
    "latest_release_name": str | None,
    "latest_release_url": str | None,
    "latest_release_tag": str | None,
    "latest_release_published": str | None,
    "readme": str | None,         # Markdown 内容，最大 100KB
}
```

---

## 二十三、多站部署方案（主站 + 子站）

当需要部署多个网站时，无需每个站独立调用 GitHub API。采用 **主站负责抓取，子站复用缓存** 的架构，一个 Token 即可支撑任意数量的站点。

### 架构图

```
                    ┌──────────────────┐
                    │   GitHub API     │
                    │   5,000 req/h    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐      持有 Token
                    │   主站 Master    │      fetch.mode: github
                    │  python build.py │
                    └───┬────────┬─────┘
                        │        │
                        │   ┌────▼────────┐
                        │   │  dist/cache/ │  ← build 时自动导出
                        │   └────┬────────┘
                        │        │
          ┌─────────────┼────────┼──────────────────┐
          │             │        │                   │
          │      HTTPS  │  HTTPS │    HTTPS          │
          ▼             ▼        ▼                   ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐     ┌──────────┐
   │ 子站 1   │  │ 子站 2   │  │ 子站 3   │ ... │ 子站 N   │
   │无 Token  │  │无 Token  │  │无 Token  │     │无 Token  │
   │remote_url│  │remote_url│  │remote_url│     │remote_url│
   └──────────┘  └──────────┘  └──────────┘     └──────────┘
```

### 工作流程

**主站（Master）—— 每台 VPS 只需一台：**
```
crontab 每天 2:00
  → python builder/build.py --clean
    → Step 1: Fetch (GitHub API → cache/)
    → Step 2: Render (cache → dist/)
    → Step 3: Export cache/ → dist/cache/   ← 自动完成
```

**子站（Slave）—— 其余 N 台 VPS：**
```
crontab 每天 2:30（主站完成后）
  → python builder/build.py --skip-fetch
    → Step 1: Fetch (跳过，自动从 master 拉取缓存)
    → Step 2: Render (cache → dist/)
```

### 配置方式

**主站 `config.yaml`：**
```yaml
fetch:
  mode: github                     # 主站模式
  remote_url: ""                   # 不需要
  cache_token: ""                  # 不需要

github:
  token: "ghp_xxxxxxxxxxxx"        # 持有 Token

cache:
  json_dir: "cache/json"
  readme_dir: "cache/readme"
```

**子站 `config.yaml`：**
```yaml
fetch:
  mode: remote                     # 子站模式
  remote_url: "https://master.example.com/cache/"
  cache_token: "your-shared-secret"

github:
  token: ""                        # 不需要 Token

cache:
  json_dir: "cache/json"
  readme_dir: "cache/readme"
```

### 安全加固（Nginx）

子站通过 HTTPS 从主站的 `https://master.example.com/cache/` 拉取缓存文件。
为避免被扫描和盗刷流量，主站 Nginx 做三层防护：

```nginx
# 1. 随机路径前缀（部署时生成一次，写入主站和子站配置）
#    不要用 /cache/，用 /static-cache/aB3xK9mZ/ 这类不可猜路径
location ~ ^/static-cache/[a-zA-Z0-9]+/ {
    alias /var/www/developer-atlas/cache/;

    # 2. 只允许 JSON 和 Markdown 文件
    location ~ \.(json|md)$ {
        # 3. Header 鉴权
        if ($http_x_cache_token != "your-shared-secret") {
            return 403;
        }

        # 4. 速率限制（每 IP 每秒 5 次）
        limit_req zone=cache_dl burst=10 nodelay;

        # 5. gzip 压缩传输
        gzip on;
        gzip_types application/json text/markdown;

        # 6. 禁止目录遍历
        autoindex off;

        # 7. 日志不记录（减少磁盘 IO）
        access_log off;

        add_header Cache-Control "public, max-age=3600";
    }

    # 非 .json .md 一律拒绝
    location ~ . {
        return 403;
    }
}
```

**Caddy 配置：**
```caddyfile
master.example.com {
    root * /var/www/developer-atlas
    file_server
    encode gzip

    @cache {
        path /static-cache/aB3xK9mZ/*.json
        path /static-cache/aB3xK9mZ/*.md
        header X-Cache-Token "your-shared-secret"
    }
    @cache_deny {
        path /static-cache/*
    }
    handle @cache {
        file_server
        rate_limit {
            interval 1s
            burst 10
        }
    }
    handle @cache_deny {
        respond 403
    }
}
```

### 流量评估

| 项目 | 数据量 |
|------|--------|
| 每次 fetch 总缓存量 | ~1.5 MB |
| 10 个子站每天传输 | ~15 MB |
| 每月流量 | ~450 MB |
| 典型 VPS 月配额 | 500 GB - 2 TB |
| 流量占比 | **< 0.1%** |

流量完全可以忽略，三层安全防护下被滥用的风险也很低。

### 一句话总结

> 同一套代码，三个配置字段决定角色（master / slave），一个 Token 养所有站。

---

## 二十四、FAQ（补充）

### Q: 一个 GitHub Token 够多少个子站用？
理论上无限。只有主站消耗 API 额度。子站从主站 HTTP 拉取缓存，不碰 GitHub API。

### Q: 子站需要配置什么？
三个字段：`fetch.mode: remote`，`fetch.remote_url`（主站 cache 地址），`fetch.cache_token`（鉴权密钥）。不需要 GitHub Token。

### Q: 主站挂了怎么办？
子站的 `RemoteFetcher` 会优先读取本地现有缓存。即使主站短暂不可用，子站可以继续使用旧的缓存渲染页面，不影响线上访问。

### Q: 文件暴露在公网会不会被刷流量？
三层防护：不可猜路径 + Header 鉴权 + 速率限制。JSON/MD 文件极小，即使偶尔扫到，每次请求也才几 KB。

### Q: 数据多久更新一次？
主站每天 fetch 一次（建议凌晨低峰期），子站建议错峰 30 分钟后执行，确保主站 cache 已更新完毕。
