"""
dy login / logout / status — 认证命令。
"""
from __future__ import annotations

import click

from dy_cli.engines.playwright_client import PlaywrightClient, PlaywrightError
from dy_cli.utils import config
from dy_cli.utils.output import success, error, info, warning, status, console


@click.command("login", help="登录抖音 (浏览器扫码)")
@click.option("--account", default=None, help="账号名")
def login(account):
    """打开浏览器扫码登录抖音。"""
    cfg = config.load_config()
    client = PlaywrightClient(
        account=account,
        headless=False,
        slow_mo=cfg["playwright"].get("slow_mo", 0),
    )

    # Check if already logged in
    if client.cookie_exists() and client.check_login():
        success("已登录抖音")
        if not click.confirm("是否重新登录?", default=False):
            return

    info("正在打开浏览器，请使用抖音 App 扫码...")
    try:
        ok = client.login()
        if ok:
            success("登录成功! 🎉")
        else:
            error("登录超时或失败")
            raise SystemExit(1)
    except PlaywrightError as e:
        error(f"登录失败: {e}")
        raise SystemExit(1)


@click.command("logout", help="退出登录")
@click.option("--account", default=None, help="账号名")
def logout(account):
    """退出登录（删除 Cookie）。"""
    client = PlaywrightClient(account=account)
    if client.logout():
        success("已退出登录，Cookie 已删除")
    else:
        info("未找到登录凭据")


@click.command("status", help="查看登录状态")
@click.option("--account", default=None, help="账号名")
def auth_status(account):
    """检查登录状态。"""
    console.print()
    client = PlaywrightClient(account=account)

    if not client.cookie_exists():
        status("登录状态", "未登录 (无 Cookie 文件)", "red")
        info("使用 [bold]dy login[/] 登录")
    else:
        info("正在验证 Cookie...")
        try:
            logged_in = client.check_login()
            if logged_in:
                status("登录状态", "已登录", "green")
                status("Cookie", client.cookie_file, "dim")
            else:
                status("登录状态", "Cookie 已失效", "yellow")
                info("使用 [bold]dy login[/] 重新登录")
        except Exception as e:
            status("登录状态", f"检查失败: {e}", "red")

    console.print()
