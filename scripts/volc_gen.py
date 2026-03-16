import os
import sys
import time
import requests
import argparse
from typing import Optional


import base64
import mimetypes


class VolcengineVideoGenerator:
    """火山引擎 (Volcengine) Seedance 视频生成核心类 (适配最新 /contents/generations/tasks 接口)"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
    ):
        self.api_key = api_key or os.getenv("VOLC_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise ValueError(
                "VOLC_API_KEY is not set. Please get it from Volcengine Ark console."
            )

    def generate(
        self,
        prompt: str,
        model_endpoint: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        duration: int = 5,
    ) -> str:
        """提交视频生成任务"""
        print(f"🚀 [火山引擎] 发起视频生成任务: {prompt[:50]}...")

        # 将配置参数追加到 prompt 中
        # 项目默认使用无水印生成，保证纯净素材
        full_prompt = f"{prompt} --duration {duration} --watermark false"

        content = [{"type": "text", "text": full_prompt}]

        # 如果有 image_url，则为图生视频任务
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        elif image_path:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/jpeg"
            with open(image_path, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode("utf-8")
            data_uri = f"data:{mime_type};base64,{base64_data}"
            content.append({"type": "image_url", "image_url": {"url": data_uri}})

        payload = {
            "model": model_endpoint,  # 此处通常是推理终端 ID 或模型名称
            "content": content,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/contents/generations/tasks"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            task_id = data.get("id") or data.get("task_id")
            if not task_id:
                raise Exception(f"Failed to get task_id: {data}")
            return task_id
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Volcengine API Request failed: {str(e)}\nResponse: {e.response.text if e.response else ''}"
            )

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/contents/generations/tasks/{task_id}"

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                result = response.json()

                status = result.get("status")

                if status == "succeeded" or status == "completed":
                    video_url = result.get("content", {}).get(
                        "video_url"
                    ) or result.get("video_url")
                    if not video_url:
                        raise Exception(f"Success but no video_url found: {result}")
                    print("\n✅ 视频生成成功!")
                    return video_url
                elif status in ["failed", "error"]:
                    error_msg = (
                        result.get("error", {}).get("message")
                        or result.get("error_message")
                        or result.get("reason")
                        or "Unknown error"
                    )
                    raise Exception(f"❌ 视频生成失败: {error_msg}")

                elapsed = int(time.time() - start_time)
                print(f"⏳ 任务状态: {status} ({elapsed}s)", end="\r")
                time.sleep(interval)
            except requests.exceptions.RequestException as e:
                print(f"\n⚠️ 轮询异常: {e}，正在重试...")
                time.sleep(5)

        raise TimeoutError(f"❌ 任务 {task_id} 超时。")

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """保存视频"""
        print(f"📥 下载视频: {url}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            save_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Volcengine Seedance CLI")
    parser.add_argument(
        "--api_key",
        default=None,
        help="火山引擎 API Key，若不传则读取 VOLC_API_KEY 环境变量",
    )
    parser.add_argument("--prompt", required=True, help="视频生成提示词")
    parser.add_argument(
        "--endpoint", required=True, help="Your Model Endpoint ID from Volcengine Ark"
    )
    parser.add_argument(
        "--image_url", default=None, help="图生视频的首帧图片 URL（选填）"
    )
    parser.add_argument(
        "--image_path", default=None, help="图生视频的首帧本地图片路径（选填）"
    )
    parser.add_argument("--duration", type=int, default=5, help="视频时长 (默认 5 秒)")
    parser.add_argument("--output", default="output.mp4", help="下载文件的保存路径")

    args = parser.parse_args()

    try:
        gen = VolcengineVideoGenerator(api_key=args.api_key)
        tid = gen.generate(
            prompt=args.prompt,
            model_endpoint=args.endpoint,
            image_url=args.image_url,
            image_path=args.image_path,
            duration=args.duration,
        )
        url = gen.poll(tid)
        path = gen.download(url, args.output)
        print(f"RESULT_PATH:{path}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
