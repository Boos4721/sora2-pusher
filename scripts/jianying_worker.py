"""
小云雀/即梦AI (Jianying) 自动化视频生成 v6
引擎: Playwright + Chromium
支持: 文生视频 (T2V) + 参考视频生成 (V2V) + 图生视频 (I2V)
平台: xyq.jianying.com (剪映小云雀) / jimeng.jianying.com (即梦AI)
自动登录: 支持通过 --auto-login 自动扫码登录并保存 cookies
"""
import asyncio
import json
import re
import os
import html
import argparse
import subprocess
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Browser

COOKIES_FILE = 'cookies.json'  # 可通过 --cookies 覆盖
DOWNLOAD_DIR = '.'  # 可通过 --output-dir 覆盖
DEBUG_DIR = None  # 可通过 --debug-dir 覆盖
STORAGE_STATE_FILE = None  # 可通过 --storage-state 覆盖
RUN_HEADED = False
RUN_SLOWMO_MS = 0
RUN_TRACE = False


async def auto_login(platform: str = "xyq", cookies_path: str = "cookies.json", storage_state_path: str = None) -> bool:
    """
    自动登录流程：打开浏览器让用户扫码登录，成功后保存 cookies + storage_state
    """
    config = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["xyq"])
    platform_name = config["name"]
    base_url = config["base_url"]

    print(f"🔐 [{platform_name}] 自动登录模式")
    print(f"   1. 请在打开的浏览器中扫码登录")
    print(f"   2. 登录成功后，cookies 将自动保存到: {cookies_path}")
    if storage_state_path:
        print(f"   3. 同时保存 storage_state（含 localStorage）到: {storage_state_path}")
        print(f"   4. 下次运行优先使用 storage_state")
    else:
        print(f"   3. 下次运行将自动使用保存的 cookies")

    async with async_playwright() as p:
        # 使用有头模式，方便用户扫码
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )

        page = await context.new_page()

        # 导航到登录页面，使用更宽松的超时
        print(f"🌐 打开登录页面: {base_url}")
        try:
            await page.goto(base_url, timeout=60000, wait_until='domcontentloaded')
        except Exception as e:
            print(f"  ⚠️ 页面加载超时，继续尝试: {e}")

        await page.wait_for_timeout(5000)

        # 尝试自动点击登录按钮
        login_button_clicked = False
        try:
            # 尝试多种登录按钮选择器
            login_selectors = [
                '#SiderMenuLogin',
                '#SiderMenuLogin div:has-text("登录")',
                'div#SiderMenuLogin[role="menuitem"]',
                'div.login-button-jDhuVc',
                'button:has-text("登录")',
                'button:has-text("立即登录")',
                'button:has-text("手机登录")',
                'a:has-text("登录")',
                'text=登录',
                'text=立即登录',
            ]
            for selector in login_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        print(f"  ✅ 点击登录按钮: {selector}")
                        login_button_clicked = True
                        break
                except:
                    continue
        except Exception as e:
            print(f"  ℹ️ 自动点击登录按钮: {e}")

        # 如果没有点击登录按钮，刷新页面让用户看到登录界面
        if not login_button_clicked:
            print("  ℹ️ 等待登录界面加载...")
            await page.wait_for_timeout(3000)

        # 等待用户登录
        print("⏳ 等待扫码登录中（请用抖音/剪映App扫码）...")
        login_success = False

        for i in range(18):  # 最多等待 3 分钟
            await page.wait_for_timeout(10000)
            body_text = await page.evaluate("() => document.body ? (document.body.innerText || '') : ''")
            is_logged_in = any(check_word in body_text for check_word in config["login_check"])
            if is_logged_in:
                login_success = True
                print(f"  ✅ 登录成功!")
                break

            if i % 12 == 0:
                print(f"    ⏳ 等待中... ({i*5}s)")

        if not login_success:
            print("  ❌ 登录超时，请重试")
            await browser.close()
            return False

        # 等待页面完全加载
        await page.wait_for_timeout(5000)

        # 导出 cookies
        cookies = await context.cookies()
        with open(cookies_path, 'w') as f:
            json.dump(cookies, f, indent=2)

        print(f"  ✅ cookies 已保存到: {cookies_path}")

        if storage_state_path:
            try:
                await context.storage_state(path=storage_state_path)
                print(f"  ✅ storage_state 已保存到: {storage_state_path}")
            except Exception as e:
                print(f"  ⚠️ storage_state 保存失败: {e}")

        await browser.close()
        return True

# 平台配置
PLATFORM_CONFIG = {
    "xyq": {
        "name": "剪映小云雀",
        "base_url": "https://xyq.jianying.com/home",
        "detail_url_template": "https://xyq.jianying.com/home?tab_name=integrated-agent&thread_id={thread_id}",
        "login_check": ["小云雀助你", "新对话"],
    },
    "jimeng": {
        "name": "即梦AI",
        "base_url": "https://jimeng.jianying.com/ai-tool/generate",
        "detail_url_template": "https://jimeng.jianying.com/ai-tool/home?tab_name=integrated-agent&thread_id={thread_id}",
        "login_check": ["AI", "创作", "新对话"],  # 即梦AI登录后显示的文字需确认
    }
}

def load_and_clean_cookies(cookies_file: str):
    with open(cookies_file, 'r') as f:
        raw = json.load(f)
    # 兼容 Playwright storage_state.json（顶层是 dict，cookies 在 raw["cookies"]）
    if isinstance(raw, dict) and isinstance(raw.get("cookies"), list):
        raw = raw["cookies"]
    cleaned = []
    allowed = ['name', 'value', 'domain', 'path', 'expires', 'httpOnly', 'secure']
    for c in raw:
        clean = {}
        for key in allowed:
            if key == 'expires':
                val = c.get('expirationDate') or c.get('expires')
                if val is not None:
                    clean['expires'] = val
                continue
            if key in c and c[key] is not None:
                clean[key] = c[key]
        cleaned.append(clean)
    return cleaned

DEBUG_SCREENSHOTS = False  # 由 --dry-run 控制

def _now_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

async def screenshot(page, name):
    global DEBUG_DIR
    if not (DEBUG_SCREENSHOTS or DEBUG_DIR):
        return
    out_dir = DEBUG_DIR or DOWNLOAD_DIR
    _ensure_dir(out_dir)
    path = os.path.join(out_dir, f'step_{name}.png')
    await page.screenshot(path=path)
    print(f"  📸 Screenshot: {path}")

async def dump_debug_bundle(page, label: str, extra: dict = None):
    """保存失败现场：截图 + HTML + 元信息（写入 DEBUG_DIR 或 DOWNLOAD_DIR）。"""
    out_dir = DEBUG_DIR or DOWNLOAD_DIR
    _ensure_dir(out_dir)
    ts = _now_run_id()
    safe_label = re.sub(r'[^0-9a-zA-Z._-]+', '_', label)[:60] or "dump"

    png_path = os.path.join(out_dir, f"dump_{ts}_{safe_label}.png")
    html_path = os.path.join(out_dir, f"dump_{ts}_{safe_label}.html")
    meta_path = os.path.join(out_dir, f"dump_{ts}_{safe_label}.json")

    try:
        await page.screenshot(path=png_path, full_page=True)
    except Exception as e:
        print(f"  ⚠️ dump screenshot failed: {e}")

    try:
        html_content = await page.content()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        print(f"  ⚠️ dump html failed: {e}")

    try:
        meta = {
            "label": label,
            "timestamp": ts,
            "url": getattr(page, "url", None),
            "extra": extra or {},
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠️ dump meta failed: {e}")

    print(f"  🧷 Debug bundle: {png_path}")

async def detect_logged_in(page, platform: str, config: dict) -> bool:
    """尽量避免用 page.content() 做登录判断（HTML 里可能常驻“登录”字样）。"""
    try:
        login_cta_visible = await page.evaluate(r'''() => {
            const els = Array.from(document.querySelectorAll('button,a'));
            const re = /(立即登录|扫码登录|登录)/;
            return els.some(el => {
                const t = (el.innerText || '').trim();
                if (!t || !re.test(t)) return false;
                const r = el.getBoundingClientRect();
                if (r.width < 10 || r.height < 10) return false;
                if (r.top < 0 || r.top > 260) return false;
                const s = window.getComputedStyle(el);
                if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity || '1') === 0) return false;
                return true;
            });
        }''')
    except Exception:
        login_cta_visible = False

    if login_cta_visible:
        return False

    # 小云雀补一个更强的正向信号，避免误判
    if platform == "xyq":
        try:
            body_text = await page.evaluate("() => document.body ? (document.body.innerText || '') : ''")
            return any(check_word in body_text for check_word in config.get("login_check", []))
        except Exception:
            return True

    # jimeng 页面文案变化大：只要没有明显登录入口，就先按已登录继续
    return True

async def check_and_resize_video(video_path: str) -> str:
    """检查视频分辨率，必要时缩放并补边到平台要求范围内。"""
    try:
        # 获取分辨率
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", video_path]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"  ⚠️ 无法获取视频分辨率: {stderr.decode()}")
            return video_path
        
        dims = stdout.decode().strip().split('x')
        if len(dims) != 2:
            return video_path
        
        w, h = int(dims[0]), int(dims[1])
        print(f"  📊 原始视频分辨率: {w}x{h}")
        
        # 平台限制: 480p (640x640) - 720p (834x1112)
        # 我们以长边不超过 1112 为准进行等比例缩放
        max_dim = 1112
        min_dim = 480
        
        need_resize = max(w, h) > max_dim or min(w, h) < min_dim

        if need_resize:
            scale_ratio = min(1.0, max_dim / max(w, h)) if max(w, h) > max_dim else 1.0
            scaled_w = max(2, int(round(w * scale_ratio)))
            scaled_h = max(2, int(round(h * scale_ratio)))
            if scaled_w % 2 != 0:
                scaled_w -= 1
            if scaled_h % 2 != 0:
                scaled_h -= 1

            pad_w = max(scaled_w, min_dim)
            pad_h = max(scaled_h, min_dim)
            if pad_w % 2 != 0:
                pad_w += 1
            if pad_h % 2 != 0:
                pad_h += 1

            filter_parts = [f"scale={scaled_w}:{scaled_h}"]
            if pad_w != scaled_w or pad_h != scaled_h:
                pad_x = max((pad_w - scaled_w) // 2, 0)
                pad_y = max((pad_h - scaled_h) // 2, 0)
                filter_parts.append(f"pad={pad_w}:{pad_h}:{pad_x}:{pad_y}:black")

            filter_chain = ",".join(filter_parts)
            print(f"  🔧 视频将处理为 {scaled_w}x{scaled_h}，最终画布 {pad_w}x{pad_h}")

            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"resized_{os.path.basename(video_path)}")
            
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", filter_chain, "-c:v", "libx264", "-crf", "23", "-preset", "fast", output_path]
            print(f"  🎬 执行缩放: {' '.join(ffmpeg_cmd)}")
            
            f_proc = await asyncio.create_subprocess_exec(*ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            await f_proc.communicate()
            
            if f_proc.returncode == 0:
                print(f"  ✅ 缩放完成: {output_path}")
                return output_path
            else:
                print(f"  ❌ 缩放失败，忽略并使用原文件")
                
    except Exception as e:
        print(f"  ⚠️ 预检查发生错误: {str(e)}")
        
    return video_path

async def safe_click(page, locator_or_selector, label, timeout=5000, retries: int = 2):
    """尽量用真实点击，失败则回退到 DOM click；对动态 UI 做简单重试。"""
    last_err = None
    for attempt in range(max(retries, 1)):
        try:
            if isinstance(locator_or_selector, str):
                loc = page.locator(locator_or_selector).first
            else:
                loc = locator_or_selector

            try:
                await loc.scroll_into_view_if_needed(timeout=timeout)
            except Exception:
                pass
            try:
                await loc.wait_for(state="visible", timeout=timeout)
            except Exception:
                pass

            await loc.click(timeout=timeout)
            print(f"  ✅ {label}: clicked")
            return True
        except Exception as e:
            last_err = e
            try:
                await loc.evaluate("el => el.click()")
                print(f"  ✅ {label}: clicked (DOM fallback)")
                return True
            except Exception:
                if attempt < retries - 1:
                    await page.wait_for_timeout(600)
                continue

    print(f"  ❌ {label}: {last_err}")
    return False

async def fill_contenteditable(page, text: str, label: str = "Prompt", timeout: int = 8000) -> bool:
    """用键盘输入填充 contenteditable，尽量触发框架事件（比 innerText 注入更稳）。"""
    loc = page.locator('div[contenteditable="true"]').first
    try:
        await loc.wait_for(state="visible", timeout=timeout)
        await loc.scroll_into_view_if_needed(timeout=timeout)
        await loc.click(timeout=timeout)
    except Exception as e:
        print(f"  ❌ {label}: contenteditable not ready: {e}")
        return False

    # 清空：兼容 macOS / Windows/Linux
    for key in ("Meta+A", "Control+A"):
        try:
            await page.keyboard.press(key)
            break
        except Exception:
            continue
    try:
        await page.keyboard.press("Backspace")
    except Exception:
        pass

    try:
        await page.keyboard.type(text, delay=15 if RUN_SLOWMO_MS else 0)
        print(f"  ✅ {label}: typed ({len(text)} chars)")
        return True
    except Exception as e:
        print(f"  ❌ {label}: type failed: {e}")
        return False

async def open_reference_material_panel(page) -> bool:
    """打开 V2V 的参考素材面板，必须优先走工具栏里的“参考”按钮。"""
    selectors = [
        ('button:has-text("参考")', '参考'),
        ('button:has-text("素材")', '素材'),
        ('button[title="上传参考素材"]', '上传参考素材'),
    ]
    for selector, label in selectors:
        if await safe_click(page, page.locator(selector).first, f'{label}按钮', timeout=8000):
            return True

    fallback = await page.evaluate('''() => {
        const editable = document.querySelector('div[contenteditable="true"]');
        const root = editable ? (editable.closest('form') || editable.parentElement || document.body) : document.body;
        const buttons = Array.from(root.querySelectorAll('button'));
        const candidate = buttons.find(btn => {
            const title = (btn.getAttribute('title') || '').trim();
            const text = (btn.innerText || '').trim();
            return title.includes('上传参考素材') || text === '参考' || text === '素材';
        });
        if (!candidate) return 'NOT_FOUND';
        candidate.click();
        return 'OK_JS';
    }''')
    print(f"  参考素材面板兜底: {fallback}")
    return fallback.startswith('OK')

async def upload_reference_media(page, file_path: str, media_kind: str) -> bool:
    """
    上传参考素材。优先直连 input[type=file]，避免依赖“从本地上传”文案。
    media_kind: 'image' | 'video'
    """
    expect_token = 'video' if media_kind == 'video' else 'image'

    file_inputs = page.locator('input[type="file"]')
    input_count = await file_inputs.count()
    for idx in range(input_count):
        locator = file_inputs.nth(idx)
        try:
            accept = (await locator.get_attribute('accept')) or ''
            is_hidden = await locator.evaluate(
                '''el => {
                    const s = window.getComputedStyle(el);
                    return s.display === 'none' || s.visibility === 'hidden';
                }'''
            )
            if accept and expect_token not in accept.lower():
                continue
            await locator.set_input_files(file_path, timeout=10000)
            print(f"  ✅ 通过 file input 上传成功: index={idx}, accept={accept or '*/*'}, hidden={is_hidden}")
            return True
        except Exception as e:
            print(f"  ⚠️ file input[{idx}] 上传失败: {e}")

    print("  ℹ️ 未找到可直接写入的 file input，回退到 file chooser 流程")
    candidate_texts = ['从本地上传', '本地上传', '上传']
    for text in candidate_texts:
        try:
            async with page.expect_file_chooser(timeout=5000) as fc_info:
                clicked = await safe_click(page, page.locator(f'text={text}').first, f'{text}入口', timeout=3000)
                if not clicked:
                    continue
            chooser = await fc_info.value
            await chooser.set_files(file_path)
            print(f"  ✅ 通过 file chooser 上传成功: {text}")
            return True
        except Exception:
            continue

    return False

async def wait_for_reference_media_ready(page, media_kind: str, timeout_ms: int = 300000) -> bool:
    """等待参考素材缩略图或重传入口出现。"""
    step_ms = 5000
    expect_video = media_kind == 'video'
    loops = max(timeout_ms // step_ms, 1)
    print("  ⏳ 等待上传完成...")
    for wait_i in range(loops):
        await page.wait_for_timeout(step_ms)
        upload_status = await page.evaluate(r'''([expectVideo]) => {
            const text = document.body.innerText || '';
            const isUploading = text.includes('上传中') || text.includes('uploading') || /\b\d{1,3}%\b/.test(text);
            const confirmBtn = Array.from(document.querySelectorAll('button')).find(btn => (btn.innerText || '').trim() === '确认');
            const confirmDisabled = confirmBtn ? (confirmBtn.hasAttribute('disabled') || btnHasSpinner(confirmBtn)) : null;

            const editable = document.querySelector('div[contenteditable="true"]');
            const scope = editable ? (editable.closest('form') || editable.parentElement || document.body) : document.body;
            const hasBackgroundThumb = Array.from(document.body.querySelectorAll('*')).some(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width < 20 || rect.height < 20) return false;
                const style = window.getComputedStyle(el);
                if (!style.backgroundImage || style.backgroundImage === 'none') return false;
                return rect.top > 150 && rect.top < 500 && rect.left > 450 && rect.left < 900;
            });
            const hasVisual = expectVideo
                ? (!!scope.querySelector('video, img[src*="tos"], canvas') || hasBackgroundThumb)
                : (!!scope.querySelector('img, canvas') || hasBackgroundThumb);
            const all = Array.from(document.querySelectorAll('*'));
            const hasLabel = all.some(el => {
                const t = (el.innerText || '').trim();
                if (!t) return false;
                if (expectVideo) return t === '视频1' || t === '重新上传' || t === '替换';
                return t === '图片1' || t === '重新上传' || t === '替换';
            });
            const sendBtn = Array.from(document.querySelectorAll('button')).find(btn => btn.querySelector('svg.lucide-arrow-up'));
            const sendDisabled = sendBtn ? (sendBtn.hasAttribute('disabled') || sendBtn.getAttribute('aria-disabled') === 'true') : null;

            if (hasVisual || hasLabel) return `DONE|sendDisabled=${sendDisabled}|confirmDisabled=${confirmDisabled}`;
            if (isUploading || confirmDisabled) return 'UPLOADING';
            return `WAITING|sendDisabled=${sendDisabled}|confirmDisabled=${confirmDisabled}`;

            function btnHasSpinner(btn) {
                return !!btn.querySelector('svg, [class*="spin"], [class*="loading"], [class*="loader"]');
            }
        }''', [expect_video])

        if upload_status.startswith('DONE'):
            print(f"  ✅ 上传完成! {upload_status} (elapsed: {(wait_i + 1) * step_ms // 1000}s)")
            return True
        if upload_status == 'UPLOADING':
            continue
        if upload_status.startswith('WAITING|sendDisabled=false') and wait_i >= 11:
            print(f"  ⚠️ 上传完成信号不稳定，按可提交状态继续: {upload_status} (elapsed: {(wait_i + 1) * step_ms // 1000}s)")
            return True
        if wait_i > 0 and wait_i % 6 == 0:
            print(f"    ⏳ 等待中... {upload_status} ({(wait_i + 1) * step_ms // 1000}s)")
    return False

async def collect_editor_state(page):
    """收集 dry-run 末态，便于判断表单是否可提交。"""
    return await page.evaluate('''() => {
        const editable = document.querySelector('div[contenteditable="true"]');
        const scope = editable ? (editable.closest('form') || editable.parentElement || document.body) : document.body;
        const sendBtn = Array.from(document.querySelectorAll('button')).find(btn => btn.querySelector('svg.lucide-arrow-up'));
        const promptText = editable ? (editable.innerText || '').trim() : '';
        const hasBackgroundThumb = Array.from(document.body.querySelectorAll('*')).some(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width < 20 || rect.height < 20) return false;
            const style = window.getComputedStyle(el);
            if (!style.backgroundImage || style.backgroundImage === 'none') return false;
            return rect.top > 150 && rect.top < 500 && rect.left > 450 && rect.left < 900;
        });
        return {
            promptLength: promptText.length,
            hasImageThumb: !!scope.querySelector('img'),
            hasVideoThumb: !!scope.querySelector('video'),
            hasCanvasThumb: !!scope.querySelector('canvas'),
            hasBackgroundThumb,
            hasReplaceAction: Array.from(document.querySelectorAll('*')).some(el => {
                const t = (el.innerText || '').trim();
                return t === '重新上传' || t === '替换';
            }),
            sendDisabled: sendBtn ? (sendBtn.hasAttribute('disabled') || sendBtn.getAttribute('aria-disabled') === 'true') : null,
            sendPresent: !!sendBtn,
        };
    }''')

async def run(prompt: str, duration: str = "10s", ratio: str = "横屏", model: str = "Seedance 2.0", dry_run: bool = False, ref_video: str = None, ref_image: str = None, platform: str = "xyq", cookies_file: str = None):
    global DEBUG_SCREENSHOTS
    DEBUG_SCREENSHOTS = dry_run

    # 如果没有指定 cookies 文件，根据平台默认
    if cookies_file is None:
        cookies_file = f"cookies_{platform}.json"

    config = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["xyq"])
    platform_name = config["name"]
    base_url = config["base_url"]
    detail_url_template = config["detail_url_template"]
    ref_video_ready = False
    if ref_image:
        mode_label = "I2V (图生视频)"
    elif ref_video:
        mode_label = "V2V (参考视频)"
    else:
        mode_label = "T2V (文生视频)"
    print(f"🚀 Starting Playwright + Chromium (headless)... [{mode_label}] [{platform_name}]")
    if ref_video and not os.path.exists(ref_video):
        print(f"❌ 参考视频文件不存在: {ref_video}")
        return
    if ref_image and not os.path.exists(ref_image):
        print(f"❌ 参考图片文件不存在: {ref_image}")
        return
    if ref_video:
        size_mb = os.path.getsize(ref_video) / (1024 * 1024)
        print(f"📎 参考视频: {ref_video} ({size_mb:.1f}MB)")
    if ref_image:
        size_kb = os.path.getsize(ref_image) / 1024
        print(f"🖼️ 参考图片: {ref_image} ({size_kb:.0f}KB)")
    if dry_run:
        print("⚠️ DRY-RUN MODE: will fill form but NOT click '开始创作'")

    async with async_playwright() as p:
        run_id = _now_run_id()
        trace_path = None
        trace_started = False
        console_logs = []
        browser = await p.chromium.launch(
            headless=not RUN_HEADED,
            slow_mo=RUN_SLOWMO_MS or 0,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        storage_state_path = STORAGE_STATE_FILE
        use_storage_state = bool(storage_state_path and os.path.exists(storage_state_path))
        if storage_state_path and not use_storage_state:
            print(f"ℹ️ storage_state not found: {storage_state_path} (will use cookies instead)")

        context_kwargs = {"viewport": {'width': 1920, 'height': 1080}}
        if use_storage_state:
            context_kwargs["storage_state"] = storage_state_path
        context = await browser.new_context(**context_kwargs)

        if RUN_TRACE:
            out_dir = DEBUG_DIR or DOWNLOAD_DIR
            _ensure_dir(out_dir)
            trace_path = os.path.join(out_dir, f"trace_{platform}_{run_id}.zip")
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            trace_started = True
            print(f"🧭 Trace enabled: {trace_path}")

        async def finalize():
            out_dir = DEBUG_DIR or DOWNLOAD_DIR
            _ensure_dir(out_dir)

            if console_logs:
                try:
                    log_path = os.path.join(out_dir, f"console_{platform}_{run_id}.log")
                    with open(log_path, "w", encoding="utf-8") as f:
                        for item in console_logs[-2000:]:
                            f.write(f"[{item.get('type')}] {item.get('text')}\n")
                    print(f"  🧾 Console log: {log_path}")
                except Exception as e:
                    print(f"  ⚠️ console log write failed: {e}")

            if trace_started and trace_path:
                try:
                    await context.tracing.stop(path=trace_path)
                    print(f"  🧭 Trace saved: {trace_path}")
                except Exception as e:
                    print(f"  ⚠️ trace stop failed: {e}")

            try:
                await browser.close()
            except Exception:
                pass

        page = await context.new_page()
        page.on("console", lambda msg: console_logs.append({"type": msg.type, "text": msg.text}))

        # === Step 1: 登录态注入（优先 storage_state） ===
        if use_storage_state:
            print(f"🔑 [Step 1] Using storage_state from {storage_state_path}...")
        else:
            print(f"🔑 [Step 1] Injecting cookies from {cookies_file}...")
            cookies = load_and_clean_cookies(cookies_file)
            await context.add_cookies(cookies)
            print(f"  ✅ {len(cookies)} cookies injected")

        # === Step 2: 导航 ===
        print(f"🌐 [Step 2] Navigating to {base_url}...")
        await page.goto(base_url, wait_until='domcontentloaded')
        await page.wait_for_timeout(8000)
        await screenshot(page, '2_loaded')

        # === Step 3: 登录验证 ===
        print("🔍 [Step 3] Checking login status...")
        is_logged_in = await detect_logged_in(page, platform, config)
        if is_logged_in:
            print("  ✅ LOGIN_SUCCESS")
        else:
            print("  ❌ LOGIN_FAILED — 请重新导出 cookies.json 或使用 --auto-login")
            await dump_debug_bundle(page, "login_failed", {"platform": platform, "base_url": base_url})
            await finalize()
            return

        # === Step 3.2: 关闭弹窗 (jimeng 有绑定弹窗) ===
        print("🚪 [Step 3.2] Closing popup dialog...")
        try:
            close_popup = await page.evaluate('''() => {
                // 查找即梦的绑定弹窗 - class 包含 bind-capcut-account
                const modal = document.querySelector('[class*="bind-capcut-account"]');
                if (modal) {
                    // 查找关闭按钮 - class 包含 close-icon-wrapper
                    const closeBtn = modal.querySelector('[class*="close-icon-wrapper"]');
                    if (closeBtn) {
                        closeBtn.click();
                        return 'CLOSED_BIND_MODAL';
                    }
                }
                // 兜底：关闭其他弹窗（优先找 aria-label=close 或 title=close）
                const candidates = Array.from(document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="dialog"]'));
                for (const dlg of candidates) {
                    const closeEl =
                        dlg.querySelector('[aria-label*="关闭"], [aria-label*="close"], [title*="关闭"], [title*="close"], [class*="close"], button:has(svg)') ||
                        dlg.querySelector('svg');
                    if (closeEl) {
                        closeEl.click();
                        return 'CLOSED_OTHER';
                    }
                }
                return 'NO_POPUP';
            }''')
            print(f"  Popup close: {close_popup}")
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  Popup close: {e}")
        await screenshot(page, '3_2_popup_closed')

        # === Step 3.5: 从 "Agent 模式" 下拉选择 "沉浸式短片" ===
        print("🎬 [Step 3.5] Selecting '沉浸式短片' from mode dropdown...")
        # 3.5a: 点击 "Agent 模式" 下拉按钮
        mode_dropdown_opened = await safe_click(
            page, page.locator('text=Agent 模式').first, 'Agent 模式下拉', timeout=8000
        )
        await page.wait_for_timeout(2000)
        await screenshot(page, '3_5a_mode_dropdown')

        if mode_dropdown_opened:
            # 3.5b: 在下拉菜单中选择 "沉浸式短片"
            immersive_clicked = await safe_click(
                page, page.locator('text=沉浸式短片').first, '沉浸式短片', timeout=5000
            )
            if not immersive_clicked:
                print("  ⚠️ Fallback: trying JS click for '沉浸式短片'")
                await page.evaluate('''() => {
                    const items = Array.from(document.querySelectorAll('*'));
                    const el = items.find(e => {
                        const t = (e.innerText || '').trim();
                        return t === '沉浸式短片' && e.offsetHeight < 40 && e.offsetHeight > 10;
                    });
                    if (el) el.click();
                }''')
        else:
            # 可能已经在沉浸式短片模式下
            toolbar_text = await page.evaluate('''() => {
                const el = document.querySelector('div[contenteditable="true"]');
                return el ? 'HAS_INPUT' : 'NO_INPUT';
            }''')
            print(f"  ⚠️ Mode dropdown not found, toolbar status: {toolbar_text}")

        await page.wait_for_timeout(3000)
        await screenshot(page, '3_5b_mode_selected')

        # === Step 3.6: 上传参考图片 (仅 I2V 模式) ===
        if ref_image:
            print(f"🖼️ [Step 3.6] Uploading reference image: {os.path.basename(ref_image)}")

            # 点击输入区域的 "+" 按钮 (工具栏最左边, title="上传参考素材")
            plus_clicked = False
            try:
                # 新 UI: 按钮有 title="上传参考素材"
                plus_locator = page.locator('button[title="上传参考素材"]').first
                box = await plus_locator.bounding_box()
                if not box:
                    # 备用: 通过 SVG class 定位
                    plus_locator = page.locator('button:has(svg.lucide-plus)').first
                await plus_locator.click(timeout=3000)
                plus_clicked = True
                print(f"  + 按钮: OK (Playwright locator)")
            except Exception as e:
                print(f"  + 按钮: locator_fail ({e})")
                
            if not plus_clicked:
                # 最后的 evaluate 兜底方案
                plus_result = await page.evaluate('''() => {
                    const svgs = Array.from(document.querySelectorAll('svg.lucide-plus'));
                    const targetSvg = svgs.find(svg => {
                        const r = svg.getBoundingClientRect();
                        return r.top > 300 && r.top < 600 && r.left > 400 && r.left < 800;
                    });
                    if (targetSvg) {
                        const btn = targetSvg.closest('button') || targetSvg.parentElement;
                        btn.click();
                        return 'OK_EVAL (svg.lucide-plus found)';
                    }
                    return 'NOT_FOUND';
                }''')
                print(f"  + 按钮: eval fallback -> {plus_result}")
                plus_clicked = plus_result.startswith('OK')
            await page.wait_for_timeout(2000)
            await screenshot(page, '3_6_plus_menu')

            if plus_clicked:
                # 点击 "本地上传" 并上传图片
                try:
                    async with page.expect_file_chooser(timeout=10000) as fc_info:
                        upload_clicked = await page.evaluate('''() => {
                            const all = Array.from(document.querySelectorAll('*'));
                            const candidates = all.filter(el => {
                                const text = el.innerText && el.innerText.trim();
                                if (!text) return false;
                                return text === '本地上传' || text === '从本地上传';
                            });
                            candidates.sort((a, b) => {
                                return (a.offsetWidth * a.offsetHeight) - (b.offsetWidth * b.offsetHeight);
                            });
                            if (candidates.length > 0) {
                                const el = candidates[0];
                                el.click();
                                return 'OK: ' + el.tagName;
                            }
                            return 'NOT_FOUND';
                        }''')
                        print(f"  本地上传: {upload_clicked}")
                        if upload_clicked == 'NOT_FOUND':
                            raise Exception("'本地上传' not found in menu")

                    file_chooser = await fc_info.value
                    await file_chooser.set_files(ref_image)
                    print(f"  ✅ 图片已选择: {os.path.basename(ref_image)}")

                    # 等待图片上传完成 (检测缩略图出现)
                    print("  ⏳ 等待图片上传...")
                    for wait_i in range(30):
                        await page.wait_for_timeout(3000)
                        has_image = await page.evaluate('''() => {
                            // 新 UI: 检查 contenteditable 附近是否有 img
                            const editable = document.querySelector('div[contenteditable="true"]');
                            if (editable) {
                                // 向上查找父容器中的 img
                                const parent = editable.closest('div[class]') || editable.parentElement;
                                if (parent && parent.querySelector('img')) return true;
                            }
                            // 兜底: 查找是否有内容为“图片1”或类似的元素(缩略图标题)
                            const all = Array.from(document.querySelectorAll('*'));
                            const hasPicThumb = all.some(el => {
                                const t = el.innerText && el.innerText.trim();
                                return t === '图片1' || t === '视频1' || (el.tagName === 'IMG' && el.src.includes('tos'));
                            });
                            return hasPicThumb;
                        }''')
                        if has_image:
                            print(f"  ✅ 图片上传完成 (elapsed: {(wait_i+1)*3}s)")
                            break
                        if wait_i > 0 and wait_i % 5 == 0:
                            print(f"    ⏳ 等待中... ({(wait_i+1)*3}s)")
                            
                    # 关闭弹出菜单 (用 Escape 键，不用 mouse.click 避免误触链接)
                    await page.keyboard.press('Escape')

                except Exception as e:
                    print(f"  ❌ 图片上传失败: {e}")

            await page.wait_for_timeout(2000)
            await screenshot(page, '3_6_image_uploaded')

        # === Step 4: 已在 Step 3.5 中选择了沉浸式短片模式，跳过 ===

        # === Step 5: 选模型 ===
        print(f"🤖 [Step 5] Selecting model: {model}...")

        # 5a: 点击工具栏的模型按钮 (显示 "2.0 Fast" 或 "2.0")
        # 关键: 不能用 Playwright text locator，因为底部卡片也含 "2.0" 文字
        # 必须限制到工具栏区域 (y在400-550, x>800)
        model_click = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll('*'));
            const btn = items.find(el => {
                const text = el.innerText && el.innerText.trim();
                if (!text || !text.includes('2.0')) return false;
                // 文本长度 < 15, 排除整个工具栏容器
                if (text.length > 15) return false;
                const rect = el.getBoundingClientRect();
                // 工具栏区域: y 在 400-700, x > 800, 小元素 (放宽因为图片预览导致下移)
                return rect.top > 400 && rect.top < 700 && rect.left > 800 &&
                       el.offsetHeight < 50 && el.offsetHeight > 15;
            });
            if (btn) {
                btn.click();
                const r = btn.getBoundingClientRect();
                return 'opened: ' + btn.innerText.trim() + ' (x=' + Math.round(r.left) + ', y=' + Math.round(r.top) + ')';
            }
            return 'NOT_FOUND';
        }''')
        print(f"  Model button: {model_click}")
        model_btn_clicked = 'opened' in model_click

        await page.wait_for_timeout(2000)
        await screenshot(page, '5a_model_dropdown')

        if model_btn_clicked:
            # 5b: 在下拉菜单中选目标模型
            want_fast = "Fast" in model
            model_select = await page.evaluate('''([wantFast]) => {
                const items = Array.from(document.querySelectorAll('*'));
                const candidates = items.filter(el => {
                    const text = el.innerText && el.innerText.trim();
                    if (!text) return false;
                    if (!/^Seedance/.test(text)) return false;
                    if (/[\u4e00-\u9fff]/.test(text)) return false;
                    if (el.offsetHeight > 40 || el.offsetHeight < 10) return false;
                    const rect = el.getBoundingClientRect();
                    // 放宽高度上限到 850 避免由于顶部有预览图导致菜单向下偏移被忽略
                    // 增加 X 轴限制 (> 900) 以过滤掉位于下方的底部 Seedance2.0 介绍卡片 (其 x 约等于 822)
                    return rect.left > 900 && rect.left < 1100 && rect.top > 350 && rect.top < 850;
                });
                for (const el of candidates) {
                    const text = el.innerText.trim();
                    const isFast = text.includes('Fast');
                    if (wantFast === isFast) {
                        el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, cancelable:true}));
                        el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, cancelable:true}));
                        el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
                        const r = el.getBoundingClientRect();
                        return 'selected: ' + text + ' (x=' + Math.round(r.left) + ', y=' + Math.round(r.top) + ')';
                    }
                }
                return 'NOT_FOUND: candidates=' + candidates.map(el => {
                    const r = el.getBoundingClientRect();
                    return '"' + el.innerText.trim() + '"(x=' + Math.round(r.left) + ',y=' + Math.round(r.top) + ')';
                }).join('; ');
            }''', [want_fast])
            print(f"  Model select: {model_select}")
            await page.wait_for_timeout(1500)
        await screenshot(page, '5b_model_selected')

        # === Step 6: 上传参考视频 (仅 V2V 模式) ===
        if ref_video:
            print(f"📎 [Step 6] Uploading reference video: {os.path.basename(ref_video)}")

            # 预检查并缩放视频
            actual_video_path = await check_and_resize_video(ref_video)
            is_temp = actual_video_path != ref_video

            try:
                # 6a: 点击工具栏的“参考素材”按钮 → 弹出面板
                panel_opened = await open_reference_material_panel(page)
                if not panel_opened:
                    print("  ❌ 未能打开参考素材面板")
                    await screenshot(page, '6a_ref_panel_failed')
                    await finalize()
                    return
                await page.wait_for_timeout(2000)
                await screenshot(page, '6a_ref_panel')

                # 6b: 上传本地视频
                uploaded = await upload_reference_media(page, actual_video_path, 'video')
                if not uploaded:
                    print("  ❌ 未能触发本地视频上传")
                    await screenshot(page, '6b_ref_upload_trigger_failed')
                    await finalize()
                    return
                print(f"  ✅ 文件已选择: {os.path.basename(actual_video_path)}")

                upload_ready = await wait_for_reference_media_ready(page, 'video')
                if not upload_ready:
                    print("  ❌ 参考视频在等待窗口内没有进入已挂载状态")
                    await screenshot(page, '6b_ref_upload_timeout')
                    await finalize()
                    return
                ref_video_ready = True

                # 关闭参考面板
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(1000)
                await screenshot(page, '6b_ref_uploaded')

            finally:
                if is_temp and os.path.exists(actual_video_path):
                    try:
                        os.remove(actual_video_path)
                        print(f"  🧹 已清理临时缩放视频: {actual_video_path}")
                    except:
                        pass

        # === Step 7: 选时长 ===
        step7_label = '7' if ref_video else '6'
        print(f"⏱️ [Step {step7_label}] Selecting duration: {duration}...")
        
        # 点击当前时长按钮 (显示 "5s"、"10s" 或 "15s")
        dur_btn = page.locator('text=/^\\d+s$/').first
        dur_opened = await safe_click(page, dur_btn, '时长按钮')
        await page.wait_for_timeout(1500)
        await screenshot(page, f'{step7_label}a_duration_dropdown')

        if dur_opened:
            try:
                dur_item = page.locator(f'text=/^{duration}$/').first
                await dur_item.click(timeout=3000)
                print(f"  ✅ 时长选择: {duration}")
            except Exception as e:
                print(f"  ⚠️ 时长选择: {e}")
            await page.wait_for_timeout(1000)
        await screenshot(page, f'{step7_label}b_duration_selected')

        # === Step 8: 注入 Prompt ===
        step8_label = '8' if ref_video else '7'
        print(f"📝 [Step {step8_label}] Injecting prompt: {prompt}")
        typed_ok = await fill_contenteditable(page, prompt, label="Prompt")
        if not typed_ok:
            inject_result = await page.evaluate('''([text]) => {
                const el = document.querySelector('div[contenteditable="true"]');
                if (el) {
                    el.innerText = text;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    return 'OK: ' + el.innerText.substring(0, 30) + '...';
                }
                return 'FAILED: no contenteditable found';
            }''', [prompt])
            print(f"  Inject(fallback): {inject_result}")
        await page.wait_for_timeout(1000)
        await screenshot(page, f'{step8_label}_prompt')

        # === Step 8: 验证/提交 ===
        if dry_run:
            await screenshot(page, '8_DRY_RUN_FINAL')
            status_text = await page.evaluate('''() => {
                const all = Array.from(document.querySelectorAll('*'));
                const info = all.find(el => {
                    const t = el.innerText && el.innerText.trim();
                    // 新 UI: 顶部显示 "沉浸式短片 Seedance 2.0 Fast 按 1 秒 3 积分扣除"
                    return t && t.includes('积分') && el.offsetHeight < 50;
                });
                return info ? info.innerText.trim() : 'NOT_FOUND';
            }''')
            editor_state = await collect_editor_state(page)
            ref_state_ok = True
            if ref_video:
                ref_state_ok = (
                    ref_video_ready or
                    editor_state['hasVideoThumb'] or
                    editor_state['hasImageThumb'] or
                    editor_state['hasCanvasThumb'] or
                    editor_state['hasBackgroundThumb'] or
                    editor_state['hasReplaceAction']
                )
            print(f"\n✅ DRY-RUN 完成！请检查截图 step_8_DRY_RUN_FINAL.png")
            print(f"📊 底部状态栏: {status_text}")
            print(f"🧪 表单状态: {json.dumps(editor_state, ensure_ascii=False)}")
            if ref_video and not ref_state_ok:
                print("❌ DRY-RUN 失败: V2V 参考视频没有出现在编辑器区域，当前流程还没跑通。")
                await finalize()
                return
            if editor_state['sendPresent'] and editor_state['sendDisabled']:
                print("⚠️ DRY-RUN 告警: 发送按钮仍是禁用态，页面可能还没接受当前表单。")
            print(f"\n确认无误后，去掉 --dry-run 参数重新运行即可提交任务。")
            await finalize()
            return

        # === Step 8: 设置 thread_id 拦截器 + 提交 ===
        thread_id = None
        async def sniff_thread(response):
            nonlocal thread_id
            if thread_id:
                return
            try:
                text = await response.text()
                if 'thread_id' in text:
                    import json as _json
                    # 尝试从 JSON 中提取 thread_id
                    data = _json.loads(text)
                    # thread_id 可能在不同层级
                    tid = None
                    if isinstance(data, dict):
                        tid = data.get('thread_id') or data.get('data', {}).get('thread_id')
                        if not tid and 'data' in data:
                            d = data['data']
                            if isinstance(d, dict):
                                tid = d.get('thread_id')
                                # 可能嵌套更深
                                for v in d.values():
                                    if isinstance(v, dict) and 'thread_id' in v:
                                        tid = v['thread_id']
                                        break
                    if not tid:
                        # 暴力正则
                        m = re.search(r'"thread_id"\s*:\s*"([^"]+)"', text)
                        if m:
                            tid = m.group(1)
                    if tid:
                        thread_id = tid
                        print(f"\n  🎯 Sniffed thread_id: {tid}")
            except Exception:
                pass

        page.on('response', sniff_thread)

        print("🖱️ [Step 8] Clicking send button (arrow)...")
        # 新 UI: 发送按钮是右下角的箭头图标 (lucide-arrow-up)
        submit_clicked = await safe_click(
            page, page.locator('button:has(svg.lucide-arrow-up)').first, '发送(箭头)', timeout=5000
        )
        await page.wait_for_timeout(5000)
        await screenshot(page, '8_submitted')

        if not submit_clicked:
            print("  ❌ Submit failed. Aborting.")
            await dump_debug_bundle(page, "submit_failed")
            await finalize()
            return

        # 等待 thread_id 被拦截
        for _ in range(10):
            if thread_id:
                break
            await page.wait_for_timeout(2000)

        if not thread_id:
            print("  ⚠️ thread_id not captured from responses, trying page HTML...")
            page_html = await page.content()
            m = re.search(r'thread_id["\s:=]+([0-9a-f-]{36})', page_html)
            if m:
                thread_id = m.group(1)
                print(f"  🎯 Found thread_id in HTML: {thread_id}")

        if not thread_id:
            print("  ❌ Could not get thread_id. Aborting.")
            await dump_debug_bundle(page, "thread_id_missing")
            await finalize()
            return

        # === Step 9: 导航到 thread 详情页 + 轮询视频 ===
        detail_url = detail_url_template.format(thread_id=thread_id)
        print(f"🔗 [Step 9] Navigating to thread detail page...")
        print(f"  URL: {detail_url}")
        await page.goto(detail_url, wait_until='domcontentloaded')
        await page.wait_for_timeout(8000)

        safe_name = ''.join(c for c in prompt[:15] if c.isalnum() or c in '_ ')
        filename = f"{safe_name}_{duration}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        print("⏳ Polling for video on detail page...")
        mp4_url = None
        for i in range(240):  # 延长至 240 次 (约 20 分钟)
            await page.wait_for_timeout(5000)

            # 双通道提取: DOM + 正则
            mp4_url = await page.evaluate(r'''() => {
                // 通道1: <video> 标签 src
                const v = document.querySelector('video');
                if (v && v.src && v.src.includes('.mp4')) return v.src;
                const s = document.querySelector('video source');
                if (s && s.src && s.src.includes('.mp4')) return s.src;
                // 通道2: 暴力正则
                const html = document.documentElement.innerHTML;
                const m = html.match(/https?:\/\/[^"'\\s\\\\]+\.mp4[^"'\\s\\\\]*/);
                return m ? m[0] : null;
            }''')

            if mp4_url:
                mp4_url = html.unescape(mp4_url)
                print(f"\n  🎉 Found MP4 at attempt {i+1}!")
                print(f"  🔗 {mp4_url[:120]}...")
                break

            if i % 12 == 0 and i > 0:
                print(f"  ⏳ Still generating... ({i*5}s elapsed)")
                # 刷新详情页
                await page.reload(wait_until='domcontentloaded')
                await page.wait_for_timeout(5000)
            print(".", end="", flush=True)

        if not mp4_url:
            print("\n  ❌ Timeout after 10 min")
            await screenshot(page, '9_timeout')
            await dump_debug_bundle(page, "detail_timeout")
            await finalize()
            return

        await screenshot(page, '9_video_ready')

        # === Step 10: curl 下载 ===
        print(f"📥 [Step 10] Downloading to {filepath}...")
        import subprocess
        result = subprocess.run(
            ['curl', '-L', '-o', filepath, '-s', '-w', '%{http_code}', mp4_url],
            capture_output=True, text=True, timeout=120
        )
        http_code = result.stdout.strip()

        if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  ✅ Saved: {os.path.abspath(filepath)} ({size_mb:.1f}MB) [HTTP {http_code}]")
        else:
            print(f"  ❌ Download failed: HTTP {http_code}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            print(f"  📋 Manual link: {mp4_url}")

        await finalize()

    print("\n🏁 Done!")

def get_cookies_path(platform: str, custom_path: str = None) -> str:
    """根据平台返回对应的 cookies 文件路径"""
    if custom_path and custom_path != "cookies.json":
        return custom_path
    # 默认按平台区分 cookies 文件
    return f"cookies_{platform}.json"

def get_storage_state_path(platform: str, custom_path: str = None) -> str:
    """根据平台返回对应的 storage_state 文件路径"""
    if custom_path:
        return custom_path
    return f"storage_{platform}.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jianying/Jimeng SeeDance 2.0 Video Generator")
    parser.add_argument("--prompt", type=str, default="一个美女在跳舞", help="Video description")
    parser.add_argument("--duration", type=str, default="10s", choices=["5s", "10s", "15s"])
    parser.add_argument("--ratio", type=str, default="横屏", choices=["横屏", "竖屏", "方屏"])
    parser.add_argument("--model", type=str, default="Seedance 2.0",
                        choices=["Seedance 2.0", "Seedance 2.0 Fast"])
    parser.add_argument("--ref-video", type=str, default=None, help="Reference video file path (V2V mode)")
    parser.add_argument("--ref-image", type=str, default=None, help="Reference image file path (I2V mode)")
    parser.add_argument("--cookies", type=str, default=None, help="Path to cookies.json (default: cookies_{platform}.json)")
    parser.add_argument("--storage-state", type=str, default=None,
                        help="Path to Playwright storage_state.json (default: storage_{platform}.json if present)")
    parser.add_argument("--output-dir", type=str, default=".", help="Directory to save output video")
    parser.add_argument("--dry-run", action="store_true", help="Only fill form, don't submit")
    parser.add_argument("--platform", type=str, default="xyq", choices=["xyq", "jimeng"],
                        help="Platform: xyq (小云雀) or jimeng (即梦AI)")
    parser.add_argument("--auto-login", action="store_true",
                        help="Auto login via QR code and save cookies")
    parser.add_argument("--headed", action="store_true",
                        help="Run with visible browser window (not headless)")
    parser.add_argument("--slowmo-ms", type=int, default=0,
                        help="Slow down Playwright actions for debugging (ms)")
    parser.add_argument("--debug-dir", type=str, default=None,
                        help="Directory to store screenshots/HTML dumps")
    parser.add_argument("--trace", action="store_true",
                        help="Save Playwright trace zip (stored in debug-dir or output-dir)")
    args = parser.parse_args()

    # 获取 cookies 路径
    COOKIES_FILE = get_cookies_path(args.platform, args.cookies)
    STORAGE_STATE_FILE = get_storage_state_path(args.platform, args.storage_state)
    DOWNLOAD_DIR = args.output_dir
    DEBUG_DIR = args.debug_dir
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    if DEBUG_DIR:
        os.makedirs(DEBUG_DIR, exist_ok=True)

    # 全局运行开关（避免大范围改动函数签名）
    RUN_HEADED = bool(args.headed)
    RUN_SLOWMO_MS = int(args.slowmo_ms or 0)
    RUN_TRACE = bool(args.trace)

    # 自动登录模式
    if args.auto_login:
        success = asyncio.run(auto_login(args.platform, COOKIES_FILE, STORAGE_STATE_FILE))
        if success:
            print("\n✅ 登录完成！现在可以运行视频生成命令了")
        exit(0 if success else 1)

    # 检查 cookies 文件
    has_storage_state = bool(STORAGE_STATE_FILE and os.path.exists(STORAGE_STATE_FILE))
    if not os.path.exists(COOKIES_FILE) and not has_storage_state:
        print(f"⚠️ {COOKIES_FILE} not found!")
        print(f"   且未发现 storage_state: {STORAGE_STATE_FILE}")
        print(f"   请运行以下命令进行自动登录:")
        print(f"   python3 scripts/jianying_worker.py --auto-login --platform {args.platform}")
        exit(1)
    if has_storage_state and not os.path.exists(COOKIES_FILE):
        print(f"ℹ️ cookies not found, will use storage_state: {STORAGE_STATE_FILE}")

    asyncio.run(run(args.prompt, args.duration, args.ratio, args.model, args.dry_run, args.ref_video, args.ref_image, args.platform, COOKIES_FILE))
