# ComfyUI Replicate API 整合 / Integration

[繁體中文](#繁體中文) | [English](#english)

---

## 繁體中文

通用 Replicate API 整合模組，支援多種 AI 模型（Sora 2, Veo 3.1, MiniMax, Lipsync 等）。

### 特色功能

✨ **動態參數** - 根據選擇的模型自動顯示/隱藏相關參數  
🎬 **影片生成** - Sora 2, Veo 3.1, MiniMax, Wan, SVD, Seedance, Kling, LTX  
🎭 **唇語同步** - Sync Lipsync 2 Pro  
🎨 **圖片生成** - Nano Banana Pro/2 (含透明去背), FLUX Schnell, FLUX Dev, Luma Photon  
🖼️ **多圖輸入** - 多張參考圖片一次餵給模型（尺寸可不同，最多 14 張）  
🔊 **音訊支援** - 獨立音訊輸出與合併功能  

### 快速開始

### 1. 安裝

**方式一：ComfyUI Manager（推薦）**

在 ComfyUI Manager 的 Custom Nodes 搜尋 `Replicate API NM` 並安裝。

**方式二：手動安裝**

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/neurmostudio0409/ComfyUI-replicate-api-NM
cd ComfyUI-replicate-api-NM
pip install -r requirements.txt
```

### 2. 設定 API Token

建立 `.env` 檔案：

```bash
export REPLICATE_API_TOKEN=你的token
```

從 https://replicate.com/account/api-tokens 取得 API token。

### 3. 重新啟動 ComfyUI

```bash
python main.py
```

## 可用節點

### 主要節點

- **🎬 Replicate (動態)** - 通用節點，支援所有模型，動態參數顯示
- **🖼️ 多圖輸入** - 貼上多行圖片路徑一次載入多張（每行一個路徑，支援絕對路徑或 ComfyUI input 目錄相對路徑），也可接線輸入；各圖尺寸可不同，可串接載入更多
- **📹 Replicate 影片輸出** - 將影片路徑轉換為 VIDEO 格式
- **🎵 Replicate 音訊輸出** - 輸出音訊檔案
- **🔄 合併影片與音訊** - 使用 FFmpeg 合併

### 基礎 Lipsync 節點

- **Sync Lipsync 生成** - 生成唇語同步影片
- **Sync 影片輸出** - 輸出 Lipsync 結果

### 專門化節點（可選）

- **🎬 Replicate 文字生成影片** - MiniMax 文字轉影片
- **🖼️ Replicate 圖片生成影片** - Wan/SVD 圖片轉影片
- **🎨 Replicate 圖片生成** - FLUX 圖片生成

## 支援的模型

### 影片生成
- **Sora 2** (openai/sora-2) - OpenAI 文字/圖片轉影片
- **Veo 3.1 Fast** (google/veo-3.1-fast) - Google 圖片轉影片
- **MiniMax Video-01** - 文字/圖片轉影片
- **Wan** (lucataco/wan) - 圖片轉影片
- **Stable Video Diffusion** - 圖片轉影片

### 唇語同步
- **Sync Lipsync 2 Pro** - 專業級唇語同步
- **Video Retalking** - 影片唇語同步

### 圖片生成
- **Nano Banana Pro** (google/nano-banana-pro) - Google 最先進圖片生成/編輯，1K/2K/4K，支援最多 14 張參考圖
- **Nano Banana 2** (google/nano-banana-2) - 快速圖片生成、多圖融合、Google 搜尋 grounding
- **Nano Banana 2 Transparent** (jide/nano-banana-2-transparent) - RGBA 透明去背
- **FLUX Schnell** - 快速圖片生成
- **FLUX Dev** - 高品質圖片生成
- **Luma Photon** - AI 圖片生成

## 使用範例

### Nano Banana 多圖參考生成

1. 新增「🖼️ 多圖輸入」節點，在 `image_paths` 貼上圖片路徑（每行一個，可直接用檔案總管「複製路徑」貼上，引號會自動去除）；也可用 image_1~6 接線輸入
2. 新增「🎨 圖片生成」節點，選擇模型：`nano-banana-pro` 或 `nano-banana-2`
3. 將多圖輸入的 `image_list` 接到圖片生成節點的 `image_input`
4. 輸入提示詞，選擇解析度（1K/2K/4K）與長寬比（`match_input_image` 可跟隨輸入圖）

```
image_paths 範例：
D:\photos\ref1.jpg
"C:\Users\me\Pictures\ref 2.png"
my_input_image.png        ← ComfyUI input 目錄內的檔案
```

### 透明去背（Nano Banana 2 Transparent）

1. 新增「🎨 圖片生成」節點，選擇模型：`nano-banana-2-transparent`
2. 接上要去背的圖片（`image`）
3. （可選）prompt 指定要保留的主體，例如 `the car`
4. 輸出為含 alpha 通道的 RGBA 圖片

### Sora 2 影片生成

1. 新增「🎬 Replicate (動態)」節點
2. 選擇模型：`sora-2`
3. 輸入提示詞（prompt）
4. 選擇長寬比（aspect_ratio）：portrait/landscape/square
5. （可選）連接輸入參考圖片（input_reference）
6. 連接「📹 Replicate 影片輸出」來轉換為 VIDEO 格式

### Veo 3.1 影片生成

1. 新增「🎬 Replicate (動態)」節點
2. 選擇模型：`veo-3.1-fast`
3. 連接輸入圖片（image）- 必要
4. 輸入提示詞（prompt）- 必要
5. （可選）連接最後一幀圖片（last_frame）
6. 選擇解析度（resolution）：480p/720p/1080p

### 唇語同步

1. 新增「Sync Lipsync 生成」節點
2. 連接影片輸入（IMAGE 格式）
3. 連接音訊輸入（AUDIO 格式）
4. 設定參數（sync_mode, temperature）
5. 連接「Sync 影片輸出」來轉換為 VIDEO 格式

## 檔案結構

```
ComfyUI-replicate-api-NM/
├── __init__.py              # 主初始化檔案
├── replicate_api.py         # API 客戶端（整合版）
├── replicate_nodes.py       # 所有節點（整合版）
├── replicate_utils.py       # 工具函式
├── model_configs.py         # 模型配置
├── requirements.txt         # Python 依賴
├── .env                     # API Token 配置
└── README.md               # 本檔案
```

## 需求

- ComfyUI
- Python 3.8+
- replicate
- opencv-python
- soundfile
- torch
- FFmpeg（音訊合併功能需要）

## 疑難排解

### API Token 錯誤

確保 `.env` 檔案格式正確：
```bash
export REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx
```

### FFmpeg 找不到

安裝 FFmpeg：
```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### 模型參數錯誤

請參考 `model_configs.py` 中的模型配置，確保提供所有必要參數。

## 更新日誌

### v2.3 (2026-07)
- ✅ 多圖輸入節點改版：支援貼上多行圖片路徑直接載入（每行一個，自動處理引號與 EXIF 方向，支援 input 目錄相對路徑）
- ✅ 檔案變更自動偵測（IS_CHANGED，改圖後重跑會重新載入）

### v2.2 (2026-07)
- ✅ 新增 Google Nano Banana Pro / Nano Banana 2 圖片生成模型
- ✅ 新增 Nano Banana 2 Transparent 透明去背模型（RGBA 輸出）
- ✅ 新增「🖼️ 多圖輸入」節點（image_input，最多 14 張、尺寸可不同）
- ✅ 單元測試（21 項）與 GitHub Actions CI/CD
- ✅ 發布至 Comfy Registry

### v2.1 (2025-01)
- ✅ 簡化檔案結構，整合 API 和節點
- ✅ 全面繁體中文化
- ✅ 移除冗餘程式碼和文檔
- ✅ 保持所有功能完整

### v2.0
- ✅ 新增 Sora 2 和 Veo 3.1 支援
- ✅ 動態參數系統
- ✅ 音訊輸出與合併功能
- ✅ 支援 14+ 模型

### v1.0
- 基礎 Lipsync 功能

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

### 連結

- Replicate API: https://replicate.com/
- API Tokens: https://replicate.com/account/api-tokens

---

## English

Universal Replicate API integration module supporting multiple AI models (Sora 2, Veo 3.1, MiniMax, Lipsync, etc.).

### Features

✨ **Dynamic Parameters** - Auto show/hide relevant parameters based on selected model  
🎬 **Video Generation** - Sora 2, Veo 3.1, MiniMax, Wan, SVD, Seedance, Kling, LTX  
🎭 **Lipsync** - Sync Lipsync 2 Pro  
🎨 **Image Generation** - Nano Banana Pro/2 (incl. transparent matting), FLUX Schnell, FLUX Dev, Luma Photon  
🖼️ **Multi Image Input** - Paste multiple image paths (one per line) to load them at once; sizes can differ, up to 14 images  
🔊 **Audio Support** - Independent audio output and merge functionality  

### Quick Start

#### 1. Installation

**Option 1: ComfyUI Manager (recommended)**

Search for `Replicate API NM` in ComfyUI Manager's Custom Nodes and install.

**Option 2: Manual**

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/neurmostudio0409/ComfyUI-replicate-api-NM
cd ComfyUI-replicate-api-NM
pip install -r requirements.txt
```

#### 2. Configure API Token

Create a `.env` file:

```bash
export REPLICATE_API_TOKEN=your_token_here
```

Get your API token from https://replicate.com/account/api-tokens

#### 3. Restart ComfyUI

```bash
python main.py
```

### Available Nodes

#### Main Nodes

- **🎬 Replicate (Dynamic)** - Universal node supporting all models with dynamic parameters
- **📹 Replicate Video Output** - Convert video path to VIDEO format
- **🎵 Replicate Audio Output** - Output audio files
- **🔄 Merge Video & Audio** - Merge using FFmpeg

#### Basic Lipsync Nodes

- **Sync Lipsync Generate** - Generate lip-synced videos
- **Sync Video Output** - Output Lipsync results

#### Specialized Nodes (Optional)

- **🎬 Replicate Text to Video** - MiniMax text-to-video
- **🖼️ Replicate Image to Video** - Wan/SVD image-to-video
- **🎨 Replicate Image Generation** - FLUX image generation

### Supported Models

#### Video Generation
- **Sora 2** (openai/sora-2) - OpenAI text/image-to-video
- **Veo 3.1 Fast** (google/veo-3.1-fast) - Google image-to-video
- **MiniMax Video-01** - Text/image-to-video
- **Wan** (lucataco/wan) - Image-to-video
- **Stable Video Diffusion** - Image-to-video

#### Lipsync
- **Sync Lipsync 2 Pro** - Professional lipsync
- **Video Retalking** - Video lipsync

#### Image Generation
- **Nano Banana Pro** (google/nano-banana-pro) - Google's state-of-the-art image generation/editing, 1K/2K/4K, up to 14 reference images
- **Nano Banana 2** (google/nano-banana-2) - Fast image generation, multi-image fusion, Google Search grounding
- **Nano Banana 2 Transparent** (jide/nano-banana-2-transparent) - RGBA transparent background matting
- **FLUX Schnell** - Fast image generation
- **FLUX Dev** - High-quality image generation
- **Luma Photon** - AI image generation

### Usage Examples

#### Sora 2 Video Generation

1. Add "🎬 Replicate (Dynamic)" node
2. Select model: `sora-2`
3. Enter prompt
4. Choose aspect_ratio: portrait/landscape/square
5. (Optional) Connect input_reference image
6. Connect "📹 Replicate Video Output" to convert to VIDEO format

#### Veo 3.1 Video Generation

1. Add "🎬 Replicate (Dynamic)" node
2. Select model: `veo-3.1-fast`
3. Connect input image - Required
4. Enter prompt - Required
5. (Optional) Connect last_frame image
6. Choose resolution: 480p/720p/1080p

#### Lipsync

1. Add "Sync Lipsync Generate" node
2. Connect video input (IMAGE format)
3. Connect audio input (AUDIO format)
4. Set parameters (sync_mode, temperature)
5. Connect "Sync Video Output" to convert to VIDEO format

### File Structure

```
ComfyUI-replicate-api-NM/
├── __init__.py              # Main initialization
├── replicate_api.py         # API client (integrated)
├── replicate_nodes.py       # All nodes (integrated)
├── replicate_utils.py       # Utility functions
├── model_configs.py         # Model configurations
├── requirements.txt         # Python dependencies
├── .env                     # API Token config
└── README.md               # This file
```

### Requirements

- ComfyUI
- Python 3.8+
- replicate
- opencv-python
- soundfile
- torch
- FFmpeg (required for audio merge functionality)

### Troubleshooting

#### API Token Error

Make sure `.env` file format is correct:
```bash
export REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx
```

#### FFmpeg Not Found

Install FFmpeg:
```bash
# Windows (using Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

#### Model Parameter Error

Refer to `model_configs.py` for model configurations and ensure all required parameters are provided.

### Changelog

#### v2.3 (2026-07)
- ✅ Multi Image Input rework: load images by pasting multi-line file paths (quote stripping, EXIF orientation, ComfyUI input-dir relative paths)
- ✅ Auto re-run on file changes (IS_CHANGED)

#### v2.2 (2026-07)
- ✅ Added Google Nano Banana Pro / Nano Banana 2 image generation models
- ✅ Added Nano Banana 2 Transparent matting model (RGBA output)
- ✅ Added "🖼️ Multi Image Input" node (image_input, up to 14 images of different sizes)
- ✅ Unit tests (21) and GitHub Actions CI/CD
- ✅ Published to Comfy Registry

#### v2.1 (2025-01)
- ✅ Simplified file structure, integrated API and nodes
- ✅ Full Traditional Chinese localization
- ✅ Removed redundant code and documentation
- ✅ Maintained complete functionality

#### v2.0
- ✅ Added Sora 2 and Veo 3.1 support
- ✅ Dynamic parameter system
- ✅ Audio output and merge functionality
- ✅ Support for 14+ models

#### v1.0
- Basic Lipsync functionality

### License

MIT License

### Contributing

Issues and Pull Requests are welcome!

### Links

- Replicate API: https://replicate.com/
- API Tokens: https://replicate.com/account/api-tokens
