"""
Replicate API 整合模組 for ComfyUI
支援多種 Replicate 平台上的模型
"""

import os
import time
import replicate
import requests
import tempfile
from dotenv import load_dotenv

# 嘗試載入 model_configs
try:
    from .model_configs import REPLICATE_MODELS, get_model_config
    HAS_MODEL_CONFIGS = True
except ImportError:
    HAS_MODEL_CONFIGS = False
    REPLICATE_MODELS = {}

# Load environment variables
load_dotenv()

# Also try to load from the plugin directory
plugin_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(plugin_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Try to import ComfyUI's folder_paths, use fallback if not available
try:
    import folder_paths
except ImportError:
    # Fallback for testing outside ComfyUI environment
    class FolderPaths:
        @staticmethod
        def get_output_directory():
            return os.path.join(os.getcwd(), "output")
    folder_paths = FolderPaths()


class ReplicateAPI:
    """
    通用 Replicate API 客戶端，支援多種模型
    """
    
    def __init__(self, api_token=None):
        """
        初始化 Replicate API 客戶端
        
        Args:
            api_token (str, optional): Replicate API token. 若未提供，將從環境變數讀取。
        """
        self.api_token = api_token or os.getenv('REPLICATE_API_TOKEN')
        
        if not self.api_token:
            raise ValueError(
                "找不到 Replicate API token。請執行以下任一方式：\n"
                "1. 在 .env 檔案中設定 REPLICATE_API_TOKEN\n"
                "2. 初始化 ReplicateAPI 時提供 api_token 參數\n"
                "從以下網址取得 API token: https://replicate.com/account/api-tokens"
            )
        
        # Set the API token for the replicate library
        os.environ['REPLICATE_API_TOKEN'] = self.api_token
        
        print("✅ Replicate API 初始化成功")
    
    def upload_file(self, file_path):
        """
        上傳檔案到 Replicate 託管服務
        
        Args:
            file_path (str): 要上傳的檔案路徑
        
        Returns:
            str: 上傳檔案的公開 URL
        """
        try:
            print(f"📤 上傳檔案: {file_path}")
            
            # Use Replicate's file upload
            with open(file_path, 'rb') as file:
                uploaded_file = replicate.files.create(file)
            
            # Get the URL - uploaded_file.urls is a dict with a 'get' key
            if hasattr(uploaded_file, 'urls'):
                # urls is a dict, access the 'get' key
                if isinstance(uploaded_file.urls, dict):
                    file_url = uploaded_file.urls.get('get') or uploaded_file.urls.get('url')
                else:
                    file_url = str(uploaded_file.urls)
            elif hasattr(uploaded_file, 'url'):
                file_url = uploaded_file.url
            else:
                # Fallback: convert to string
                file_url = str(uploaded_file)
            
            print(f"✅ 檔案上傳成功: {file_url}")
            return file_url
            
        except Exception as e:
            print(f"❌ 上傳檔案時發生錯誤: {e}")
            print(f"   檔案路徑: {file_path}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_model(self, model_id, inputs, output_filename="replicate_output"):
        """
        執行任意 Replicate 模型
        
        Args:
            model_id (str): 模型識別碼
            inputs (dict): 模型輸入參數
            output_filename (str): 輸出檔案基本名稱
        
        Returns:
            Union[str, list]: 輸出檔案路徑或路徑列表
        """
        # Get model configuration
        config = None
        if HAS_MODEL_CONFIGS:
            config = get_model_config(model_id)
        
        if config:
            model_name = config["name"]
            print(f"🤖 執行模型: {model_name}")
        else:
            # Fallback for models not in config
            model_name = model_id if '/' in model_id else f"replicate/{model_id}"
            print(f"🤖 執行模型: {model_name}")
        
        print(f"📝 輸入: {inputs}")
        
        try:
            # Run the model on Replicate
            print(f"📡 傳送請求到 Replicate...")
            
            output = replicate.run(model_name, input=inputs)
            
            print(f"✅ 模型執行完成")
            
            # Handle different output types
            if config:
                outputs = config.get("outputs", ["video"])
                has_audio = config.get("has_audio", False)
                
                if len(outputs) == 1 and not has_audio:
                    # Single output
                    return self._process_output(output, outputs[0], output_filename)
                elif len(outputs) > 1 or has_audio:
                    # Multiple outputs
                    results = []
                    if isinstance(output, (list, tuple)):
                        for i, output_type in enumerate(outputs):
                            if i < len(output):
                                result = self._process_output(output[i], output_type, f"{output_filename}_{output_type}")
                                results.append(result)
                            else:
                                results.append(None)
                    else:
                        # Single output but model has audio
                        video_path = self._process_output(output, outputs[0], output_filename)
                        results.append(video_path)
                        
                        if has_audio and video_path:
                            audio_path = self._extract_audio_from_video(video_path, f"{output_filename}_audio")
                            results.append(audio_path)
                        else:
                            results.append(None)
                    
                    return results
            
            # Default: assume video output
            return self._process_output(output, "video", output_filename)
                
        except Exception as e:
            print(f"❌ 模型執行時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_output(self, output, output_type, filename):
        """
        根據類型處理模型輸出
        
        Args:
            output: 模型輸出
            output_type (str): 輸出類型 ("video", "image", "audio", "3d", "json")
            filename (str): 儲存的基本檔名
        
        Returns:
            str/dict: 下載/儲存的檔案路徑，或 JSON 資料
        """
        # Handle JSON output (e.g., voice-cloning)
        if output_type == "json":
            if isinstance(output, dict):
                return output
            if hasattr(output, '__dict__'):
                return vars(output)
            try:
                import json
                return json.loads(str(output))
            except Exception:
                return {"result": str(output)}
        
        # Get URL from output
        if hasattr(output, 'url'):
            url = output.url
        elif isinstance(output, str):
            url = output
        elif isinstance(output, list) and len(output) > 0:
            return self._process_output(output[0], output_type, filename)
        else:
            print(f"⚠️ 非預期的輸出格式: {type(output)}")
            url = str(output)
        
        print(f"📥 輸出 URL: {url}")
        
        # Determine file extension
        extension_map = {
            "video": ".mp4",
            "image": ".png",
            "audio": ".wav",
            "3d": ".glb",
        }
        extension = extension_map.get(output_type, ".mp4")
        
        # Download the file
        return self._download_file(url, filename, extension)
    
    def _download_file(self, url, filename, extension):
        """
        從 URL 下載檔案
        
        Args:
            url (str): 下載的 URL
            filename (str): 基本檔名
            extension (str): 副檔名
        
        Returns:
            str: 下載的檔案路徑
        """
        try:
            print(f"⬇️ 下載中: {url}")
            
            # Get output directory
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # Create output path with timestamp
            timestamp = int(time.time())
            output_path = os.path.join(output_dir, f"{filename}_{timestamp}{extension}")
            
            # Download the file
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✅ 檔案下載成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ 下載檔案時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_audio_from_video(self, video_path, output_filename):
        """
        從影片檔案提取音訊
        
        Args:
            video_path (str): 影片檔案路徑
            output_filename (str): 音訊檔案基本名稱
        
        Returns:
            str: 提取的音訊檔案路徑
        """
        try:
            import subprocess
            
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = int(time.time())
            audio_path = os.path.join(output_dir, f"{output_filename}_{timestamp}.wav")
            
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # WAV format
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite
                audio_path
            ]
            
            print(f"🎵 從影片提取音訊...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(audio_path):
                print(f"✅ 音訊提取完成: {audio_path}")
                return audio_path
            else:
                print(f"⚠️ 無法提取音訊: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"⚠️ 提取音訊時發生錯誤: {e}")
            return None
    
    def get_available_models(self):
        """
        取得所有可用的模型列表
        
        Returns:
            dict: 可用模型字典
        """
        return REPLICATE_MODELS if HAS_MODEL_CONFIGS else {}


class SyncAPI(ReplicateAPI):
    """
    舊版 API 類別，用於 lipsync 功能
    保持向後相容性
    """
    
    def generate_lipsync(self, video_url=None, audio_url=None, video_path=None, audio_path=None, 
                        output_filename="lipsync_output", model="lipsync-2-pro",
                        sync_mode="loop", temperature=0.5, active_speaker=False):
        """
        使用 Replicate API 生成嘴唇同步影片
        舊版方法，保持向後相容
        """
        print(f"🎬 開始生成 lipsync...")
        print(f"🤖 模型: sync/{model}")
        
        # Handle local file uploads
        if video_path and not video_url:
            print(f"📹 上傳影片: {video_path}")
            video_url = self.upload_file(video_path)
            if not video_url:
                print(f"❌ 影片上傳失敗")
                return None
        
        if audio_path and not audio_url:
            print(f"🎵 上傳音訊: {audio_path}")
            audio_url = self.upload_file(audio_path)
            if not audio_url:
                print(f"❌ 音訊上傳失敗")
                return None
        
        # Validate inputs
        if not video_url or not audio_url:
            print(f"❌ 需要同時提供影片和音訊 URL")
            return None
        
        print(f"📹 影片 URL: {video_url}")
        print(f"🎵 音訊 URL: {audio_url}")
        print(f"⚙️  同步模式: {sync_mode}")
        print(f"⚙️  溫度: {temperature}")
        print(f"⚙️  啟用發言者偵測: {active_speaker}")
        
        # Prepare inputs
        inputs = {
            "video": video_url,
            "audio": audio_url,
            "sync_mode": sync_mode,
            "temperature": temperature,
            "active_speaker": active_speaker
        }
        
        # Run the model
        result = self.run_model("lipsync-2-pro", inputs, output_filename)
        
        # Return first result if it's a list
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return result

