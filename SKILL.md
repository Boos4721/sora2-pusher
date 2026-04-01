---
name: douyin
description: |
  抖音全能 Skill：搜索、下载、发布、互动、热榜、直播、数据看板、即梦 AIGC 生成、提示词优化、历史记录管理。
  API Client 负责搜索/下载/采集（即时），Playwright 负责发布/登录/数据分析（按需浏览器），
  dreamina CLI 负责即梦文生图/文生视频/图生视频等 AIGC 功能，
  本地存储支持 SQLite/JSON 双后端，提示词优化配合 OpenClaw LLM 使用。
metadata:
  trigger: 抖音相关操作（搜索、下载、发布、热榜、直播、数据、评论）、即梦 AIGC 生成（文生图、文生视频、图生视频）、提示词优化、历史记录查看
---

# 抖音统一 Skill

## 概述

本 Skill 整合三大引擎：
- **API Client**（httpx 逆向 API）：搜索、下载、评论、热榜、直播、用户 — 即时响应
- **Playwright**（浏览器自动化）：发布、登录、数据看板、通知 — 按需启动
- **dreamina CLI**（即梦官方 AIGC）：文生图、文生视频、图生视频 — 自动安装
- **本地存储**（SQLite/JSON）：历史记录、提示词保存 — 数据持久化

## 目录结构

```
douyin/
├── SKILL.md
├── src/dy_cli/
│   ├── main.py
│   ├── engines/
│   │   ├── api_client.py
│   │   └── playwright_client.py
│   ├── commands/
│   │   ├── search.py, download.py, publish.py
│   │   ├── trending.py, live.py, analytics.py
│   │   ├── auth.py, profile.py, interact.py
│   │   ├── dreamina.py, prompt.py, history.py
│   │   └── config_cmd.py, account.py, init.py
│   └── utils/
│       ├── config.py, output.py, signature.py
│       ├── storage.py, export.py, index_cache.py
├── docs/
│   ├── dreamina.md
│   ├── openclaw-integration.md
│   └── cli-guide.md
└── .openclaw/skills/dreamina/
    └── SKILL.md
```

## 完整命令列表

### 工具选择指南

| 操作 | 用哪个 | 命令 |
|------|--------|------|
| 搜索视频 | API | `dy search "关键词"` |
| 无水印下载 | API | `dy download URL` |
| 热榜 | API | `dy trending` |
| 视频详情 | API | `dy detail AWEME_ID` |
| 评论列表 | API | `dy comments AWEME_ID` |
| 用户资料 | API | `dy profile SEC_USER_ID` |
| 直播信息 | API | `dy live info ROOM_ID` |
| 直播录制 | API + ffmpeg | `dy live record ROOM_ID` |
| **发布视频/图文** | Playwright | `dy publish -t 标题 -c 描述 -v 视频` |
| **即梦文生图** | dreamina CLI | `dy dreamina text2image -p "提示词"` |
| **即梦文生视频** | dreamina CLI | `dy dreamina text2video -p "提示词"` |
| **即梦图生视频** | dreamina CLI | `dy dreamina image2video -i img.jpg` |
| **提示词优化** | OpenClaw LLM | `dy prompt optimize "提示词"` |
| **历史记录** | 本地存储 | `dy history search` / `dy history gen` |
| **扫码登录** | Playwright | `dy login` |
| **数据看板** | Playwright | `dy analytics` |
| **通知消息** | Playwright | `dy notifications` |

---

## Part 1: API 工具（搜索/下载/采集）

### 搜索

```bash
dy search "AI创业"
dy search "咖啡" --sort 最多点赞 --time 一天内
dy search "科技" --type video --count 50 --json-output
```

参数:
- `--sort`: 综合 | 最多点赞 | 最新发布
- `--time`: 不限 | 一天内 | 一周内 | 半年内
- `--type`: general | video | user

### 下载

```bash
dy download https://v.douyin.com/xxxxx/
dy download 1234567890
dy download URL --music --output-dir ~/Videos
dy download URL --json-output    # 仅输出链接
```

### 热榜

```bash
dy trending
dy trending --count 20
dy trending --watch              # 每 5 分钟刷新
dy trending --json-output
```

### 视频详情

```bash
dy detail AWEME_ID
dy detail AWEME_ID --comments
dy detail AWEME_ID --json-output
```

### 评论

```bash
dy comments AWEME_ID
dy comments AWEME_ID --count 50 --json-output
```

### 用户

```bash
dy profile SEC_USER_ID
dy profile SEC_USER_ID --posts --post-count 30
dy me
```

### 直播

```bash
dy live info ROOM_ID
dy live info ROOM_ID --json-output
dy live record ROOM_ID                   # 需要 ffmpeg
dy live record ROOM_ID --quality HD1
```

---

## Part 2: Playwright 工具（发布/登录/数据）

### 前置条件

```bash
pip install playwright
playwright install chromium
```

### 登录

```bash
dy login                        # 打开浏览器扫码
dy status                       # 检查登录状态
dy logout                       # 退出登录
```

Cookie 存储位置: `~/.dy/cookies/{account}.json`

### 发布

```bash
# 视频
dy publish -t "标题" -c "描述" -v video.mp4
dy publish -t "标题" -c "描述" -v video.mp4 --tags 旅行 --tags 美食

# 图文
dy publish -t "标题" -c "描述" -i img1.jpg -i img2.jpg

# 选项
dy publish ... --visibility 仅自己可见     # 私密
dy publish ... --schedule "2026-03-16T08:00:00+08:00"  # 定时
dy publish ... --thumbnail cover.jpg       # 封面
dy publish ... --headless                  # 无头模式
dy publish ... --dry-run                   # 预览不发布
```

### 数据看板

```bash
dy analytics
dy analytics --csv data.csv
dy analytics --json-output
```

### 通知

```bash
dy notifications
dy notifications --json-output
```

---

## Part 3: 即梦 AIGC 工具（文生图/视频）

### 安装与管理

dreamina CLI 会在首次使用时自动安装（非交互环境），也可以手动安装：

```bash
dy dreamina install                 # 安装/更新 dreamina CLI
dy dreamina login                   # 登录即梦账号
dy dreamina login --headless        # 无头模式（适合 OpenClaw）
dy dreamina logout                  # 退出
dy dreamina relogin                 # 重新登录
dy dreamina credit                  # 查看账户余额
```

### 文生图

```bash
dy dreamina text2image -p "一只可爱的猫咪"
dy dreamina text2image -p "风景" --ratio 16:9
dy dreamina text2image -p "肖像" --resolution 4k --model 5.0
dy dreamina text2image -p "猫咪" --poll 60    # 轮询等待
dy dreamina text2image -p "..." --json-output  # 输出 JSON
dy dreamina text2image -p "..." --no-save      # 不保存历史
```

**支持的比例**: 21:9, 16:9, 3:2, 4:3, 1:1, 3:4, 2:3, 9:16

**支持的模型**: 3.0, 3.1, 4.0, 4.1, 4.5, 4.6, 5.0, lab

### 文生视频

```bash
dy dreamina text2video -p "猫咪在草地上奔跑"
dy dreamina text2video -p "海浪" --duration 10
dy dreamina text2video -p "城市夜景" --model seedance2.0
```

**支持的时长**: 4-15 秒

**支持的模型**: seedance2.0fast (默认), seedance2.0 (高质量)

### 图生视频

```bash
dy dreamina image2video -i photo.jpg -p "镜头缓慢推进"
dy dreamina image2video -i photo.jpg -p "相机移动" --duration 8 --model 3.5pro
```

### 更多生成命令

```bash
dy dreamina multiframe2video --help   # 多帧图生视频
dy dreamina multimodal2video --help    # 多模态生视频
dy dreamina image2image --help         # 图生图
dy dreamina upscale --help              # 图片超分
dy dreamina frames2video --help         # 首尾帧生视频
```

### 任务管理

```bash
dy dreamina tasks                    # 列出所有任务
dy dreamina tasks --gen-status success  # 按状态筛选
dy dreamina query <submit_id>       # 查询特定任务结果
dy dreamina raw -- ...               # 透传任意参数
```

### 自动保存

所有生成任务会自动保存到本地历史记录，可以通过 `dy history gen` 查看。

---

## Part 4: 提示词优化（配合 OpenClaw LLM）

### 优化提示词

```bash
dy prompt optimize "一只猫"                    # 优化提示词
dy prompt optimize "一只猫" --style anime       # 指定风格
dy prompt optimize "一只猫" --language zh       # 中文输出
dy prompt optimize "一只猫" --auto-apply        # 自动应用到 dreamina
dy prompt optimize "一只猫" --json-output       # JSON 输出
```

**设计为在 OpenClaw 中使用**：OpenClaw 会自动用 LLM 优化提示词，添加细节、风格、光照等专业术语。

### 提示词模板

```bash
dy prompt templates                  # 显示提示词模板和风格推荐
```

### 保存和管理提示词

```bash
dy prompt save "my-prompt" "一只可爱的猫咪..."  # 保存提示词
dy prompt save "my-prompt" "..." --category anime  # 指定分类
dy prompt list                              # 列出保存的提示词
dy prompt list --category anime             # 按分类筛选
```

---

## Part 5: 历史记录管理

### 搜索历史

```bash
dy history search                    # 查看搜索历史
dy history search --keyword "AI"     # 按关键词筛选
dy history search --limit 50         # 显示条数
dy history search --json-output      # JSON 输出
dy history search -o results.json    # 导出到 JSON
dy history search -o results.csv     # 导出到 CSV
```

### 生成历史

```bash
dy history gen                       # 查看生成历史
dy history gen --task-type text2image  # 按类型筛选
dy history gen --status success      # 按状态筛选
dy history gen --limit 50            # 显示条数
dy history gen --json-output         # JSON 输出
dy history gen -o results.json       # 导出到 JSON
dy history gen -o results.csv        # 导出到 CSV
```

### 清空历史

```bash
dy history clear --search --yes      # 清空搜索历史
dy history clear --gen --yes         # 清空生成历史
dy history clear --search --gen --yes  # 清空所有历史
```

---

## Part 6: 配置与运维

### 配置文件

`~/.dy/config.json`:

```bash
dy config show
dy config set api.proxy http://127.0.0.1:7897
dy config set api.timeout 60
dy config set playwright.headless true
dy config set default.download_dir ~/Videos
```

### 多账号

```bash
dy account list
dy account add work
dy account default work
dy login --account work
dy search "关键词" --account work
```

### 登录态维护

- Cookie 存储在 `~/.dy/cookies/`
- 过期后需重新 `dy login` 扫码
- 不同账号 Cookie 文件独立
- dreamina 登录状态独立存储

### 本地存储

- SQLite 数据库: `~/.dy/storage/dy_cli.db`
- JSON 文件存储: `~/.dy/storage/`
- 提示词存储: `~/.dy/prompts.json`

### 注意事项

- 抖音签名算法 (a-bogus) 频繁更新，搜索/下载功能可能需要定期适配
- 创作者中心 UI 也会更新，发布功能可能需要调整选择器
- 批量操作建议加 2-5 秒延时，避免触发风控
- 所有命令支持 `--json-output` 输出机器可读格式
- 所有命令支持 `--account` 指定账号
- dreamina CLI 首次使用会自动安装，也可手动运行 `dy dreamina install`
- 即梦功能需要先安装 dreamina CLI: `curl -fsSL https://jimeng.jianying.com/cli | bash`
- 提示词优化功能设计为在 OpenClaw 中使用，配合 LLM 获得最佳效果
- 所有生成任务自动保存到本地历史记录

---

## OpenClaw 工作流示例

### 示例 1: 搜索 → 下载 → 发布

```
用户: "帮我找一些美食视频，下载一个，然后用即梦生成一个类似的视频，最后发布到抖音"

1. dy search "美食" --count 10
2. dy download 1
3. dy prompt optimize "美食制作视频"
4. dy dreamina text2video -p "优化后的提示词"
5. dy publish -t "美食分享" -c "自己做的美食" -v generated_video.mp4
```

### 示例 2: 即梦生成完整流程

```
用户: "帮我生成一个猫咪视频并保存记录"

1. dy dreamina install (如果未安装)
2. dy dreamina login (如果未登录)
3. dy prompt optimize "一只可爱的猫咪在草地上玩耍" --auto-apply
4. dy dreamina text2video -p "优化后的提示词" --duration 8
5. dy history gen (查看生成记录)
```

### 示例 3: 图生视频 + 发布

```
用户: "我有一张照片，帮我做成视频并发布"

1. dy prompt optimize "镜头缓慢推进，风景视频"
2. dy dreamina image2video -i photo.jpg -p "优化后的提示词"
3. dy publish -t "美丽的风景" -c "分享一下" -v generated_video.mp4
```
