import os
import time
import requests
import json
import argparse
from typing import Optional

class VolcengineVideoGenerator:
    """火山引擎 (Volcengine) Seedance 2.0 视频生成核心类"""
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://ark.cn-beijing.volces.com/api/v3"):
        self.api_key = api_key or os.getenv("VOLC_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise ValueError("VOLC_API_KEY is not set. Please get it from Volcengine Ark console.")

    def generate(self, prompt: str, model_endpoint: str, 
                 duration: int = 10, resolution: str = "1080p") -> str:
        """提交视频生成任务"""
        print(f"🚀 [火山引擎] 发起视频生成任务: {prompt[:50]}...")
        
        # 火山引擎 Ark API 结构
        payload = {
            "model": model_endpoint, # 此处通常是推理终端 ID
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "fps": 24,
            "logo_info": {
                "add_logo": False # 显式请求不添加水印/Logo
            }
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 实际 API Endpoint 请参考火山引擎最新文档，通常为 /video_generation/tasks
        url = f"{self.base_url}/video_generation/tasks"
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # 根据火山文档，返回可能在 id 或 task_id
            task_id = data.get("id") or data.get("task_id")
            if not task_id:
                raise Exception(f"Failed to get task_id: {data}")
            return task_id
        except requests.exceptions.RequestException as e:
            raise Exception(f"Volcengine API Request failed: {str(e)}")

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/video_generation/tasks/{task_id}"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # 火山 Ark 状态字段通常在 task_status 或 status
                status = result.get("status") or result.get("task_status")
                
                if status == "succeeded" or status == "completed":
                    # 视频链接通常在 video_url 或 output 中
                    video_url = result.get("video_url") or result.get("output", {}).get("video_url")
                    if not video_url:
                        raise Exception(f"Success but no video_url found: {result}")
                    print("\n✅ 视频生成成功!")
                    return video_url
                elif status == "failed":
                    error_msg = result.get("error_message") or result.get("reason") or "Unknown error"
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
        response = requests.get(url, stream=True)
        response.raise_for_status()
        save_path = os.path.abspath(filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Volcengine Seedance 2.0 CLI")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--endpoint", required=True, help="Your Model Endpoint ID from Volcengine Ark")
    parser.add_argument("--output", default="output.mp4")
    
    args = parser.parse_args()
    
    try:
        gen = VolcengineVideoGenerator()
        tid = gen.generate(args.prompt, model_endpoint=args.endpoint)
        url = gen.poll(tid)
        path = gen.download(url, args.output)
        print(f"RESULT_PATH:{path}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        exit(1)
