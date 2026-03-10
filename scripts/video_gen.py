import os
import time
import requests
import json
import argparse
from typing import Optional

class VideoGenerator:
    """Seedance 2.0 / Sora 2 视频生成核心类"""
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.atlascloud.ai/v1"):
        self.api_key = api_key or os.getenv("SEEDANCE_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise ValueError("SEEDANCE_API_KEY is not set. Please configure it via environment variables.")

    def generate(self, prompt: str, model: str = "openai/sora-2", 
                 duration: int = 10, resolution: str = "1080p") -> str:
        """提交视频生成任务"""
        print(f"🚀 发起视频生成任务 ({model}): {prompt[:50]}...")
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "no_watermark": True  # 尝试请求去水印版本
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(f"{self.base_url}/model/generateVideo", headers=headers, json=payload)
            response.raise_for_status()
            request_id = response.json().get("request_id")
            if not request_id:
                raise Exception(f"Failed to get request_id: {response.text}")
            return request_id
        except requests.exceptions.RequestException as e:
            raise Exception(f"API Request failed: {str(e)}")

    def poll(self, request_id: str, interval: int = 10, timeout: int = 600) -> str:
        """轮询生成结果"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/model/prediction/{request_id}/get", headers=headers)
                response.raise_for_status()
                result = response.json()
                status = result.get("status")
                
                if status == "succeeded":
                    output_url = result.get("output_url")
                    if not output_url:
                        # Some APIs return result in different fields
                        output_url = result.get("output", {}).get("url")
                    print("\n✅ 视频生成成功!")
                    return output_url
                elif status == "failed":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"❌ 视频生成失败: {error_msg}")
                
                elapsed = int(time.time() - start_time)
                print(f"⏳ 正在生成中... ({elapsed}s)", end="\r")
                time.sleep(interval)
            except requests.exceptions.RequestException as e:
                print(f"\n⚠️ 轮询连接异常: {e}，5秒后重试...")
                time.sleep(5)
        
        raise TimeoutError(f"❌ 视频生成任务超时 (超过 {timeout}s)。")

    def download(self, url: str, filename: str = "output.mp4") -> str:
        """下载视频到本地"""
        print(f"📥 正在从 {url} 下载视频...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # 确保保存路径存在
            save_path = os.path.abspath(filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ 视频已保存至: {save_path}")
            return save_path
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sora/Seedance Video Generator CLI")
    parser.add_argument("--prompt", required=True, help="Video generation prompt")
    parser.add_argument("--output", default="output.mp4", help="Output filename")
    parser.add_argument("--model", default="openai/sora-2")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--resolution", default="1080p")
    
    args = parser.parse_args()
    
    try:
        gen = VideoGenerator()
        req_id = gen.generate(args.prompt, model=args.model, duration=args.duration, resolution=args.resolution)
        video_url = gen.poll(req_id)
        local_path = gen.download(video_url, args.output)
        print(f"RESULT_PATH:{local_path}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        exit(1)
