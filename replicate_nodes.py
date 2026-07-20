"""
Replicate ComfyUI 節點整合
支援 Lipsync、通用模型、動態參數等功能
"""

import os
import shutil
import torch
import numpy as np
import cv2
# 以頂層模組方式匯入時（例如 pytest 收集）改用絕對匯入
# 用 __package__ 判斷而非 try/except，避免掩蓋真正的相依套件缺失錯誤
if __package__:
    from .replicate_api import ReplicateAPI, get_download_directory
    from .replicate_utils import AudioUtils, ImageUtils, cleanup_temp_file
else:
    from replicate_api import ReplicateAPI, get_download_directory
    from replicate_utils import AudioUtils, ImageUtils, cleanup_temp_file

# 嘗試載入 model_configs
try:
    if __package__:
        from .model_configs import REPLICATE_MODELS, get_model_config, get_model_names, get_model_names_by_group
    else:
        from model_configs import REPLICATE_MODELS, get_model_config, get_model_names, get_model_names_by_group
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
        @staticmethod
        def get_input_directory():
            return os.path.join(os.getcwd(), "input")
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
                
                # === 圖片輸入（統一接口）/ Unified Image Input ===
                "images": ("IMAGE,REPLICATE_IMAGE_LIST", {
                    "tooltip": "圖片輸入（統一）/ Images (unified) - 接單張圖、batch 或多圖輸入節點；後端自動分配到模型對應參數（Veo/Wan=輸入圖、Sora=參考圖、MiniMax=首幀、Kling=起始圖、Nano Banana/Seedance=多張參考圖）/ Automatically routed to the model's image parameter(s)."
                }),
                "last_frame": ("IMAGE", {
                    "tooltip": "末幀圖片 / Last Frame - Veo 使用，獨立輸入 / Used for Veo, dedicated input"
                }),

                # === 影片/音訊輸入 / Video/Audio Inputs ===
                "video": ("VIDEO", {
                    "tooltip": "輸入影片 / Input Video - Lipsync 使用 / Used for Lipsync"
                }),
                "audio": ("AUDIO", {
                    "tooltip": "輸入音訊 / Input Audio - Lipsync, MusicGen 使用 / Used for Lipsync, MusicGen"
                }),
                
                # === Sora/Veo 參數 / Sora/Veo Parameters ===
                "aspect_ratio": (["portrait", "landscape", "square", "auto", "match_input_image", "1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2", "4:5", "5:4", "21:9", "9:21"], {
                    "default": "landscape",
                    "tooltip": "長寬比 / Aspect Ratio - Sora, FLUX, Nano Banana, Grok 使用 / Used for Sora, FLUX, Nano Banana, Grok"
                }),
                "resolution": (["480p", "720p", "1080p", "1K", "2K", "4K"], {
                    "default": "720p",
                    "tooltip": "解析度 / Resolution - Veo, Nano Banana 使用 / Used for Veo, Nano Banana"
                }),
                "quality": (["480p", "720p", "1080p"], {
                    "default": "1080p",
                    "tooltip": "影片品質 / Video Quality - PixVerse 使用 / Used for PixVerse"
                }),
                
                # === Lipsync 參數 / Lipsync Parameters ===
                "sync_mode": (["loop", "trim", "bounce", "cut_off", "silence", "remap"], {
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
                "image_search": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Google 圖片搜尋參考 / Image Search grounding - Nano Banana 2 使用"
                }),
                "google_search": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Google 網頁搜尋 / Web Search grounding - Nano Banana 2 使用"
                }),
                "alpha_ceil": ("INT", {
                    "default": 250, "min": 0, "max": 255, "step": 1,
                    "tooltip": "透明度上限 / Alpha Ceil - Nano Banana Transparent 使用"
                }),
                "alpha_floor": ("INT", {
                    "default": 6, "min": 0, "max": 255, "step": 1,
                    "tooltip": "透明度下限 / Alpha Floor - Nano Banana Transparent 使用"
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
                "prompt_upsampling": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "提示詞增強 / Prompt Upsampling - P-Video 使用"
                }),
                "model_version": (["stereo-large", "large", "medium", "small"], {
                    "default": "stereo-large",
                    "tooltip": "模型版本 / Model Version - MusicGen 使用"
                }),
                "num_samples": ("INT", {
                    "default": 4, "min": 1, "max": 10, "step": 1,
                    "tooltip": "樣本數 / Samples - Video to SFX 使用"
                }),
                "generate_audio": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "生成音訊 / Generate Audio - Seedance 2.0 使用 / Used for Seedance 2.0"
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
                    "default": -1, "min": -1, "max": 0xffffffffffffffff, "step": 1,
                    "tooltip": "種子值 / Seed - Seedance 等使用 / Used for Seedance etc. (-1 = random)"
                }),
                "camera_motion": (["none", "dolly_in", "dolly_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "roll_cw", "roll_ccw"], {
                    "default": "none",
                    "tooltip": "鏡頭運動 / Camera Motion - LTX-2.3 使用 / Used for LTX-2.3"
                }),
            },
        }
    
    RETURN_TYPES = ("VIDEO", "AUDIO", "IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("video", "audio", "image", "file_path", "info")
    FUNCTION = "run_model"
    CATEGORY = "replicate"
    INPUT_IS_LIST = True

    def run_model(self, model, **kwargs):
        """
        執行選擇的 Replicate 模型 / Run selected Replicate model
        自動過濾並只使用該模型需要的參數；結果直接輸出 VIDEO/AUDIO/IMAGE，
        可直接接 Save Video / Save Audio / Save Image（轉換與影音合併藏在後端）
        """
        kwargs = _unwrap_list_inputs(kwargs)
        model = model[0] if isinstance(model, list) else model
        result = _run_replicate_model(model, **kwargs)
        return (result[0], result[1], result[2], result[4], result[3])


# ======================
# 共用執行邏輯 / Shared Execution Logic
# ======================

def _flatten_image_items(value):
    """把統一圖片輸入攤平成單張張量清單（每項 [1,H,W,C]）
    支援：單張/批次 IMAGE 張量、REPLICATE_IMAGE_LIST（含巢狀清單）"""
    items = []
    if value is None:
        return items
    if isinstance(value, (list, tuple)):
        for v in value:
            items.extend(_flatten_image_items(v))
        return items
    if isinstance(value, torch.Tensor):
        tensor = value
        if tensor.dim() == 3:
            tensor = tensor.unsqueeze(0)
        for i in range(tensor.shape[0]):
            items.append(tensor[i:i+1])
    return items


def _unwrap_list_inputs(values, keep_whole=("images",)):
    """INPUT_IS_LIST 模式下 ComfyUI 會把每個輸入包成清單，
    這裡把單值參數還原，只有 keep_whole（多圖輸入）保留整份清單。
    如此其他套件的清單輸出（如 Muse 多圖節點）接進來時，
    節點只會執行一次並同時收到所有圖片，而不是逐張跑多次。"""
    out = {}
    for name, value in values.items():
        if name in keep_whole:
            out[name] = value
        elif isinstance(value, list):
            out[name] = value[0] if value else None
        else:
            out[name] = value
    return out


def _encode_image_data_uri(image_path):
    """把圖片檔編成 base64 data URI
    （部分模型後端無法讀取 Replicate 檔案 API 的授權 URL，需內嵌傳送）"""
    import base64
    ext = os.path.splitext(image_path)[1].lower().lstrip(".") or "png"
    if ext == "jpg":
        ext = "jpeg"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/{ext};base64,{encoded}"


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


def _load_audio_file(audio_path):
    """把音訊檔載入為 ComfyUI AUDIO dict（waveform [C,T] + sample_rate）"""
    try:
        import soundfile as sf
        waveform, sample_rate = sf.read(audio_path)
        waveform_tensor = torch.from_numpy(waveform).float()
        if len(waveform_tensor.shape) == 1:
            waveform_tensor = waveform_tensor.unsqueeze(0)
        elif len(waveform_tensor.shape) == 2:
            if waveform_tensor.shape[0] > waveform_tensor.shape[1]:
                waveform_tensor = waveform_tensor.transpose(0, 1)
        # ComfyUI AUDIO 需要 batch 維度 [B,C,T]
        if waveform_tensor.dim() == 2:
            waveform_tensor = waveform_tensor.unsqueeze(0)
        print(f"✅ 音訊已載入: {audio_path} ({sample_rate}Hz, {tuple(waveform_tensor.shape)})")
        return {"waveform": waveform_tensor, "sample_rate": sample_rate}
    except Exception as e:
        print(f"⚠️ 載入音訊失敗 {audio_path}: {e}")
        return None


def _mux_video_audio(video_path, audio_path, output_filename="merged"):
    """模型把影音分開回傳時，自動用 ffmpeg 合併回單一影片（放暫存目錄）
    失敗時回傳 None（沿用原始影片）"""
    try:
        import subprocess
        import time
        output_dir = get_download_directory()
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{output_filename}_{int(time.time())}.mp4")
        cmd = ['ffmpeg', '-i', video_path, '-i', audio_path,
               '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
               '-shortest', '-y', output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(output_path):
            print(f"🔄 已自動合併影音: {output_path}")
            return output_path
        print(f"⚠️ ffmpeg 合併失敗，沿用原始影片: {result.stderr[-200:] if result.stderr else ''}")
        return None
    except Exception as e:
        print(f"⚠️ 合併影音失敗，沿用原始影片: {e}")
        return None


def _run_replicate_model(model_id, prompt="", image=None, input_reference=None,
                          first_frame_image=None, last_frame=None, start_image=None,
                          video=None, audio=None, **kwargs):
    """
    共用的 Replicate 模型執行邏輯
    Returns: (video, audio, image_tensor, info_text, file_path)
    video 為 VIDEO 物件（VideoWrapper）或 None；audio 為 ComfyUI AUDIO dict 或 None
    """
    config = get_model_config(model_id) if HAS_MODEL_CONFIGS else None
    if not config:
        info = f"❌ 未知模型: {model_id}"
        print(info)
        return (None, None, torch.zeros((1, 512, 512, 3)), info, "")
    
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
        # 記錄被自動轉接的輸入（誤接補救），避免重複警告
        fallback_used = set()

        # === 統一圖片接口路由 / Unified image input routing ===
        # 節點只提供一個 images 輸入；各模型吃的圖片端點名稱不同
        # (image / input_reference / first_frame_image / start_image /
        #  reference_images / image_input / face ...)，在此依模型設定自動分配。
        # last_frame 為獨立輸入，不參與自動分配。
        unified_images = _flatten_image_items(kwargs.get('images'))
        if unified_images:
            list_targets = [n for n, c in model_inputs.items() if c.get("type") == "IMAGE_LIST"]
            single_targets = [n for n, c in model_inputs.items()
                              if c.get("type") == "IMAGE" and n != "last_frame"]
            if list_targets:
                # 吃清單的模型（Nano Banana image_input、Seedance reference_images）→ 全部分配
                target = list_targets[0]
                existing = image_map.get(target) if target in image_map else kwargs.get(target)
                if existing is None or (isinstance(existing, (list, tuple)) and len(existing) == 0):
                    image_map[target] = unified_images
                    print(f"🖼️ 統一圖片輸入 → '{target}' ({len(unified_images)} 張 / images)")
            elif single_targets:
                # 吃單張的模型 → 依模型參數宣告順序逐張分配
                assigned = 0
                for name in single_targets:
                    existing = image_map.get(name) if name in image_map else kwargs.get(name)
                    if existing is not None:
                        continue
                    if assigned >= len(unified_images):
                        break
                    image_map[name] = unified_images[assigned]
                    assigned += 1
                    print(f"🖼️ 統一圖片輸入: 第 {assigned} 張 → '{name}'")
                if assigned < len(unified_images):
                    print(f"⚠️ 有 {len(unified_images) - assigned} 張圖片未被使用（{model_id} 的圖片端點已滿）")
            else:
                print(f"⚠️ {model_id} 不接受圖片輸入，已忽略 {len(unified_images)} 張圖片 / model accepts no image input")

        def _upload_image_batch(tensor):
            """將批次圖片張量逐張存檔上傳，回傳 URL 清單
            支援：IMAGE batch 張量、REPLICATE_IMAGE_LIST (張量清單，各圖尺寸可不同)"""
            if isinstance(tensor, (list, tuple)):
                urls = []
                for item in tensor:
                    urls.extend(_upload_image_batch(item))
                return urls
            arr = tensor.cpu().numpy() if isinstance(tensor, torch.Tensor) else tensor
            if not hasattr(arr, 'shape'):
                return []
            if len(arr.shape) == 3:
                arr = arr[None, ...]
            urls = []
            for i in range(arr.shape[0]):
                single = arr[i:i+1]
                path = ImageUtils.save_image_tensor(single)
                if not path:
                    continue
                temp_files.append(path)
                url = api.upload_file(path)
                if url:
                    urls.append(url)
            return urls
        
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

                if image_param is None:
                    # 誤接補救：圖接在多圖輸入 (image_input) 但模型只吃單張 → 用第一張
                    list_param = kwargs.get('image_input')
                    if 'image_input' not in model_inputs and isinstance(list_param, (list, tuple)) and len(list_param) > 0:
                        image_param = list_param[0]
                        fallback_used.add('image_input')
                        print(f"ℹ️ '{input_name}' 未連接，改用多圖輸入 (image_input) 的第一張圖片")

                if image_param is not None:
                    image_path = ImageUtils.save_image_tensor(image_param)
                    if image_path:
                        temp_files.append(image_path)
                        if config.get("image_as_data_uri"):
                            # 部分模型（如 xai Grok）無法讀取 Replicate 檔案 API 的
                            # 授權 URL，改以 base64 data URI 內嵌傳送
                            image_url = _encode_image_data_uri(image_path)
                            print(f"🖼️ '{input_name}': 以 data URI 內嵌傳送 ({len(image_url) // 1024} KB)")
                        else:
                            image_url = api.upload_file(image_path)
                        if image_url:
                            inputs[input_name] = image_url
                elif is_required:
                    print(f"⚠️ 必要圖片參數 '{input_name}' 未提供")

            elif input_type == "IMAGE_LIST":
                image_param = None
                if input_name in image_map:
                    image_param = image_map[input_name]
                elif input_name in kwargs:
                    image_param = kwargs[input_name]

                if image_param is None or (isinstance(image_param, (list, tuple)) and len(image_param) == 0):
                    # 誤接補救：使用者常把參考圖接到 image / input_reference 等單張輸入，
                    # 但此模型（如 Nano Banana）只吃 image_input 清單 → 自動改用接到的圖
                    alt_sources = dict(image_map)
                    alt_sources['reference_images'] = kwargs.get('reference_images')
                    for alt_name, alt_value in alt_sources.items():
                        if alt_value is None or alt_name in model_inputs:
                            continue
                        image_param = alt_value
                        fallback_used.add(alt_name)
                        print(f"ℹ️ '{input_name}' 未連接，自動改用 '{alt_name}' 輸入的圖片 / using images wired to '{alt_name}'")
                        break

                if image_param is not None and not (isinstance(image_param, (list, tuple)) and len(image_param) == 0):
                    urls = _upload_image_batch(image_param)
                    if urls:
                        inputs[input_name] = urls
                        print(f"🖼️ '{input_name}': 已上傳 {len(urls)} 張參考圖片 / uploaded {len(urls)} reference image(s)")
                    else:
                        print(f"⚠️ '{input_name}' 沒有成功上傳任何圖片 / no image uploaded successfully")
                elif is_required:
                    print(f"⚠️ 必要圖片清單 '{input_name}' 未提供")

            elif input_type == "API_TOKEN":
                # 模型需要使用者的 Replicate API token (例如 nano-banana-2-transparent)
                inputs[input_name] = api.api_token

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
                value = kwargs.get(input_name) if input_name in kwargs else None
                if input_type == "COMBO":
                    allowed = input_config.get("options", [])
                    if value is not None and allowed and value not in allowed:
                        fallback = input_config.get("default", allowed[0])
                        print(f"⚠️ '{input_name}'='{value}' 不被 {model_id} 支援，改用 '{fallback}' (允許值: {allowed})")
                        value = fallback
                if input_name == "seed" and value is not None:
                    if value < 0:
                        value = None  # -1 = 隨機，不送出讓 Replicate 自行決定
                    else:
                        cfg_max = input_config.get("max")
                        if cfg_max is not None and value > cfg_max:
                            value = value % (cfg_max + 1)
                if value is not None:
                    inputs[input_name] = value
                elif is_required and "default" in input_config:
                    inputs[input_name] = input_config["default"]
        
        # 提醒被忽略的圖片輸入（有接線但該模型不使用，也沒被自動轉接）
        provided_images = dict(image_map)
        provided_images['image_input'] = kwargs.get('image_input')
        provided_images['reference_images'] = kwargs.get('reference_images')
        for name, value in provided_images.items():
            if value is None or (isinstance(value, (list, tuple)) and len(value) == 0):
                continue
            if name in model_inputs or name in fallback_used:
                continue
            print(f"⚠️ 輸入 '{name}' 已連接，但 {model_id} 不使用此參數，已忽略 / '{name}' is connected but not used by this model, ignored")

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
            return (None, None, torch.zeros((1, 512, 512, 3)), info_text, "")
        elif isinstance(result, list) and len(result) >= 2:
            video_path = result[0] if result[0] else ""
            audio_path = result[1] if result[1] else ""
            # 影音分開回傳的模型 → 自動合併回單一影片（轉換藏在後端）
            if (video_path and audio_path
                    and os.path.exists(video_path) and os.path.exists(audio_path)):
                merged = _mux_video_audio(video_path, audio_path, output_filename)
                if merged:
                    video_path = merged
        elif isinstance(result, str):
            if result.endswith(('.glb', '.obj', '.fbx', '.gltf')):
                file_path = result
            elif config.get("return_type") == "AUDIO":
                # 音訊生成模型（MusicGen 等）的結果是音訊檔
                audio_path = result
            else:
                video_path = result
                if config.get("has_audio"):
                    # 音軌已從影片抽出（影片本身仍含音訊）
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
        if not video_path and not audio_path and not file_path and result and isinstance(result, str) and os.path.exists(result):
            try:
                img = cv2.imread(result, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    if len(img.shape) == 2:
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                    elif img.shape[2] == 4:
                        # 保留透明度 (nano-banana-2-transparent 等去背模型)
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
                    else:
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
        
        # 直接包成 ComfyUI 原生輸出（免轉換節點）；檔案留在暫存目錄，保存交給 Save 節點
        video_out = VideoWrapper(video_path) if video_path and os.path.exists(video_path) else None
        audio_out = _load_audio_file(audio_path) if audio_path and os.path.exists(audio_path) else None

        return (video_out, audio_out, first_frame, info_text, file_path)

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        for temp_file in temp_files:
            cleanup_temp_file(temp_file)
        return (None, None, torch.zeros((1, 512, 512, 3)), f"❌ 錯誤: {str(e)}", "")


# ======================
# 輸入節點 / Input Nodes
# ======================

class ReplicateMultiImageInput:
    """
    🖼️ 多圖輸入節點 - 從路徑載入多張圖片為圖片清單
    image_paths：每行一個圖片路徑（絕對路徑，或相對於 ComfyUI input 目錄）
    各圖片尺寸可以不同（不需要相同大小的 batch）
    也可用 image_1~6 接線輸入，或透過 image_list 串接多個此節點
    合併順序：image_list → image_1~6 → image_paths
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_paths": ("STRING", {
                    "default": "", "multiline": True,
                    "tooltip": "每行一個圖片路徑（絕對路徑或相對於 ComfyUI input 目錄）/ One image path per line (absolute, or relative to the ComfyUI input directory)"}),
            },
            "optional": {
                "image_1": ("IMAGE", {"tooltip": "圖片 1 / Image 1"}),
                "image_2": ("IMAGE", {"tooltip": "圖片 2 / Image 2"}),
                "image_3": ("IMAGE", {"tooltip": "圖片 3 / Image 3"}),
                "image_4": ("IMAGE", {"tooltip": "圖片 4 / Image 4"}),
                "image_5": ("IMAGE", {"tooltip": "圖片 5 / Image 5"}),
                "image_6": ("IMAGE", {"tooltip": "圖片 6 / Image 6"}),
                "image_list": ("REPLICATE_IMAGE_LIST", {
                    "tooltip": "串接另一個多圖輸入節點 / Chain another Multi Image Input node"}),
            },
        }

    RETURN_TYPES = ("REPLICATE_IMAGE_LIST",)
    RETURN_NAMES = ("image_list",)
    FUNCTION = "combine_images"
    CATEGORY = "replicate/input"

    @staticmethod
    def _parse_paths(image_paths):
        """解析多行路徑文字，去除空行與引號（Windows「複製路徑」會帶引號）"""
        paths = []
        for line in (image_paths or "").split("\n"):
            path = line.strip().strip('"').strip("'")
            if path:
                paths.append(path)
        return paths

    @staticmethod
    def _resolve_path(path):
        """回傳存在的完整路徑；找不到時回傳 None"""
        if os.path.exists(path):
            return path
        full_path = os.path.join(folder_paths.get_input_directory(), path)
        if os.path.exists(full_path):
            return full_path
        return None

    @classmethod
    def _load_image_from_path(cls, path):
        """從路徑載入圖片為 [1,H,W,3] 張量（處理 EXIF 方向）"""
        full_path = cls._resolve_path(path)
        if full_path is None:
            print(f"⚠️ 找不到圖片: {path}")
            return None
        try:
            from PIL import Image, ImageOps
            image = Image.open(full_path)
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            arr = np.array(image).astype(np.float32) / 255.0
            return torch.from_numpy(arr)[None,]
        except Exception as e:
            print(f"⚠️ 載入圖片失敗 {path}: {e}")
            return None

    @classmethod
    def IS_CHANGED(cls, image_paths="", **kwargs):
        """路徑指向的檔案變更時重新執行"""
        parts = []
        for path in cls._parse_paths(image_paths):
            full_path = cls._resolve_path(path)
            if full_path:
                try:
                    parts.append(f"{full_path}:{os.path.getmtime(full_path)}")
                except OSError:
                    parts.append(f"{full_path}:unreadable")
            else:
                parts.append(f"{path}:missing")
        return "|".join(parts)

    def combine_images(self, image_paths="", image_list=None, **kwargs):
        """合併串接清單、接線圖片與路徑載入的圖片（保留各自尺寸）"""
        images = list(image_list) if image_list else []
        for i in range(1, 7):
            img = kwargs.get(f"image_{i}")
            if img is not None:
                images.append(img)
        for path in self._parse_paths(image_paths):
            tensor = self._load_image_from_path(path)
            if tensor is not None:
                images.append(tensor)
        print(f"🖼️ 多圖輸入: 共 {len(images)} 個圖片輸入")
        return (images,)


# ======================
# 節點註冊
# ======================

NODE_CLASS_MAPPINGS = {
    # 生成節點（全模型，直接輸出 VIDEO/AUDIO/IMAGE）
    "ReplicateDynamicNode": ReplicateDynamicNode,

    # 輸入節點 / Input Nodes
    "ReplicateMultiImageInput": ReplicateMultiImageInput,
}

# 雙語顯示名稱映射 / Bilingual Display Name Mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "ReplicateDynamicNode": "🤖 Replicate 萬用生成 / Universal Generator (All Models)",
    "ReplicateMultiImageInput": "🖼️ 多圖輸入 / Multi Image Input",
}
