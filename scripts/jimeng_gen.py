import os
import time
import requests
import argparse
import base64
from typing import Optional
from volcengine.visual.VisualService import VisualService

class JimengVideoGenerator:
    """即梦AI (Jimeng) 视频生成3.0 Pro 核心类"""
    def __init__(self, ak: Optional[str] = None, sk: Optional[str] = None):
        self.ak = ak or os.getenv("VOLC_ACCESSKEY")
        self.sk = sk or os.getenv("VOLC_SECRETKEY")
        if not self.ak or not self.sk:
            raise ValueError("VOLC_ACCESSKEY or VOLC_SECRETKEY is not set. Please provide them or set environment variables.")
        
        self.visual_service = VisualService()
        self.visual_service.set_ak(self.ak)
        self.visual_service.set_sk(self.sk)

    def generate(self, prompt: str, image_url: Optional[str] = None, image_path: Optional[str] = None,
                 duration: int = 5, aspect_ratio: str = "16:9") -> str:
        """提交视频生成任务"""
        print(f"🚀 [即梦AI] 发起视频生成任务: {prompt[:50]}...")
        
        # 帧数 = 24 * n + 1，其中n为秒数，支持5s、10s
        frames = 121 if duration <= 5 else 241
        
        formdata = {
            "req_key": "jimeng_ti2v_v30_pro",
            "prompt": prompt,
            "frames": frames,
            "aspect_ratio": aspect_ratio
        }
        
        if image_url:
            formdata["image_urls"] = [image_url]
        elif image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
            formdata["binary_data_base64"] = [base64.b64encode(image_data).decode("utf-8")]
            
        try:
            resp = self.visual_service.cv_sync2async_submit_task(formdata)
            # The SDK returns a dict directly or response object, let's assume it returns a dict based on standard behavior
            if "code" in resp and resp["code"] != 10000:
                raise Exception(f"API Error: {resp.get('message', 'Unknown Error')} (Code: {resp['code']})")
                
            data = resp.get("data", {})
            task_id = data.get("task_id")
            if not task_id:
                raise Exception(f"Failed to get task_id: {resp}")
            return task_id
        except Exception as e:
            raise Exception(f"Jimeng API Submit Request failed: {str(e)}")

    def poll(self, task_id: str, interval: int = 15, timeout: int = 900) -> str:
        """轮询任务状态"""
        start_time = time.time()
        
        formdata = {
            "req_key": "jimeng_ti2v_v30_pro",
            "task_id": task_id
        }
        
        while time.time() - start_time < timeout:
            try:
                resp = self.visual_service.cv_sync2async_get_result(formdata)
                if "code" in resp and resp["code"] != 10000:
                    raise Exception(f"API Error: {resp.get('message', 'Unknown Error')} (Code: {resp['code']})")
                    
                data = resp.get("data", {})
                status = data.get("status")
                
                if status == "done":
                    video_url = data.get("video_url")
                    if not video_url:
                        raise Exception(f"Success but no video_url found: {resp}")
                    print("\n✅ 视频生成成功!")
                    return video_url
                elif status in ["failed", "not_found", "expired"]:
                    raise Exception(f"❌ 视频生成失败: Status {status}")
                
                elapsed = int(time.time() - start_time)
                print(f"⏳ 任务状态: {status} ({elapsed}s)", end="\r")
                time.sleep(interval)
            except Exception as e:
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
    parser = argparse.ArgumentParser(description="Volcengine Jimeng 3.0 Pro CLI")
    parser.add_argument("--ak", default=None, help="火山引擎 Access Key，若不传则读取 VOLC_ACCESSKEY 环境变量")
    parser.add_argument("--sk", default=None, help="火山引擎 Secret Key，若不传则读取 VOLC_SECRETKEY 环境变量")
    parser.add_argument("--prompt", required=True, help="视频生成提示词")
    parser.add_argument("--image_url", default=None, help="图生视频的首帧图片 URL（选填）")
    parser.add_argument("--image_path", default=None, help="图生视频的首帧本地图片路径（选填）")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10], help="视频时长 (5 或 10，默认 5)")
    parser.add_argument("--aspect_ratio", default="16:9", choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9"], help="文生视频的长宽比 (默认 16:9)")
    parser.add_argument("--output", default="output.mp4", help="下载文件的保存路径")
    
    args = parser.parse_args()
    
    try:
        gen = JimengVideoGenerator(ak=args.ak, sk=args.sk)
        tid = gen.generate(
            prompt=args.prompt, 
            image_url=args.image_url,
            image_path=args.image_path,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio
        )
        url = gen.poll(tid)
        path = gen.download(url, args.output)
        print(f"RESULT_PATH:{path}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        exit(1)
