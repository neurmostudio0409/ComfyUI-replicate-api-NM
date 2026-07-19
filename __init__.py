"""
ComfyUI Replicate API 整合模組
支援多種 Replicate 平台上的模型
"""

import os

# 以頂層模組方式匯入時（例如 pytest 收集）改用絕對匯入
# 用 __package__ 判斷而非 try/except，避免掩蓋真正的相依套件缺失錯誤
if __package__:
    from .replicate_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
else:
    from replicate_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 載入 API token
def load_api_token():
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('!'):
                        continue
                    if 'REPLICATE_API_TOKEN' in line:
                        if '=' in line:
                            key = line.split('=', 1)[1].strip().strip('"\'')
                            if key and key != '<paste-your-token-here>':
                                os.environ['REPLICATE_API_TOKEN'] = key
                                print("✅ 已從 .env 檔案載入 Replicate API token")
                                return
            print("⚠️ REPLICATE_API_TOKEN 未在 .env 檔案中配置")
            print("   請編輯 .env 並設定: export REPLICATE_API_TOKEN=<your-token>")
        else:
            print("⚠️ 找不到 .env 檔案。請建立一個並設定 REPLICATE_API_TOKEN")
            print("   從以下網址取得 API token: https://replicate.com/account/api-tokens")
    except Exception as e:
        print(f"❌ 載入 API token 時發生錯誤: {e}")

# 模組載入時載入 API token
load_api_token()

# 顯示歡迎訊息
print("=" * 70)
print("🤖 ComfyUI Replicate API - 萬用生成節點 v2.5")
print("=" * 70)
print("📦 支援的模型：")
print("   🎬 影片生成: Sora 2, Veo 3.1, Seedance, Kling, Grok, MiniMax, Wan")
print("   🎨 圖片生成: Nano Banana Pro/2/Transparent, FLUX, Luma Photon")
print("   🎭 唇語同步: Sync Lipsync 2 Pro, Video Retalking")
print("   🎵 音訊生成: MusicGen  🧊 3D 生成")
print("=" * 70)
print("✨ 節點：")
print("   🤖 萬用生成 - 單一節點跑所有模型，直接輸出 VIDEO/AUDIO/IMAGE")
print("   🖼️ 多圖輸入 - 載入多張參考圖片（各自尺寸）")
print("   轉換與影音合併全部自動處理，結果請接 Save 節點保存")
print("=" * 70)
print("🔑 API Tokens: https://replicate.com/account/api-tokens")
print("📚 文件: https://replicate.com/")
print("=" * 70)

# ComfyUI 相容性
WEB_DIRECTORY = "./web"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
