"""
dy download — 无水印下载命令（抖音特色功能）。
"""
from __future__ import annotations

import os
import re

import click
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn

from dy_cli.engines.api_client import DouyinAPIClient, DouyinAPIError
from dy_cli.utils import config
from dy_cli.utils.output import success, error, info, warning, console


@click.command("download", help="下载抖音视频/图片 (无水印)")
@click.argument("url_or_id")
@click.option("--output-dir", "-o", default=None, help="保存目录 (默认 ~/Downloads/douyin)")
@click.option("--music", is_flag=True, help="同时下载背景音乐")
@click.option("--account", default=None, help="使用指定账号")
@click.option("--json-output", "as_json", is_flag=True, help="仅输出下载链接 (JSON)")
def download(url_or_id, output_dir, music, account, as_json):
    """
    下载抖音视频/图片（无水印）。

    支持:
    - 分享链接: https://v.douyin.com/xxxxx/
    - 完整链接: https://www.douyin.com/video/1234567890
    - 视频 ID: 1234567890
    """
    cfg = config.load_config()
    output_dir = output_dir or cfg["default"].get("download_dir", os.path.expanduser("~/Downloads/douyin"))
    os.makedirs(output_dir, exist_ok=True)

    client = DouyinAPIClient.from_config(account)

    try:
        # Resolve aweme_id
        if url_or_id.isdigit():
            aweme_id = url_or_id
        else:
            info("正在解析分享链接...")
            aweme_id = client.resolve_share_url(url_or_id)

        info(f"视频 ID: {aweme_id}")

        # Get download info
        info("正在获取下载链接...")
        dl_info = client.get_download_url(aweme_id)

        if as_json:
            from dy_cli.utils.output import print_json
            print_json(dl_info)
            return

        desc = dl_info.get("desc", "untitled")
        author = dl_info.get("author", "unknown")

        # Sanitize filename
        safe_name = re.sub(r'[\\/:*?"<>|\n\r]', '_', desc)[:50].strip('_') or aweme_id
        prefix = f"{author}_{safe_name}"

        downloaded_files = []

        # Download video
        video_url = dl_info.get("video_url")
        if video_url:
            video_path = os.path.join(output_dir, f"{prefix}.mp4")
            info(f"正在下载视频...")
            _download_with_progress(client, video_url, video_path)
            downloaded_files.append(video_path)

        # Download images (for image posts)
        image_urls = dl_info.get("images")
        if image_urls:
            for idx, img_url in enumerate(image_urls, 1):
                img_path = os.path.join(output_dir, f"{prefix}_{idx}.jpg")
                info(f"正在下载图片 {idx}/{len(image_urls)}...")
                _download_with_progress(client, img_url, img_path)
                downloaded_files.append(img_path)

        # Download music
        if music:
            music_url = dl_info.get("music_url")
            if music_url:
                music_path = os.path.join(output_dir, f"{prefix}_music.mp3")
                info(f"正在下载音乐...")
                _download_with_progress(client, music_url, music_path)
                downloaded_files.append(music_path)
            else:
                warning("未找到背景音乐")

        # Summary
        if downloaded_files:
            console.print()
            success(f"下载完成! ({len(downloaded_files)} 个文件)")
            for f in downloaded_files:
                size = os.path.getsize(f)
                size_str = f"{size / 1024 / 1024:.1f}MB" if size > 1024 * 1024 else f"{size / 1024:.0f}KB"
                console.print(f"  📁 {f} ({size_str})")
        else:
            warning("未找到可下载的内容")

    except DouyinAPIError as e:
        error(f"下载失败: {e}")
        raise SystemExit(1)
    finally:
        client.close()


def _download_with_progress(client: DouyinAPIClient, url: str, output_path: str):
    """带进度条的下载。"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(os.path.basename(output_path), total=None)

        def on_progress(downloaded: int, total: int):
            if total > 0:
                progress.update(task, total=total, completed=downloaded)
            else:
                progress.update(task, completed=downloaded)

        client.download_file(url, output_path, progress_callback=on_progress)
