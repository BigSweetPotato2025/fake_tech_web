# WORKLOG — 2026-10-12 工作状态

## 一、今日完成的事（已提交并推送）

### 1. 架构变更：主从模式 → 每站独立更新（commit `06e02c2`）
- 背景：主从模式（子站从主站 HTTP 拉缓存）不可靠（子站 2.5 个月没更新成功过），且主站换域名要改所有子站配置
- 新架构：**每台站点独立持有 GitHub Token，直连 GitHub API 抓取并构建**，站点之间互不依赖
- 已删除：`fetch/remote.py`、`build.py` 的 remote 分支、`_export_cache()`（不再产出 `dist/cache/`）、config 的 `remote_url`/`cache_token`、README/DESIGN 子站章节、生产 Caddy 的 `/cache/*` X-Cache-Token 403 鉴权块（已 reload）、旧 `dist/cache/` 目录
- API 配额无压力：单站一次完整构建 ≈ 49 次 search + 200 次 core 调用，远低于 5000/h 限额

### 2. 修复的 bug（commit `5eef9d1`）
- **`--skip-fetch` 空页 bug**：跳过抓取时不重建 `all_repos`，projects/详情页渲染全空（疑似子站数据"没更新过"的根因之一）。已提取 `_build_all_repos()` 供两个分支共用
- **CSS 丢失无兜底**：`output.css` 是 tailwind 生成物（不在 git，只有 `input.css` 被追踪），丢失后原代码只报警告。现在构建自动检测缺失并用本地 `node_modules/.bin/tailwindcss` 编译
- **构建入口**：`python3 builder/build.py` 加了 sys.path 引导，无需 `PYTHONPATH` 直接可跑

### 3. 验证结果
- 全量构建：4398 个仓库，约 8 分钟
- 线上 `https://www.howellcome.com/` 返回 200，数据为当日
- 提交链：`d81df2c → 06e02c2 → 5eef9d1`（已推送至 GitHub）
- 注：期间 `assets/css/output.css` 在 16:52-16:53 之间（git rebase 窗口）莫名消失，本机无 crontab 嫌疑，未解之谜；已用自动编译兜底

## 二、服务器盘点（10 台）

| 服务器 | 部署情况 | 说明 |
|--------|---------|------|
| **www**（本机 107.172.234.175） | ✅ 主站 `/var/www/fake_tech` | **今日已改造完成**，Caddy 生产配置 `/etc/caddy/frontend.Caddyfile` |
| **devops** | ✅ 子站 `/var/www/html` | `mode: remote`，**还没迁移**；secret.yaml 空（**缺 token**）；git 在 a1f68a6 |
| **redis06** | ✅ 子站 `/var/www/html` | `mode: remote`，**还没迁移**；secret.yaml 有 token；git 在 9a11945；cron 命令没激活 venv（裸 `python`） |
| **hk** | ✅ 子站 `/usr/local/naive/html` | `mode: remote`，**还没迁移**；naive 代理服务 80/443；secret.yaml 空（**缺 token**）；git 曾在 d81df2c（该提交已进远端 master） |
| filecdn02 / mirror / redis01 / redis02 / redis04 / redis05 | ❌ 未部署 | 干净，不用管 |

- 三台子站最后成功构建都停在 **2026-07-22 ~ 07-25**（约 2.5 个月未更新）
- 子站 cron 服务在跑但构建任务从未留下日志（US/Eastern 时区的 8:30 = 北京 20:30）
- **SSH**：9 台 VPS 都是 **端口 65522**，root 登录；用户提供的私钥存在 `/tmp/opencode/id_vps`（**临时目录，重启会丢，续工时需重新找用户要**）
- 本机的 `~/.ssh/id_ed25519_fake_tech` 对那 9 台无效

## 三、待办（回头继续）

1. **新域名**：用户说稍后告知。届时：改 `config/config.yaml` 的 `site.url` → 重建 → 更新 Caddy/证书 → 推送
2. **三台子站迁移**（devops / redis06 / hk）：
   - 每台：`git pull`（拉 06e02c2+）→ `config.yaml` 删 `remote_url`/`cache_token`（`mode: github` 已是默认）→ `secret.yaml` 填该站自己的 GitHub token → 修正 cron 命令（redis06 要 `source venv/bin/activate` + 时区注意）→ 手动跑一次 `python3 builder/build.py` 验证
   - **devops 和 hk 缺 token，需用户先提供**
   - 注意：仓库里 remote 模式已删除，子站 `git pull` 后不改配置就无法构建，迁移有紧迫性
3. 可选：三台子站的 cron 时间统一（现在是 US/Eastern 时区的 8:30）

## 四、关键文件速查

```
builder/build.py        # 构建入口（fetch → render → CSS 编译/拷贝），已加 sys.path 引导
fetch/github.py         # GitHub API 抓取（唯一 fetcher）
config/config.yaml      # 公开配置（site.url 等）
config/secret.yaml      # token（git 忽略）
/etc/caddy/frontend.Caddyfile  # 生产 Caddy（已无 cache 鉴权块）
```
