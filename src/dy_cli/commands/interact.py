"""
dy like / comment / favorite / follow — 互动命令。
"""
from __future__ import annotations

import click

from dy_cli.engines.api_client import DouyinAPIClient, DouyinAPIError
from dy_cli.utils.output import success, error, info, console, print_comments


def _get_client(account=None):
    return DouyinAPIClient.from_config(account)


@click.command("like", help="点赞视频")
@click.argument("aweme_id")
@click.option("--unlike", is_flag=True, help="取消点赞")
@click.option("--account", default=None, help="使用指定账号")
def like(aweme_id, unlike, account):
    """点赞或取消点赞。"""
    action = "取消点赞" if unlike else "点赞"
    info(f"正在{action}: {aweme_id}")

    # Note: Like requires signed API calls or Playwright interaction.
    # This is a placeholder — actual implementation needs browser automation.
    try:
        from dy_cli.engines.playwright_client import PlaywrightClient, PlaywrightError
        # For now, use API client to verify video exists
        client = _get_client(account)
        detail = client.get_video_detail(aweme_id)
        desc = detail.get("desc", "")[:30]
        info(f"视频: {desc}")
        client.close()

        # TODO: Implement via Playwright interaction on douyin.com
        info(f"互动功能需要浏览器自动化 (即将支持)")
        info(f"可手动访问: https://www.douyin.com/video/{aweme_id}")

    except DouyinAPIError as e:
        error(f"{action}失败: {e}")
        raise SystemExit(1)


@click.command("favorite", help="收藏视频")
@click.argument("aweme_id")
@click.option("--unfavorite", is_flag=True, help="取消收藏")
@click.option("--account", default=None, help="使用指定账号")
def favorite(aweme_id, unfavorite, account):
    """收藏或取消收藏。"""
    action = "取消收藏" if unfavorite else "收藏"
    info(f"正在{action}: {aweme_id}")

    try:
        client = _get_client(account)
        detail = client.get_video_detail(aweme_id)
        desc = detail.get("desc", "")[:30]
        info(f"视频: {desc}")
        client.close()

        info(f"互动功能需要浏览器自动化 (即将支持)")
        info(f"可手动访问: https://www.douyin.com/video/{aweme_id}")

    except DouyinAPIError as e:
        error(f"{action}失败: {e}")
        raise SystemExit(1)


@click.command("comment", help="评论视频")
@click.argument("aweme_id")
@click.option("--content", "-c", required=True, help="评论内容")
@click.option("--account", default=None, help="使用指定账号")
def comment(aweme_id, content, account):
    """发表评论。"""
    info(f"正在评论: {aweme_id}")

    try:
        client = _get_client(account)
        detail = client.get_video_detail(aweme_id)
        desc = detail.get("desc", "")[:30]
        info(f"视频: {desc}")
        client.close()

        info(f"评论功能需要浏览器自动化 (即将支持)")
        info(f"可手动访问: https://www.douyin.com/video/{aweme_id}")

    except DouyinAPIError as e:
        error(f"评论失败: {e}")
        raise SystemExit(1)


@click.command("comments", help="查看视频评论")
@click.argument("aweme_id")
@click.option("--count", type=int, default=20, help="评论数量")
@click.option("--account", default=None, help="使用指定账号")
@click.option("--json-output", "as_json", is_flag=True, help="输出 JSON")
def comments(aweme_id, count, account, as_json):
    """查看视频评论列表。"""
    client = _get_client(account)

    try:
        info(f"正在获取评论: {aweme_id}")
        data = client.get_comments(aweme_id, count=count)
        comment_list = data.get("comments", [])

        if as_json:
            from dy_cli.utils.output import print_json
            print_json(data)
        else:
            print_comments(comment_list)

    except DouyinAPIError as e:
        error(f"获取评论失败: {e}")
        raise SystemExit(1)
    finally:
        client.close()


@click.command("follow", help="关注用户")
@click.argument("sec_user_id")
@click.option("--unfollow", is_flag=True, help="取消关注")
@click.option("--account", default=None, help="使用指定账号")
def follow(sec_user_id, unfollow, account):
    """关注或取消关注用户。"""
    action = "取消关注" if unfollow else "关注"
    info(f"正在{action}用户: {sec_user_id}")

    try:
        client = _get_client(account)
        profile = client.get_user_profile(sec_user_id)
        nickname = profile.get("nickname", "-")
        info(f"用户: {nickname}")
        client.close()

        info(f"关注功能需要浏览器自动化 (即将支持)")

    except DouyinAPIError as e:
        error(f"{action}失败: {e}")
        raise SystemExit(1)
