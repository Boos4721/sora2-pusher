# Sora2-Pusher

🤖 AI 视频生成与社交媒体自动化发布助手。基于 [OpenClaw](https://github.com/openclaw/openclaw) 架构，深度集成 OpenAI Sora 2、火山引擎 Seedance 2.0 以及 **即梦AI 视频生成 3.0**。

## ✨ 特性

- **多引擎驱动**：
  - **即梦AI 3.0**：基于火山引擎，支持多镜头叙事，精准遵循指令。提供 **3.0 Pro** (支持图生/文生)、**3.0 1080P** 及 **3.0 720P** 多种模型版本供灵活选用。
  - **火山引擎 Seedance 2.0 (豆包)**：主打“原生音画同步”，适合高频卡点、精准口型的短视频创作。
  - **OpenAI Sora 2**：主打“物理模拟”，适合高真实感、长时长的电影级大片。
- **多模态适配与通讯软件无缝衔接**：完美支持在飞书、Telegram 等聊天软件中直接发送图片触发“图生视频”流程，Agent 会自动提取附件。
- **全自动流水线**：从文本 Prompt 或首帧图片输入，到视频生成下载，再到抖音创作者中心自动发布闭环。
- **智能意图与上下文记忆**：支持用自然语言任意指定生成模型，系统将自动从对话历史中提取 API 凭证，告别繁琐的重复配置。
- **Browser-in-the-Loop**：利用 [PinchTab](https://github.com/pinchtab/pinchtab) 浏览器引擎，安全复用抖音登录状态，执行稳定的全自动发版。

## 📦 安装

1. 确保已安装并配置好 [OpenClaw](https://docs.openclaw.ai)。
2. 将本项目克隆到 OpenClaw 的技能目录：
   ```bash
   git clone git@github.com:Boos4721/sora2-pusher.git ~/.openclaw/skills/sora-pusher
   ```
3. 依赖安装 (自动安装脚本依赖与 PinchTab):
   ```bash
   pip install requests volcengine --break-system-packages
   curl -fsSL https://pinchtab.com/install.sh | bash
   ```
   *(注：在 OpenClaw 中安装此 Skill 时，此步骤将会自动执行)*
4. 配置凭据 (以下信息可直接配置为环境变量，或在对话中直接发给 Agent)：
   - **即梦AI**：需提供火山引擎 `VOLC_ACCESSKEY` (AK) 和 `VOLC_SECRETKEY` (SK)。
   - **Seedance 2.0 (豆包)**：需提供火山引擎 `VOLC_API_KEY` (Bearer Token) 与 `VOLC_MODEL_ENDPOINT` (推理终端 ID)。
   - **Sora 2 (Atlas网关)**：配置 `ATLAS_API_KEY`。

## 🚀 使用方法

在对话框中直接下达自然语言指令，Agent 会自动调度最合适的生成脚本：

- "帮我用 **即梦** 生成一段赛博朋克风格的视频并发布到抖音，标题是：AI 浪潮"
- "用这张图片作为首帧，通过 **即梦3.0 Pro** 生成一段无人机视角的飞行视频：[图片链接]"
- "用 **豆包 Seedance** 生成视频，不要水印，完成后发抖音"
- "帮我用 **Sora 2** 生成一段[描述]的视频"

> 💡 **提示**: 如果之前在对话中发过相关的 Key，直接下达任务指令即可，Agent 会自动寻回之前的 Key 并完成鉴权。

## 📁 目录结构

- `SKILL.md`: 技能核心定义，指导 Agent 的行为逻辑和调用规则。
- `scripts/jimeng_gen.py`: 即梦AI 生成脚本（支持 Pro / 720P / 1080P，AK/SK 鉴权）。
- `scripts/volc_gen.py`: 火山引擎 Seedance 2.0 生成脚本（Bearer Token 鉴权）。
- `scripts/video_gen.py`: Atlas Cloud 通用网关（默认指向 Sora 2）。
- `references/douyin_publish.md`: 基于 PinchTab 的抖音自动化发布指南。

## 🤝 鸣谢

- 流程参考 [social-push](https://github.com/jihe520/social-push)
- 理念参考 [page-agent](https://github.com/alibaba/page-agent)