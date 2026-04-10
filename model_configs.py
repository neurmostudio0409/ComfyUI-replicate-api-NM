"""
Replicate Model Configurations
Defines all supported models and their parameters
"""

REPLICATE_MODELS = {
    # ===== Video Generation Models =====
    "sora-2": {
        "name": "openai/sora-2",
        "display_name": "OpenAI Sora 2",
        "category": "video/generation",
        "description": "OpenAI's Sora 2 - Advanced text-to-video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "aspect_ratio": {"type": "COMBO", "options": ["portrait", "landscape", "square"], "default": "landscape"},
            "input_reference": {"type": "IMAGE", "required": False},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "veo-3.1-fast": {
        "name": "google/veo-3.1-fast",
        "display_name": "Google Veo 3.1 Fast",
        "category": "video/generation",
        "description": "Google's Veo 3.1 - Fast video generation from image and text",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "last_frame": {"type": "IMAGE", "required": False},
            "resolution": {"type": "COMBO", "options": ["480p", "720p", "1080p"], "default": "720p"},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "minimax-video-01": {
        "name": "minimax/video-01",
        "display_name": "MiniMax Video-01",
        "category": "video/generation",
        "description": "Generate high-quality videos from text prompts",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "first_frame_image": {"type": "IMAGE", "required": False},
            "prompt_optimizer": {"type": "BOOLEAN", "default": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "pixverse-v5": {
        "name": "pixverse/pixverse-v5",
        "display_name": "PixVerse V5",
        "category": "video/generation",
        "description": "High-quality video generation with detailed control",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "quality": {"type": "COMBO", "options": ["480p", "720p", "1080p"], "default": "1080p"},
            "duration": {"type": "INT", "default": 8, "min": 1, "max": 30, "step": 1},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "luma-photon": {
        "name": "luma/photon",
        "display_name": "Luma Photon",
        "category": "image/generation",
        "description": "Fast, high-quality image generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "aspect_ratio": {"type": "COMBO", "options": ["16:9", "9:16", "4:3", "3:4", "1:1"], "default": "16:9"},
        },
        "outputs": ["image"],
        "return_type": "IMAGE",
    },
    
    "luma-photon-flash": {
        "name": "luma/photon-flash",
        "display_name": "Luma Photon Flash",
        "category": "image/generation",
        "description": "Ultra-fast image generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "aspect_ratio": {"type": "COMBO", "options": ["16:9", "9:16", "4:3", "3:4", "1:1"], "default": "16:9"},
        },
        "outputs": ["image"],
        "return_type": "IMAGE",
    },
    
    # ===== Lipsync Models =====
    "lipsync-2-pro": {
        "name": "sync/lipsync-2-pro",
        "display_name": "Sync Lipsync 2 Pro",
        "category": "video/lipsync",
        "description": "Studio-grade lipsync model for video dubbing",
        "inputs": {
            "video": {"type": "VIDEO", "required": True},
            "audio": {"type": "AUDIO", "required": True},
            "sync_mode": {"type": "COMBO", "options": ["loop", "bounce", "cut_off", "silence", "remap"], "default": "loop"},
            "temperature": {"type": "FLOAT", "default": 0.5, "min": 0.0, "max": 1.0, "step": 0.1},
            "active_speaker": {"type": "BOOLEAN", "default": False},
        },
        "outputs": ["video", "audio"],
        "return_type": "VIDEO",
        "has_audio": True,
    },
    
    # ===== Image to Video Models =====
    "wan": {
        "name": "lucataco/wan",
        "display_name": "Wan - Image to Video",
        "category": "video/generation",
        "description": "Convert images to videos with motion",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "num_frames": {"type": "INT", "default": 81, "min": 1, "max": 81, "step": 1},
            "guidance_scale": {"type": "FLOAT", "default": 7.5, "min": 1.0, "max": 20.0, "step": 0.5},
            "num_inference_steps": {"type": "INT", "default": 50, "min": 10, "max": 100, "step": 1},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "wan-2.5-i2v": {
        "name": "wan-video/wan-2.5-i2v",
        "display_name": "Wan 2.5 - Image to Video",
        "category": "video/generation",
        "description": "圖片轉影片 - 將靜態圖片轉換為動態影片 / Image to video conversion",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "stable-video-diffusion": {
        "name": "stability-ai/stable-video-diffusion",
        "display_name": "Stable Video Diffusion",
        "category": "video/generation",
        "description": "Generate videos from images using Stable Video Diffusion",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "motion_bucket_id": {"type": "INT", "default": 127, "min": 1, "max": 255, "step": 1},
            "cond_aug": {"type": "FLOAT", "default": 0.02, "min": 0.0, "max": 1.0, "step": 0.01},
            "decoding_t": {"type": "INT", "default": 14, "min": 1, "max": 100, "step": 1},
            "fps": {"type": "INT", "default": 6, "min": 1, "max": 30, "step": 1},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    # ===== Text to Video Models =====
    "minimax-video-01-live": {
        "name": "minimax/video-01-live",
        "display_name": "MiniMax Video-01 Live",
        "category": "video/generation",
        "description": "Real-time video generation from text",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "first_frame_image": {"type": "IMAGE", "required": False},
            "prompt_optimizer": {"type": "BOOLEAN", "default": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "hailuo-2.3-fast": {
        "name": "minimax/hailuo-2.3-fast",
        "display_name": "MiniMax Hailuo 2.3 Fast",
        "category": "video/generation",
        "description": "快速影片生成 - 高速生成高品質影片 / Fast high-quality video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "duration": {"type": "INT", "default": 10, "min": 1, "max": 30, "step": 1},
            "first_frame_image": {"type": "IMAGE", "required": False},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "sora-2-pro": {
        "name": "openai/sora-2-pro",
        "display_name": "OpenAI Sora 2 Pro",
        "category": "video/generation",
        "description": "Sora 2 專業版 - OpenAI 最先進的文字轉影片模型 / OpenAI's most advanced text-to-video model",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "ltx-2-fast": {
        "name": "lightricks/ltx-2-fast",
        "display_name": "Lightricks LTX-2 Fast",
        "category": "video/generation",
        "description": "LTX-2 快速影片生成 - 圖片轉影片 / Fast image-to-video generation",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "ltx-2-pro": {
        "name": "lightricks/ltx-2-pro",
        "display_name": "Lightricks LTX-2 Pro",
        "category": "video/generation",
        "description": "LTX-2 Pro 圖片轉影片 / Image-to-video generation",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "ltx-2-distilled": {
        "name": "lightricks/ltx-2-distilled",
        "display_name": "Lightricks LTX-2 Distilled",
        "category": "video/generation",
        "description": "LTX-2 Distilled 圖片轉影片 / Distilled image-to-video generation",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "ltx-2.3-fast": {
        "name": "lightricks/ltx-2.3-fast",
        "display_name": "Lightricks LTX-2.3 Fast",
        "category": "video/generation",
        "description": "LTX-2.3 快速文字轉影片 / Fast text-to-video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "camera_motion": {"type": "COMBO", "options": ["none", "dolly_in", "dolly_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "roll_cw", "roll_ccw"], "default": "none"},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "kling-v2.1": {
        "name": "kwaivgi/kling-v2.1",
        "display_name": "Kling v2.1",
        "category": "video/generation",
        "description": "Kling v2.1 - 圖片轉影片 / Image-to-video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "start_image": {"type": "IMAGE", "required": False},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "seedance-2.0": {
        "name": "bytedance/seedance-2.0",
        "display_name": "ByteDance Seedance 2.0",
        "category": "video/generation",
        "description": "Seedance 2.0 - 文字轉影片 / Text-to-video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "seed": {"type": "INT", "required": False, "default": -1, "min": -1, "max": 2147483647, "step": 1},
            "duration": {"type": "INT", "default": 7, "min": 1, "max": 30, "step": 1},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "seedance-1-lite": {
        "name": "bytedance/seedance-1-lite",
        "display_name": "ByteDance Seedance 1 Lite",
        "category": "video/generation",
        "description": "Seedance 1 Lite - 輕量文字轉影片 / Lightweight text-to-video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "seedance-1-pro": {
        "name": "bytedance/seedance-1-pro",
        "display_name": "ByteDance Seedance 1 Pro",
        "category": "video/generation",
        "description": "Seedance 1 Pro - 專業文字轉影片 / Professional text-to-video generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    "p-video": {
        "name": "prunaai/p-video",
        "display_name": "PrunaAI P-Video",
        "category": "video/generation",
        "description": "快速影片生成 - 從圖片和文字生成影片 / Fast video generation from image and text",
        "inputs": {
            "image": {"type": "IMAGE", "required": True},
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "prompt_upsampling": {"type": "BOOLEAN", "default": False},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },

    # ===== Video Enhancement Models =====
    "video-retalking": {
        "name": "chenxwh/video-retalking",
        "display_name": "Video Retalking",
        "category": "video/enhancement",
        "description": "Audio-based lip synchronization for talking head videos",
        "inputs": {
            "video": {"type": "VIDEO", "required": True},
            "audio": {"type": "AUDIO", "required": True},
            "face": {"type": "IMAGE", "required": False},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    "real-esrgan-video": {
        "name": "lucataco/real-esrgan-video",
        "display_name": "Real-ESRGAN Video Upscale",
        "category": "video/enhancement",
        "description": "Upscale videos with Real-ESRGAN",
        "inputs": {
            "video": {"type": "VIDEO", "required": True},
            "scale": {"type": "INT", "default": 2, "min": 1, "max": 4, "step": 1},
            "face_enhance": {"type": "BOOLEAN", "default": False},
        },
        "outputs": ["video"],
        "return_type": "VIDEO",
    },
    
    # ===== Audio Models =====
    "musicgen": {
        "name": "meta/musicgen",
        "display_name": "MusicGen",
        "category": "audio/generation",
        "description": "Generate music from text descriptions",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "duration": {"type": "INT", "default": 8, "min": 1, "max": 30, "step": 1},
            "model_version": {"type": "COMBO", "options": ["stereo-large", "large", "medium", "small"], "default": "stereo-large"},
            "temperature": {"type": "FLOAT", "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1},
        },
        "outputs": ["audio"],
        "return_type": "AUDIO",
    },
    
    "video-to-sfx-v1": {
        "name": "mirelo/video-to-sfx-v1",
        "display_name": "Video to SFX V1",
        "category": "audio/generation",
        "description": "影片轉音效 - 根據影片內容自動生成音效 / Generate sound effects from video content",
        "inputs": {
            "video_path": {"type": "VIDEO", "required": True},
            "num_samples": {"type": "INT", "default": 4, "min": 1, "max": 10, "step": 1},
        },
        "outputs": ["audio"],
        "return_type": "AUDIO",
    },

    "voice-cloning": {
        "name": "minimax/voice-cloning",
        "display_name": "MiniMax Voice Cloning",
        "category": "audio/voice-cloning",
        "description": "聲音克隆 - 從音訊樣本克隆聲音 / Clone voice from audio sample",
        "inputs": {
            "voice_file": {"type": "AUDIO", "required": True},
        },
        "outputs": ["json"],
        "return_type": "STRING",
    },
    
    # ===== Image Generation Models =====
    "flux-schnell": {
        "name": "black-forest-labs/flux-schnell",
        "display_name": "FLUX Schnell",
        "category": "image/generation",
        "description": "Fast high-quality image generation",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "aspect_ratio": {"type": "COMBO", "options": ["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"], "default": "1:1"},
            "output_format": {"type": "COMBO", "options": ["webp", "jpg", "png"], "default": "webp"},
            "output_quality": {"type": "INT", "default": 80, "min": 0, "max": 100, "step": 1},
        },
        "outputs": ["image"],
        "return_type": "IMAGE",
    },
    
    "flux-dev": {
        "name": "black-forest-labs/flux-dev",
        "display_name": "FLUX Dev",
        "category": "image/generation",
        "description": "High-quality image generation with more control",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
            "aspect_ratio": {"type": "COMBO", "options": ["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"], "default": "1:1"},
            "guidance": {"type": "FLOAT", "default": 3.5, "min": 1.5, "max": 5.0, "step": 0.1},
            "num_inference_steps": {"type": "INT", "default": 28, "min": 1, "max": 50, "step": 1},
            "output_format": {"type": "COMBO", "options": ["webp", "jpg", "png"], "default": "webp"},
            "output_quality": {"type": "INT", "default": 80, "min": 0, "max": 100, "step": 1},
        },
        "outputs": ["image"],
        "return_type": "IMAGE",
    },

    # ===== 3D Generation Models =====
    "hunyuan-3d-3.1": {
        "name": "tencent/hunyuan-3d-3.1",
        "display_name": "Tencent Hunyuan 3D 3.1",
        "category": "3d/generation",
        "description": "3D模型生成 - 從文字生成3D模型 / Generate 3D models from text",
        "inputs": {
            "prompt": {"type": "STRING", "required": True, "multiline": True},
        },
        "outputs": ["3d"],
        "return_type": "FILE",
    },
}


def get_model_config(model_id):
    """Get configuration for a specific model"""
    return REPLICATE_MODELS.get(model_id)


def get_models_by_category(category):
    """Get all models in a specific category"""
    return {k: v for k, v in REPLICATE_MODELS.items() if v.get("category") == category}


def get_all_categories():
    """Get list of all available categories"""
    categories = set()
    for model in REPLICATE_MODELS.values():
        if "category" in model:
            categories.add(model["category"])
    return sorted(list(categories))


def get_model_choices():
    """Get list of model choices for ComfyUI dropdown"""
    return [(v["display_name"], k) for k, v in REPLICATE_MODELS.items()]


def get_model_names():
    """Get list of model names for ComfyUI"""
    return list(REPLICATE_MODELS.keys())


# Category groups for node organization
CATEGORY_GROUPS = {
    "video": ["video/generation"],
    "enhancement": ["video/enhancement", "video/lipsync"],
    "audio": ["audio/generation", "audio/voice-cloning"],
    "image": ["image/generation"],
    "3d": ["3d/generation"],
}


def get_model_names_by_group(group_key):
    """Get model names for a category group"""
    prefixes = CATEGORY_GROUPS.get(group_key, [])
    return [k for k, v in REPLICATE_MODELS.items() if v.get("category") in prefixes]
