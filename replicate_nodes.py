"""
Replicate ComfyUI 節點整合
支援 Lipsync、通用模型、動態參數等功能
"""

import os
import shutil
import torch
import numpy as np
import cv2
from .replicate_api import SyncAPI, ReplicateAPI
from .replicate_utils import VideoUtils, AudioUtils, ImageUtils, cleanup_temp_file

# 嘗試載入 model_configs
try:
    from .model_configs import REPLICATE_MODELS, get_model_config, get_model_names, get_model_names_by_group
    HAS_MODEL_CONFIGS = True
except ImportError:
    HAS_MODEL_CONFIGS = False
    def get_model_names():
        return ["lipsync-2-pro"]
    def get_model_names_by_group(group):  # noqa: unused parameter for fallback
        return []

# Try to import ComfyUI's folder_paths
try:
    import folder_paths
except ImportError:
    class FolderPaths:
        @staticmethod
        def get_output_directory():
            return os.path.join(os.getcwd(), "output")
    folder_paths = FolderPaths()


class VideoWrapper:
    """影片包裝類別，相容於 Save Video 節點"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self._width = None
        self._height = None
        self._fps = None
        self._frame_count = None
        
        # Load video properties
        if os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                self._width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self._height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self._fps = cap.get(cv2.CAP_PROP_FPS)
                self._frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
    
    def get_dimensions(self):
        """回傳影片尺寸 (width, height)"""
        return (self._width or 1280, self._height or 720)
    
    def get_fps(self):
        """回傳影片幀率"""
        return self._fps or 30.0
    
    def get_frame_count(self):
        """回傳總幀數"""
        return self._frame_count or 0
    
    def get_path(self):
        """回傳影片檔案路徑"""
        return self.video_path
    
    def save_to(self, output_path, **kwargs):
        """儲存影片到指定路徑 (Save Video 節點需要)"""
        try:
            if os.path.exists(self.video_path):
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                format_type = kwargs.get('format', None)
                if format_type:
                    print(f"📁 儲存影片格式: {format_type}")
                shutil.copy2(self.video_path, output_path)
                print(f"✅ 影片已儲存至: {output_path}")
                return output_path
            else:
                print(f"❌ 來源影片不存在: {self.video_path}")
                return None
        except Exception as e:
            print(f"❌ 儲存影片時發生錯誤: {e}")
            return None
        
    def __str__(self):
        return self.video_path


# ======================
# 基礎 Lipsync 節點
# ======================

class SyncLipsyncNode:
    """
    ComfyUI 節點：使用 Replicate 的 sync/lipsync-2-pro 模型生成嘴唇同步影片
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("IMAGE",),
                "audio": ("AUDIO",),
            },
            "optional": {
                "output_filename": ("STRING", {"default": "lipsync_output"}),
                "sync_mode": (["loop", "trim"], {"default": "loop"}),
                "temperature": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1}),
                "active_speaker": ("BOOLEAN", {"default": False}),
            },
        }
    
    RETURN_TYPES = ("SYNC_VIDEO", "SYNC_AUDIO")
    RETURN_NAMES = ("video_paths", "audio_paths")
    FUNCTION = "generate_lipsync"
    CATEGORY = "video/lipsync"
    
    def generate_lipsync(self, video, audio, output_filename="lipsync_output", 
                        sync_mode="loop", temperature=0.5, active_speaker=False):
        """生成嘴唇同步影片"""
        print("=" * 60)
        print("🎬 Replicate Lipsync 生成 (sync/lipsync-2-pro)")
        print("=" * 60)
        
        temp_files = []
        
        try:
            api = SyncAPI()
            
            print("🎞️ 處理影片輸入...")
            fps = 24
            final_video_path = VideoUtils.save_image_sequence_to_video(video, fps=fps)
            if final_video_path:
                temp_files.append(final_video_path)
            else:
                print("❌ 處理影片輸入失敗！")
                return ([], [])
            
            print("🎵 處理音訊輸入...")
            final_audio_path = AudioUtils.save_audio_from_comfyui(audio)
            if final_audio_path:
                temp_files.append(final_audio_path)
            else:
                print("❌ 處理音訊輸入失敗！")
                return ([], [])
            
            print("=" * 60)
            print("📤 上傳檔案到 Replicate...")
            print("=" * 60)
            
            result_video_path = api.generate_lipsync(
                video_path=final_video_path,
                audio_path=final_audio_path,
                output_filename=output_filename,
                model="lipsync-2-pro",
                sync_mode=sync_mode,
                temperature=temperature,
                active_speaker=active_speaker
            )
            
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            
            if result_video_path and os.path.exists(result_video_path):
                print("=" * 60)
                print("✅ Lipsync 生成完成！")
                print(f"📁 輸出: {result_video_path}")
                print("=" * 60)
                
                video_paths = [result_video_path]
                audio_paths = [final_audio_path] if final_audio_path and os.path.exists(final_audio_path) else []
                
                return (video_paths, audio_paths)
            else:
                print("=" * 60)
                print("❌ Lipsync 生成失敗！")
                print("=" * 60)
                return ([], [])
                
        except ValueError as e:
            print(f"❌ API 初始化失敗: {str(e)}")
            print("\n請確保：")
            print("1. 在 .env 檔案中設定 REPLICATE_API_TOKEN")
            print("2. 從以下網址取得 API token: https://replicate.com/account/api-tokens")
            
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            
            return ([], [])
        except Exception as e:
            print(f"❌ 生成時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            
            return ([], [])


class SyncVideoOutput:
    """
    輸出節點：將 Sync lipsync 結果轉換為 VIDEO 格式
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("SYNC_VIDEO",),
            },
            "optional": {
                "audio_paths": ("SYNC_AUDIO",),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "output_video"
    CATEGORY = "video/lipsync"
    
    def output_video(self, video_paths, audio_paths=None):
        if not video_paths:
            print("⚠️ 警告：沒有生成影片。")
            return (None,)
        
        video_path = video_paths[0] if isinstance(video_paths, list) else video_paths
        
        if not os.path.exists(video_path):
            print(f"⚠️ 警告：找不到影片檔案: {video_path}")
            return (None,)
        
        print(f"✅ 影片檔案就緒: {video_path}")
        
        if audio_paths and len(audio_paths) > 0:
            try:
                audio_path = audio_paths[0]
                if os.path.exists(audio_path):
                    print(f"✅ 音訊檔案可用: {audio_path}")
                else:
                    print(f"⚠️ 找不到音訊檔案: {audio_path}")
            except Exception as e:
                print(f"⚠️ 處理音訊失敗: {e}")
        
        video_wrapper = VideoWrapper(video_path)
        print(f"✅ 已建立影片包裝器: {video_wrapper.get_dimensions()}")
        
        return (video_wrapper,)


# ======================
# 通用模型節點
# ======================

class ReplicateDynamicNode:
    """
    動態節點：根據選擇的模型只處理相關參數
    支援 Sora、Veo 等所有 Replicate 模型
    
    注意：ComfyUI 的限制使得無法真正隱藏參數，
    但節點會自動忽略當前模型不需要的參數。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        model_list = get_model_names() if HAS_MODEL_CONFIGS else ["lipsync-2-pro"]
        
        return {
            "required": {
                "model": (model_list, {
                    "default": "sora-2" if "sora-2" in model_list else model_list[0],
                    "tooltip": "選擇模型 / Select Model - 節點將自動使用該模型需要的參數 / Node will automatically use parameters required by this model"
                }),
            },
            "optional": {
                # === 文字輸入 / Text Inputs ===
                "prompt": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "tooltip": "提示詞 / Prompt - 用於 Sora, Veo, MiniMax 等 / Used for Sora, Veo, MiniMax, etc."
                }),
                
                # === 圖片輸入 / Image Inputs ===
                "image": ("IMAGE", {
                    "tooltip": "輸入圖片 / Input Image - Veo, Wan, SVD 需要 / Required for Veo, Wan, SVD"
                }),
                "input_reference": ("IMAGE", {
                    "tooltip": "參考圖片 / Reference Image - Sora 2 使用 / Used for Sora 2"
                }),
                "first_frame_image": ("IMAGE", {
                    "tooltip": "首幀圖片 / First Frame - MiniMax 使用 / Used for MiniMax"
                }),
                "last_frame": ("IMAGE", {
                    "tooltip": "末幀圖片 / Last Frame - Veo 使用 / Used for Veo"
                }),
                "start_image": ("IMAGE", {
                    "tooltip": "起始幀圖片 / Start Image - Kling 使用 / Used for Kling"
                }),
                
                # === 影片/音訊輸入 / Video/Audio Inputs ===
                "video": ("VIDEO", {
                    "tooltip": "輸入影片 / Input Video - Lipsync 使用 / Used for Lipsync"
                }),
                "audio": ("AUDIO", {
                    "tooltip": "輸入音訊 / Input Audio - Lipsync, MusicGen 使用 / Used for Lipsync, MusicGen"
                }),
                
                # === Sora/Veo 參數 / Sora/Veo Parameters ===
                "aspect_ratio": (["portrait", "landscape", "square", "1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"], {
                    "default": "landscape",
                    "tooltip": "長寬比 / Aspect Ratio - Sora, FLUX 使用 / Used for Sora, FLUX"
                }),
                "resolution": (["480p", "720p", "1080p"], {
                    "default": "720p",
                    "tooltip": "解析度 / Resolution - Veo 使用 / Used for Veo"
                }),
                "quality": (["480p", "720p", "1080p"], {
                    "default": "1080p",
                    "tooltip": "影片品質 / Video Quality - PixVerse 使用 / Used for PixVerse"
                }),
                
                # === Lipsync 參數 / Lipsync Parameters ===
                "sync_mode": (["loop", "trim"], {
                    "default": "loop",
                    "tooltip": "同步模式 / Sync Mode - Lipsync 使用 / Used for Lipsync"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 2.0, "step": 0.1,
                    "tooltip": "溫度 / Temperature - Lipsync, LLM 使用 / Used for Lipsync, LLM"
                }),
                "active_speaker": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "啟用發言者偵測 / Active Speaker Detection - Lipsync 使用 / Used for Lipsync"
                }),
                
                # === 圖片生成參數 / Image Generation Parameters ===
                "guidance": ("FLOAT", {
                    "default": 3.5, "min": 1.5, "max": 5.0, "step": 0.1,
                    "tooltip": "引導強度 / Guidance - FLUX 使用 / Used for FLUX"
                }),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5, "min": 1.0, "max": 20.0, "step": 0.5,
                    "tooltip": "引導比例 / Guidance Scale - Wan, SVD 使用 / Used for Wan, SVD"
                }),
                "output_format": (["webp", "jpg", "png"], {
                    "default": "webp",
                    "tooltip": "輸出格式 / Output Format - 圖片生成使用 / Used for image generation"
                }),
                "output_quality": ("INT", {
                    "default": 80, "min": 0, "max": 100, "step": 1,
                    "tooltip": "輸出品質 / Output Quality - 圖片生成使用 / Used for image generation"
                }),
                
                # === 影片生成參數 / Video Generation Parameters ===
                "num_inference_steps": ("INT", {
                    "default": 50, "min": 1, "max": 100, "step": 1,
                    "tooltip": "推理步數 / Inference Steps - 影片生成使用 / Used for video generation"
                }),
                "num_frames": ("INT", {
                    "default": 81, "min": 1, "max": 200, "step": 1,
                    "tooltip": "幀數 / Frame Count - Wan, SVD 使用 / Used for Wan, SVD"
                }),
                "fps": ("INT", {
                    "default": 6, "min": 1, "max": 30, "step": 1,
                    "tooltip": "每秒幀數 / FPS - SVD 使用 / Used for SVD"
                }),
                "duration": ("INT", {
                    "default": 8, "min": 1, "max": 30, "step": 1,
                    "tooltip": "時長(秒) / Duration (seconds) - 影片生成使用 / Used for video generation"
                }),
                
                # === 進階參數 / Advanced Parameters ===
                "prompt_optimizer": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "提示詞優化 / Prompt Optimizer - MiniMax 使用 / Used for MiniMax"
                }),
                "face_enhance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "臉部增強 / Face Enhancement - Real-ESRGAN 使用 / Used for Real-ESRGAN"
                }),
                "scale": ("INT", {
                    "default": 2, "min": 1, "max": 4, "step": 1,
                    "tooltip": "放大倍數 / Upscale Factor - Real-ESRGAN 使用 / Used for Real-ESRGAN"
                }),
                "motion_bucket_id": ("INT", {
                    "default": 127, "min": 1, "max": 255, "step": 1,
                    "tooltip": "運動強度 / Motion Bucket - SVD 使用 / Used for SVD"
                }),
                "seed": ("INT", {
                    "default": -1, "min": -1, "max": 2147483647, "step": 1,
                    "tooltip": "種子值 / Seed - Seedance 等使用 / Used for Seedance etc. (-1 = random)"
                }),
                "camera_motion": (["none", "dolly_in", "dolly_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "roll_cw", "roll_ccw"], {
                    "default": "none",
                    "tooltip": "鏡頭運動 / Camera Motion - LTX-2.3 使用 / Used for LTX-2.3"
                }),
            },
        }
    
    RETURN_TYPES = ("REPLICATE_VIDEO", "REPLICATE_AUDIO", "IMAGE", "STRING")
    RETURN_NAMES = ("video_paths", "audio_paths", "image", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate/dynamic"
    
    def run_model(self, model, prompt="", image=None, input_reference=None, first_frame_image=None,
                 last_frame=None, start_image=None, video=None, audio=None, **kwargs):
        """
        執行選擇的 Replicate 模型 / Run selected Replicate model
        自動過濾並只使用該模型需要的參數 / Automatically filters and uses only required parameters
        """
        result = _run_replicate_model(
            model, prompt=prompt, image=image, input_reference=input_reference,
            first_frame_image=first_frame_image, last_frame=last_frame,
            start_image=start_image, video=video, audio=audio, **kwargs
        )
        return (result[0], result[1], result[2], result[3])


class ReplicateVideoOutput:
    """
    將 Replicate 影片輸出轉換為 VIDEO 格式
    相容於 Save Video 節點
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("REPLICATE_VIDEO",),
            },
            "optional": {
                "audio_paths": ("REPLICATE_AUDIO",),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "output_video"
    CATEGORY = "replicate/output"
    
    def output_video(self, video_paths, audio_paths=None):
        """將影片路徑轉換為 VIDEO 格式"""
        if not video_paths:
            print("⚠️ 警告：沒有生成影片。")
            return (None,)
        
        # 取得第一個影片路徑
        video_path = video_paths[0] if isinstance(video_paths, list) else video_paths
        
        if not os.path.exists(video_path):
            print(f"⚠️ 警告：找不到影片檔案: {video_path}")
            return (None,)
        
        print(f"✅ 影片檔案就緒: {video_path}")
        
        # 處理音訊資訊（如有提供）
        if audio_paths and len(audio_paths) > 0:
            try:
                audio_path = audio_paths[0]
                if os.path.exists(audio_path):
                    print(f"✅ 音訊檔案可用: {audio_path}")
                else:
                    print(f"⚠️ 找不到音訊檔案: {audio_path}")
            except Exception as e:
                print(f"⚠️ 處理音訊失敗: {e}")
        
        # 建立 VideoWrapper 物件供 Save Video 節點使用
        video_wrapper = VideoWrapper(video_path)
        print(f"✅ 已建立影片包裝器: {video_wrapper.get_dimensions()}")
        
        return (video_wrapper,)


class ReplicateAudioOutput:
    """
    輸出 Replicate 生成的音訊檔案
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_paths": ("REPLICATE_AUDIO",),
            },
        }
    
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "output_audio"
    CATEGORY = "replicate/output"
    
    def output_audio(self, audio_paths):
        """載入並輸出音訊檔案"""
        if not audio_paths:
            print("⚠️ 警告：沒有生成音訊。")
            return (None,)
        
        # 取得第一個音訊路徑
        audio_path = audio_paths[0] if isinstance(audio_paths, list) else audio_paths
        
        if not os.path.exists(audio_path):
            print(f"⚠️ 警告：找不到音訊檔案: {audio_path}")
            return (None,)
        
        try:
            import soundfile as sf
            waveform, sample_rate = sf.read(audio_path)
            
            waveform_tensor = torch.from_numpy(waveform).float()
            
            if len(waveform_tensor.shape) == 1:
                waveform_tensor = waveform_tensor.unsqueeze(0)
            elif len(waveform_tensor.shape) == 2:
                if waveform_tensor.shape[0] > waveform_tensor.shape[1]:
                    waveform_tensor = waveform_tensor.transpose(0, 1)
            
            audio_dict = {
                "waveform": waveform_tensor,
                "sample_rate": sample_rate
            }
            
            print(f"✅ 音訊已載入: {audio_path}")
            print(f"   取樣率: {sample_rate}Hz")
            print(f"   形狀: {waveform_tensor.shape}")
            
            return (audio_dict,)
            
        except Exception as e:
            print(f"❌ 載入音訊時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return (None,)


class ReplicateVideoAudioMerge:
    """
    合併影片和音訊為單一影片檔案
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("REPLICATE_VIDEO",),
                "audio_paths": ("REPLICATE_AUDIO",),
            },
            "optional": {
                "output_filename": ("STRING", {"default": "merged_video"}),
            }
        }
    
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "merge_video_audio"
    CATEGORY = "replicate/output"
    
    def merge_video_audio(self, video_paths, audio_paths, output_filename="merged_video"):
        """使用 ffmpeg 合併影片和音訊"""
        if not video_paths:
            print("❌ 沒有提供影片")
            return (None,)
        
        # 取得第一個影片和音訊路徑
        video_path = video_paths[0] if isinstance(video_paths, list) else video_paths
        
        if not os.path.exists(video_path):
            print(f"❌ 找不到影片檔案: {video_path}")
            return (None,)
        
        if not audio_paths or len(audio_paths) == 0:
            print("⚠️ 沒有提供音訊，回傳原始影片")
            return (VideoWrapper(video_path),)
        
        audio_path = audio_paths[0] if isinstance(audio_paths, list) else audio_paths
        
        if not os.path.exists(audio_path):
            print(f"⚠️ 找不到音訊檔案: {audio_path}，回傳原始影片")
            return (VideoWrapper(video_path),)
        
        try:
            import subprocess
            
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            import time
            timestamp = int(time.time())
            output_path = os.path.join(output_dir, f"{output_filename}_{timestamp}.mp4")
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-shortest',
                '-y',
                output_path
            ]
            
            print(f"🔄 合併影片和音訊...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"✅ 已儲存合併影片: {output_path}")
                return (VideoWrapper(output_path),)
            else:
                print(f"❌ FFmpeg 合併失敗: {result.stderr}")
                print("⚠️ 回傳原始影片")
                return (VideoWrapper(video_path),)
                
        except Exception as e:
            print(f"❌ 合併影片和音訊時發生錯誤: {e}")
            print("⚠️ 回傳原始影片")
            return (VideoWrapper(video_path),)


# ======================
# 簡化節點（可選）
# ======================

class ReplicateTextToVideoNode:
    """文字生成影片"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "model": (["minimax-video-01", "minimax-video-01-live"], {"default": "minimax-video-01"}),
            },
            "optional": {
                "first_frame_image": ("IMAGE",),
                "prompt_optimizer": ("BOOLEAN", {"default": True}),
                "output_filename": ("STRING", {"default": "text_to_video"}),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate_video"
    CATEGORY = "replicate/video"
    
    def generate_video(self, prompt, model="minimax-video-01", first_frame_image=None, 
                      prompt_optimizer=True, output_filename="text_to_video"):
        """從文字生成影片"""
        print("=" * 60)
        print(f"🎬 文字生成影片: {model}")
        print("=" * 60)
        
        temp_files = []
        
        try:
            api = ReplicateAPI()
            
            inputs = {
                "prompt": prompt,
                "prompt_optimizer": prompt_optimizer,
            }
            
            if first_frame_image is not None:
                image_path = ImageUtils.save_image_tensor(first_frame_image)
                if image_path:
                    temp_files.append(image_path)
                    image_url = api.upload_file(image_path)
                    if image_url:
                        inputs["first_frame_image"] = image_url
            
            result_path = api.run_model(model, inputs, output_filename)
            
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            
            if result_path:
                print(f"✅ 影片已生成: {result_path}")
                return (result_path,)
            else:
                return ("",)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            return ("",)


class ReplicateImageToVideoNode:
    """圖片生成影片"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "model": (["wan", "stable-video-diffusion"], {"default": "wan"}),
            },
            "optional": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "num_frames": ("INT", {"default": 81, "min": 1, "max": 200, "step": 1}),
                "guidance_scale": ("FLOAT", {"default": 7.5, "min": 1.0, "max": 20.0, "step": 0.5}),
                "num_inference_steps": ("INT", {"default": 50, "min": 10, "max": 100, "step": 1}),
                "motion_bucket_id": ("INT", {"default": 127, "min": 1, "max": 255, "step": 1}),
                "fps": ("INT", {"default": 6, "min": 1, "max": 30, "step": 1}),
                "output_filename": ("STRING", {"default": "image_to_video"}),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate_video"
    CATEGORY = "replicate/video"
    
    def generate_video(self, image, model="wan", prompt="", num_frames=81, 
                      guidance_scale=7.5, num_inference_steps=50, motion_bucket_id=127,
                      fps=6, output_filename="image_to_video"):
        """從圖片生成影片"""
        print("=" * 60)
        print(f"🎬 圖片生成影片: {model}")
        print("=" * 60)
        
        temp_files = []
        
        try:
            api = ReplicateAPI()
            
            image_path = ImageUtils.save_image_tensor(image)
            if not image_path:
                print("❌ 儲存圖片失敗")
                return ("",)
            
            temp_files.append(image_path)
            image_url = api.upload_file(image_path)
            if not image_url:
                print("❌ 上傳圖片失敗")
                return ("",)
            
            inputs = {"image": image_url}
            
            if model == "wan":
                inputs.update({
                    "prompt": prompt,
                    "num_frames": num_frames,
                    "guidance_scale": guidance_scale,
                    "num_inference_steps": num_inference_steps,
                })
            elif model == "stable-video-diffusion":
                inputs.update({
                    "motion_bucket_id": motion_bucket_id,
                    "fps": fps,
                })
            
            result_path = api.run_model(model, inputs, output_filename)
            
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            
            if result_path:
                print(f"✅ 影片已生成: {result_path}")
                return (result_path,)
            else:
                return ("",)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            for temp_file in temp_files:
                cleanup_temp_file(temp_file)
            return ("",)


class ReplicateImageGenNode:
    """圖片生成"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "model": (["flux-schnell", "flux-dev", "luma-photon", "luma-photon-flash"], 
                         {"default": "flux-schnell"}),
            },
            "optional": {
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"], 
                               {"default": "1:1"}),
                "guidance": ("FLOAT", {"default": 3.5, "min": 1.5, "max": 5.0, "step": 0.1}),
                "num_inference_steps": ("INT", {"default": 28, "min": 1, "max": 50, "step": 1}),
                "output_format": (["webp", "jpg", "png"], {"default": "webp"}),
                "output_quality": ("INT", {"default": 80, "min": 0, "max": 100, "step": 1}),
                "output_filename": ("STRING", {"default": "generated_image"}),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate_image"
    CATEGORY = "replicate/image"
    
    def generate_image(self, prompt, model="flux-schnell", aspect_ratio="1:1",
                      guidance=3.5, num_inference_steps=28, output_format="webp",
                      output_quality=80, output_filename="generated_image"):
        """從文字生成圖片"""
        print("=" * 60)
        print(f"🖼️ 圖片生成: {model}")
        print("=" * 60)
        
        try:
            api = ReplicateAPI()
            
            inputs = {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "output_format": output_format,
                "output_quality": output_quality,
            }
            
            if model == "flux-dev":
                inputs.update({
                    "guidance": guidance,
                    "num_inference_steps": num_inference_steps,
                })
            
            result_path = api.run_model(model, inputs, output_filename)
            
            if result_path and os.path.exists(result_path):
                image = cv2.imread(result_path)
                if image is not None:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    image_tensor = torch.from_numpy(image_rgb).float() / 255.0
                    image_tensor = image_tensor.unsqueeze(0)
                    print(f"✅ 圖片已載入: {image_tensor.shape}")
                    return (image_tensor,)
            
            print("❌ 生成圖片失敗")
            return (torch.zeros((1, 512, 512, 3)),)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            return (torch.zeros((1, 512, 512, 3)),)


class ReplicateModelInfo:
    """
    顯示執行資訊節點
    Shows execution information
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "execution_info": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "multiline": True,
                }),
            },
        }
    
    RETURN_TYPES = ()
    FUNCTION = "display_info"
    CATEGORY = "replicate/info"
    OUTPUT_NODE = True
    
    def display_info(self, execution_info=""):
        """顯示執行資訊"""
        if execution_info and execution_info.strip():
            print("\n" + "=" * 70)
            print("📊 執行資訊 / Execution Information")
            print("=" * 70)
            print(execution_info)
            print("=" * 70 + "\n")
        else:
            print("ℹ️  等待執行資訊... / Waiting for execution info...")
        
        return {}


# ======================
# 共用執行邏輯 / Shared Execution Logic
# ======================

def _extract_video_path(video_input):
    """從影片輸入提取檔案路徑"""
    if isinstance(video_input, str):
        return video_input
    elif hasattr(video_input, 'video_path'):
        return video_input.video_path
    elif hasattr(video_input, 'filename'):
        return video_input.filename
    elif isinstance(video_input, dict):
        return video_input.get('video') or video_input.get('filename') or video_input.get('path')
    return None


def _run_replicate_model(model_id, prompt="", image=None, input_reference=None,
                          first_frame_image=None, last_frame=None, start_image=None,
                          video=None, audio=None, **kwargs):
    """
    共用的 Replicate 模型執行邏輯
    Returns: (video_paths, audio_paths, first_frame_tensor, info_text, file_path)
    """
    config = get_model_config(model_id) if HAS_MODEL_CONFIGS else None
    if not config:
        info = f"❌ 未知模型: {model_id}"
        print(info)
        return ([], [], torch.zeros((1, 512, 512, 3)), info, "")
    
    print("=" * 60)
    print(f"🤖 Replicate: {config['display_name']}")
    print(f"📋 模型ID: {model_id}")
    print("=" * 60)
    
    output_filename = model_id.replace(".", "_").replace("/", "_")
    temp_files = []
    
    try:
        api = ReplicateAPI()
        inputs = {}
        model_inputs = config.get("inputs", {})
        
        # 圖片參數對照表
        image_map = {
            'image': image,
            'input_reference': input_reference,
            'first_frame_image': first_frame_image,
            'last_frame': last_frame,
            'start_image': start_image,
        }
        
        for input_name, input_config in model_inputs.items():
            input_type = input_config.get("type")
            is_required = input_config.get("required", False)
            
            if input_type == "STRING" and input_name == "prompt":
                if prompt or is_required:
                    inputs[input_name] = prompt
                    
            elif input_type == "IMAGE":
                image_param = None
                if input_name in image_map:
                    image_param = image_map[input_name]
                elif input_name in kwargs:
                    image_param = kwargs[input_name]
                
                if image_param is not None:
                    image_path = ImageUtils.save_image_tensor(image_param)
                    if image_path:
                        temp_files.append(image_path)
                        image_url = api.upload_file(image_path)
                        if image_url:
                            inputs[input_name] = image_url
                elif is_required:
                    print(f"⚠️ 必要圖片參數 '{input_name}' 未提供")
                    
            elif input_type == "VIDEO":
                if video is not None:
                    video_path = _extract_video_path(video)
                    if video_path and os.path.exists(video_path):
                        video_url = api.upload_file(video_path)
                        if video_url:
                            inputs[input_name] = video_url
                            
            elif input_type == "AUDIO":
                if audio is not None:
                    audio_path = AudioUtils.save_audio_from_comfyui(audio)
                    if audio_path:
                        temp_files.append(audio_path)
                        audio_url = api.upload_file(audio_path)
                        if audio_url:
                            inputs[input_name] = audio_url
                            
            elif input_type in ["COMBO", "FLOAT", "INT", "BOOLEAN"]:
                if input_name in kwargs and kwargs[input_name] is not None:
                    inputs[input_name] = kwargs[input_name]
                elif is_required and "default" in input_config:
                    inputs[input_name] = input_config["default"]
        
        print(f"📤 執行模型...")
        print(f"📝 參數: {list(inputs.keys())}")
        
        result = api.run_model(model_id, inputs, output_filename)
        
        for temp_file in temp_files:
            cleanup_temp_file(temp_file)
        
        # 處理結果
        video_path = ""
        audio_path = ""
        file_path = ""
        
        if isinstance(result, dict):
            # JSON output (e.g., voice-cloning)
            import json
            info_text = f"✅ 執行成功\n🤖 {config['display_name']}\n📋 結果:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
            return ([], [], torch.zeros((1, 512, 512, 3)), info_text, "")
        elif isinstance(result, list) and len(result) >= 2:
            video_path = result[0] if result[0] else ""
            audio_path = result[1] if result[1] else ""
        elif isinstance(result, str):
            if result.endswith(('.glb', '.obj', '.fbx', '.gltf')):
                file_path = result
            else:
                video_path = result
                if config.get("has_audio"):
                    audio_path = result.replace(".mp4", "_audio.wav")
                    if not os.path.exists(audio_path):
                        audio_path = ""
        
        # 提取第一幀
        first_frame = torch.zeros((1, 512, 512, 3))
        if video_path and os.path.exists(video_path):
            try:
                cap = cv2.VideoCapture(video_path)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    first_frame = torch.from_numpy(frame_rgb).float() / 255.0
                    first_frame = first_frame.unsqueeze(0)
            except Exception:
                pass
        
        # 載入圖片結果
        if not video_path and not file_path and result and isinstance(result, str) and os.path.exists(result):
            try:
                img = cv2.imread(result)
                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    first_frame = torch.from_numpy(img_rgb).float() / 255.0
                    first_frame = first_frame.unsqueeze(0)
                    file_path = result
            except Exception:
                pass
        
        # 建立資訊
        info_lines = [f"✅ 執行成功", f"🤖 {config['display_name']}"]
        info_lines.append(f"📝 參數: {', '.join(inputs.keys())}")
        if video_path:
            info_lines.append(f"📁 影片: {video_path}")
        if audio_path:
            info_lines.append(f"🎵 音訊: {audio_path}")
        if file_path:
            info_lines.append(f"📁 檔案: {file_path}")
        info_text = "\n".join(info_lines)
        
        video_paths = [video_path] if video_path and os.path.exists(video_path) else []
        audio_paths = [audio_path] if audio_path and os.path.exists(audio_path) else []
        
        return (video_paths, audio_paths, first_frame, info_text, file_path if file_path else (video_path or ""))
    
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        for temp_file in temp_files:
            cleanup_temp_file(temp_file)
        return ([], [], torch.zeros((1, 512, 512, 3)), f"❌ 錯誤: {str(e)}", "")


# ======================
# 分類節點 / Category Nodes
# ======================

class ReplicateVideoNode:
    """🎬 影片生成節點 - 支援所有影片生成模型"""
    
    @classmethod
    def INPUT_TYPES(cls):
        models = get_model_names_by_group("video") if HAS_MODEL_CONFIGS else []
        return {
            "required": {
                "model": (models, {
                    "default": models[0] if models else "",
                    "tooltip": "選擇影片生成模型 / Select video generation model"
                }),
            },
            "optional": {
                "prompt": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "提示詞 / Prompt"}),
                "image": ("IMAGE", {
                    "tooltip": "輸入圖片 / Input Image (Veo, Wan, LTX, P-Video)"}),
                "input_reference": ("IMAGE", {
                    "tooltip": "參考圖片 / Reference Image (Sora 2)"}),
                "first_frame_image": ("IMAGE", {
                    "tooltip": "首幀圖片 / First Frame (MiniMax, Hailuo)"}),
                "last_frame": ("IMAGE", {
                    "tooltip": "末幀圖片 / Last Frame (Veo)"}),
                "start_image": ("IMAGE", {
                    "tooltip": "起始圖片 / Start Image (Kling)"}),
                "aspect_ratio": (["portrait", "landscape", "square", "1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"], {
                    "default": "landscape",
                    "tooltip": "長寬比 / Aspect Ratio (Sora)"}),
                "resolution": (["480p", "720p", "1080p"], {
                    "default": "720p",
                    "tooltip": "解析度 / Resolution (Veo)"}),
                "quality": (["480p", "720p", "1080p"], {
                    "default": "1080p",
                    "tooltip": "品質 / Quality (PixVerse)"}),
                "duration": ("INT", {
                    "default": 8, "min": 1, "max": 30, "step": 1,
                    "tooltip": "時長秒 / Duration (PixVerse, Hailuo, Seedance)"}),
                "num_frames": ("INT", {
                    "default": 81, "min": 1, "max": 200, "step": 1,
                    "tooltip": "幀數 / Frames (Wan)"}),
                "num_inference_steps": ("INT", {
                    "default": 50, "min": 1, "max": 100, "step": 1,
                    "tooltip": "推理步數 / Steps (Wan)"}),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5, "min": 1.0, "max": 20.0, "step": 0.5,
                    "tooltip": "引導比例 / Guidance Scale (Wan)"}),
                "fps": ("INT", {
                    "default": 6, "min": 1, "max": 30, "step": 1,
                    "tooltip": "FPS (SVD)"}),
                "motion_bucket_id": ("INT", {
                    "default": 127, "min": 1, "max": 255, "step": 1,
                    "tooltip": "運動強度 / Motion Bucket (SVD)"}),
                "seed": ("INT", {
                    "default": -1, "min": -1, "max": 2147483647, "step": 1,
                    "tooltip": "種子 / Seed (-1=random)"}),
                "camera_motion": (["none", "dolly_in", "dolly_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "roll_cw", "roll_ccw"], {
                    "default": "none",
                    "tooltip": "鏡頭運動 / Camera Motion (LTX-2.3)"}),
                "prompt_optimizer": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "提示詞優化 / Prompt Optimizer (MiniMax)"}),
                "prompt_upsampling": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "提示詞增強 / Prompt Upsampling (P-Video)"}),
            },
        }
    
    RETURN_TYPES = ("REPLICATE_VIDEO", "REPLICATE_AUDIO", "IMAGE", "STRING")
    RETURN_NAMES = ("video_paths", "audio_paths", "image", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate/video"
    
    def run_model(self, model, **kwargs):
        result = _run_replicate_model(model, **kwargs)
        return (result[0], result[1], result[2], result[3])


class ReplicateEnhanceNode:
    """🎭 影片增強節點 - 唇語同步、影片放大等"""
    
    @classmethod
    def INPUT_TYPES(cls):
        models = get_model_names_by_group("enhancement") if HAS_MODEL_CONFIGS else []
        return {
            "required": {
                "model": (models, {
                    "default": models[0] if models else "",
                    "tooltip": "選擇影片增強模型 / Select enhancement model"
                }),
            },
            "optional": {
                "video": ("VIDEO", {
                    "tooltip": "輸入影片 / Input Video"}),
                "audio": ("AUDIO", {
                    "tooltip": "輸入音訊 / Input Audio (Lipsync, Retalking)"}),
                "face": ("IMAGE", {
                    "tooltip": "人臉圖片 / Face Image (Retalking)"}),
                "sync_mode": (["loop", "bounce", "cut_off", "silence", "remap"], {
                    "default": "loop",
                    "tooltip": "同步模式 / Sync Mode (Lipsync)"}),
                "temperature": ("FLOAT", {
                    "default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1,
                    "tooltip": "溫度 / Temperature (Lipsync)"}),
                "active_speaker": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "發言者偵測 / Active Speaker (Lipsync)"}),
                "scale": ("INT", {
                    "default": 2, "min": 1, "max": 4, "step": 1,
                    "tooltip": "放大倍數 / Scale (ESRGAN)"}),
                "face_enhance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "臉部增強 / Face Enhance (ESRGAN)"}),
            },
        }
    
    RETURN_TYPES = ("REPLICATE_VIDEO", "REPLICATE_AUDIO", "IMAGE", "STRING")
    RETURN_NAMES = ("video_paths", "audio_paths", "image", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate/enhancement"
    
    def run_model(self, model, **kwargs):
        result = _run_replicate_model(model, **kwargs)
        return (result[0], result[1], result[2], result[3])


class ReplicateAudioGenNode:
    """🎵 音訊生成節點 - 音樂生成、音效、聲音克隆"""
    
    @classmethod
    def INPUT_TYPES(cls):
        models = get_model_names_by_group("audio") if HAS_MODEL_CONFIGS else []
        return {
            "required": {
                "model": (models, {
                    "default": models[0] if models else "",
                    "tooltip": "選擇音訊模型 / Select audio model"
                }),
            },
            "optional": {
                "prompt": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "提示詞 / Prompt (MusicGen)"}),
                "audio": ("AUDIO", {
                    "tooltip": "輸入音訊 / Input Audio (Voice Cloning voice_file)"}),
                "video": ("VIDEO", {
                    "tooltip": "輸入影片 / Input Video (Video to SFX)"}),
                "duration": ("INT", {
                    "default": 8, "min": 1, "max": 30, "step": 1,
                    "tooltip": "時長秒 / Duration (MusicGen)"}),
                "model_version": (["stereo-large", "large", "medium", "small"], {
                    "default": "stereo-large",
                    "tooltip": "模型版本 / Model Version (MusicGen)"}),
                "temperature": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1,
                    "tooltip": "溫度 / Temperature (MusicGen)"}),
                "num_samples": ("INT", {
                    "default": 4, "min": 1, "max": 10, "step": 1,
                    "tooltip": "樣本數 / Samples (Video to SFX)"}),
            },
        }
    
    RETURN_TYPES = ("REPLICATE_AUDIO", "STRING")
    RETURN_NAMES = ("audio_paths", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate/audio"
    
    def run_model(self, model, **kwargs):
        result = _run_replicate_model(model, **kwargs)
        return (result[1], result[3])


class ReplicateImageNode:
    """🎨 圖片生成節點 - FLUX、Luma Photon 等"""
    
    @classmethod
    def INPUT_TYPES(cls):
        models = get_model_names_by_group("image") if HAS_MODEL_CONFIGS else []
        return {
            "required": {
                "model": (models, {
                    "default": models[0] if models else "",
                    "tooltip": "選擇圖片生成模型 / Select image generation model"
                }),
            },
            "optional": {
                "prompt": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "提示詞 / Prompt"}),
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"], {
                    "default": "1:1",
                    "tooltip": "長寬比 / Aspect Ratio"}),
                "guidance": ("FLOAT", {
                    "default": 3.5, "min": 1.5, "max": 5.0, "step": 0.1,
                    "tooltip": "引導強度 / Guidance (FLUX Dev)"}),
                "num_inference_steps": ("INT", {
                    "default": 28, "min": 1, "max": 50, "step": 1,
                    "tooltip": "推理步數 / Steps (FLUX Dev)"}),
                "output_format": (["webp", "jpg", "png"], {
                    "default": "webp",
                    "tooltip": "輸出格式 / Output Format"}),
                "output_quality": ("INT", {
                    "default": 80, "min": 0, "max": 100, "step": 1,
                    "tooltip": "輸出品質 / Output Quality"}),
            },
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate/image"
    
    def run_model(self, model, **kwargs):
        result = _run_replicate_model(model, **kwargs)
        return (result[2], result[3])


class Replicate3DNode:
    """🧊 3D 模型生成節點"""
    
    @classmethod
    def INPUT_TYPES(cls):
        models = get_model_names_by_group("3d") if HAS_MODEL_CONFIGS else []
        return {
            "required": {
                "model": (models, {
                    "default": models[0] if models else "",
                    "tooltip": "選擇 3D 生成模型 / Select 3D generation model"
                }),
            },
            "optional": {
                "prompt": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "提示詞 / Prompt"}),
            },
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("file_path", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate/3d"
    
    def run_model(self, model, **kwargs):
        result = _run_replicate_model(model, **kwargs)
        return (result[4], result[3])


# ======================
# 節點註冊
# ======================

NODE_CLASS_MAPPINGS = {
    # Lipsync 節點
    "SyncLipsyncNode": SyncLipsyncNode,
    "SyncVideoOutput": SyncVideoOutput,
    
    # 動態節點 (向後相容)
    "ReplicateDynamicNode": ReplicateDynamicNode,
    
    # 分類節點 / Category Nodes
    "ReplicateVideoNode": ReplicateVideoNode,
    "ReplicateEnhanceNode": ReplicateEnhanceNode,
    "ReplicateAudioGenNode": ReplicateAudioGenNode,
    "ReplicateImageNode": ReplicateImageNode,
    "Replicate3DNode": Replicate3DNode,
    
    # 資訊節點
    "ReplicateModelInfo": ReplicateModelInfo,
    
    # 輸出節點
    "ReplicateVideoOutput": ReplicateVideoOutput,
    "ReplicateAudioOutput": ReplicateAudioOutput,
    "ReplicateVideoAudioMerge": ReplicateVideoAudioMerge,
    
    # 專門化節點 (舊版)
    "ReplicateTextToVideoNode": ReplicateTextToVideoNode,
    "ReplicateImageToVideoNode": ReplicateImageToVideoNode,
    "ReplicateImageGenNode": ReplicateImageGenNode,
}

# 雙語顯示名稱映射 / Bilingual Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    # Lipsync 節點 / Lipsync Nodes
    "SyncLipsyncNode": "🎭 Sync Lipsync 生成 / Generate",
    "SyncVideoOutput": "📹 Sync 影片輸出 / Video Output",
    
    # 動態節點 (向後相容)
    "ReplicateDynamicNode": "🎬 Replicate 動態 / Dynamic (All Models)",
    
    # 分類節點 / Category Nodes
    "ReplicateVideoNode": "🎬 影片生成 / Video Generation",
    "ReplicateEnhanceNode": "🎭 影片增強 / Video Enhancement",
    "ReplicateAudioGenNode": "🎵 音訊生成 / Audio Generation",
    "ReplicateImageNode": "🎨 圖片生成 / Image Generation",
    "Replicate3DNode": "🧊 3D 生成 / 3D Generation",
    
    # 資訊節點 / Info Node
    "ReplicateModelInfo": "📋 模型資訊 / Model Info",
    
    # 輸出節點 / Output Nodes
    "ReplicateVideoOutput": "📹 Replicate 影片 / Video Output",
    "ReplicateAudioOutput": "🎵 Replicate 音訊 / Audio Output",
    "ReplicateVideoAudioMerge": "🔄 合併影音 / Merge Video+Audio",
    
    # 專門化節點 (舊版) / Specialized Nodes (Legacy)
    "ReplicateTextToVideoNode": "🎬 文字轉影片 / Text to Video",
    "ReplicateImageToVideoNode": "🖼️ 圖片轉影片 / Image to Video",
    "ReplicateImageGenNode": "🎨 圖片生成(舊) / Image Gen (Legacy)",
}
