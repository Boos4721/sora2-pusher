# Sora2-Pusher

🤖 AI 视频生成与社交媒体自动化发布助手。基于 [OpenClaw](https://github.com/openclaw/openclaw) 架构，集成 OpenAI Sora 2 与 字节跳动 Seedance 2.0 视频生成能力。

## ✨ 特性

- **双引擎驱动**：
  - **OpenAI Sora 2**：主打“物理模拟”，适合高真实感、长时长的电影级大片。
  - **ByteDance Seedance 2.0**：主打“原生音画同步”，适合高频卡点、精准口型的短视频创作。
- **全自动流水线**：从文本 Prompt 到视频生成，再到抖音自动发布。
- **自动去水印**：默认配置去水印参数，确保视频素材纯净。
- **Browser-in-the-Loop**：利用 OpenClaw 浏览器助手，安全复用抖音登录状态。

## 📦 安装

1. 确保已安装并配置好 [OpenClaw](https://docs.openclaw.ai)。
2. 将本项目克隆到 OpenClaw 的技能目录：
   ```bash
   git clone git@github.com:Boos4721/sora2-pusher.git ~/.openclaw/skills/sora-pusher
   ```
3. 配置凭据：
   - **Sora 2 (Atlas网关)**：配置 `SEEDANCE_API_KEY`。
   - **Seedance 2.0 (火山引擎)**：配置 `VOLC_API_KEY` 与 `VOLC_MODEL_ENDPOINT`。

## 🚀 使用方法

在对话框中直接下达指令：
- "帮我用 **Sora 2** 生成一段[描述]的视频并发布到抖音"
- "用 **火山引擎** 生成视频，带上精准口型，完成后发抖音"

## 📁 目录结构

- `SKILL.md`: 技能核心定义。
- `scripts/volc_gen.py`: 火山引擎 Seedance 2.0 专用生成脚本。
- `scripts/video_gen.py`: Atlas Cloud 通用网关（默认指向 Sora 2）。
- `references/douyin_publish.md`: 抖音自动化发布指南。

## 🤝 鸣谢

- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)
