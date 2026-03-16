---
name: sora2-pusher
description: >
  AI 视频生成与社交媒体自动化发布技能。支持通过 OpenAI Sora 2、火山引擎 Seedance 2.0 以及即梦AI视频生成3.0 Pro 生成高质量视频，并利用 PinchTab 自动发布到抖音创作者中心。
  使用触发词："用火山引擎生成视频", "用即梦生成视频", "把这段文字生成视频发抖音", "生成视频并发布"。
  支持：(1) 文生视频，(2) 图生视频，(3) 视频自动发布到抖音。
metadata:
  openclaw:
    homepage: https://github.com/Boos4721/sora2-pusher
    init: "pip3 install requests volcengine --break-system-packages && curl -fsSL https://pinchtab.com/install.sh | bash"
---

# Sora Pusher Skill

AI 视频生成与社交媒体自动化发布技能。集成火山引擎 Seedance / 即梦AI 与 PinchTab 浏览器控制引擎。

## 🚀 功能
- **视频生成**：调用 **火山引擎 Ark (Seedance 2.0)** 或 **即梦AI 3.0 Pro** 生成视频（支持文生视频与图生视频）。
- **自动发布**：驱动 `pinchtab` 命令将生成的视频发布到抖音（Douyin）创作者中心。
- **任务流水线**：从生成、状态轮询到文件下载与上传的全流程自动化。

## 📁 目录结构
- `SKILL.md`: 技能核心定义与规范。
- `scripts/`: 核心逻辑脚本。
  - `jimeng_gen.py`: 即梦AI 3.0 Pro 专用生成脚本（使用 Volcengine SDK，AK/SK 鉴权）。
  - `volc_gen.py`: 火山引擎 Ark Seedance 2.0 生成脚本（支持最新版多模态 API，Bearer Token 鉴权）。
  - `video_gen.py`: 基于 Atlas Cloud 的备选生成脚本。
- `references/`: 平台发布流程指南。

## 🛠️ 配置要求
- **火山引擎 Ark (Seedance)**: `VOLC_API_KEY` (API 密钥) 及 `VOLC_MODEL_ENDPOINT` (推理终端 ID)。
- **即梦AI 3.0 Pro**: `VOLC_ACCESSKEY` (AK) 及 `VOLC_SECRETKEY` (SK)。
- 登录状态：建议先执行 `pinchtab nav "https://creator.douyin.com/"` 进行一次手动扫码登录，登录后会持久化保存 profile。

## 📝 核心规则 (Rules)
1. **模型与参数选择**：
   - 用户可用自然语言指定模型（如“用即梦3.0”、“用豆包Seedance”、“用Sora”等）。如果用户没有指定，默认推荐使用“即梦AI 3.0 Pro”。
   - **非常重要**：在执行生成任务前，务必检查对话历史中是否已经提供了对应的 API 凭证。如果对话中已经有 API Key 或 AK/SK，请直接提取并在命令行中传入，**不要**再向用户询问。只有在对话历史和环境变量中都找不到所需凭证时，才向用户索要。
3. **处理用户上传的图片 (多模态适配)**：
   - 核心系统 (如 OpenClaw) 接收飞书、Telegram 等渠道的用户消息时，可能会包含图片附件。
   - **非常重要**：如果用户随消息上传了图片附件，Agent 需要读取该附件的本地路径，并将此路径作为 `--image_path` 传入生成脚本，从而触发图生视频逻辑。
4. **生成流程 - 即梦AI (支持 3.0 Pro / 720P / 1080P)**：
   - **文生视频**：`python3 ~/.openclaw/skills/sora-pusher/scripts/jimeng_gen.py --model [pro|720p|1080p] --ak "[AK]" --sk "[SK]" --prompt "[提示词]"`
   - **图生视频 (仅限 Pro)**：在使用 `--model pro` 时，追加 `--image_url "[图片链接]"` 或是 `--image_path "[附件的本地图片路径]"`。
   - 时长默认为 5 秒，支持 `--duration 10`。
5. **生成流程 - 火山引擎 Seedance**：
   - **文生视频**：`python3 ~/.openclaw/skills/sora-pusher/scripts/volc_gen.py --api_key "[API_KEY]" --prompt "[提示词]" --endpoint "[推理终端ID]"`
   - **图生视频**：追加 `--image_url "[图片链接]"` 或是 `--image_path "[附件的本地图片路径]"`。
6. **发布流程**：生成成功并下载后（脚本输出 `RESULT_PATH:[路径]`），自动调用 `pinchtab` 命令行或 API 闭环执行上传与发布指令 (见 `references/douyin_publish.md`)。
7. **超时与重试**：默认超时 900 秒，自动处理异步状态轮询。

## 📖 使用示例
- "用即梦3.0 Pro生成一段赛博朋克风格的视频并发布到抖音，标题是：AI 浪潮"
- "用这张图片作为首帧，通过即梦生成一段无人机视角的飞行视频：[图片链接]"
- "用火山引擎Seedance生成视频并发抖音：[描述词]"

## 🤝 鸣谢
- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)
