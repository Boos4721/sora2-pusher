# 抖音视频发布流程 (PinchTab 驱动版)

基于强大的浏览器控制工具 [PinchTab](https://github.com/pinchtab/pinchtab) 实现抖音自动化发布。通过 PinchTab 的持久化配置与 HTTP API/CLI，可以更稳定地执行发布流程。

## 🚀 环境准备

1. **安装 PinchTab**:
   ```bash
   curl -fsSL https://pinchtab.com/install.sh | bash
   # 或者 macOS 下使用 brew
   brew install pinchtab/tap/pinchtab
   ```
2. **启动 PinchTab 后台服务**:
   ```bash
   pinchtab daemon install
   pinchtab daemon
   ```

## 🎥 自动化发布步骤

我们可以直接通过 PinchTab CLI 驱动浏览器：

### 1. 打开创作者中心与自动登录
```bash
pinchtab nav "https://creator.douyin.com/creator-micro/content/upload"
```
- **二维码回传扫码**：如果尚未登录，页面会出现登录二维码。Agent 此时应截取当前页面或特定二维码元素的图片，并将其返回给用户（如通过飞书/TG 等渠道）。
- 用户在手机端扫码授权后，页面会自动跳转，后续 PinchTab 会通过 Profile 持久化登录状态，不再需要重复扫码。

### 2. 交互与元素分析
获取页面中所有可交互元素的 ref (如 e1, e2, e3)：
```bash
pinchtab snap -i
```

### 3. 上传视频文件
在分析出的 DOM 中找到 `<input type="file">` 的对应 ref (假设为 e5)：
```bash
# 由于浏览器安全限制，通常使用 fill 或专用上传动作填入绝对路径
pinchtab fill e5 "/Users/xxx/sora2-pusher/output.mp4"
```

### 4. 填写标题及参数
假设标题输入框的 ref 为 e8：
```bash
pinchtab fill e8 "这是用AI生成的视频！ #AI生成 #震撼"
```

### 5. 点击发布
确认视频上传进度达 100% 后，找到“发布”按钮的 ref (假设为 e12) 并点击：
```bash
pinchtab click e12
```

## 🤖 与 Agent 结合的技巧

在使用大模型 (Agent) 执行此任务时，可以告知 Agent 使用以下逻辑闭环：
1. Agent 调用 `pinchtab nav` 进入上传页。
2. Agent 调用 `pinchtab snap -i` 获取页面控件字典。
3. Agent 根据视觉或文本语义分析出 **上传输入框**、**标题输入框**、**发布按钮** 对应的 ref 编号。
4. Agent 依次调用 `pinchtab fill` 与 `pinchtab click` 完成最终上传。