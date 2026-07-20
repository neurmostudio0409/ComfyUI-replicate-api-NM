# ComfyUI Replicate API 整合 / Integration

[繁體中文](#繁體中文) | [English](#english)

---

## 繁體中文

通用 Replicate API 整合模組，支援多種 AI 模型（Sora 2, Veo 3.1, MiniMax, Lipsync 等）。

### 特色功能

🤖 **萬用生成節點** - 單一節點跑所有模型，結果直接輸出 VIDEO / AUDIO / IMAGE，不需任何轉換節點  
🎬 **影片生成** - Sora 2, Veo 3.1, MiniMax, Wan, SVD, Seedance, Kling, LTX, Grok  
🎭 **唇語同步** - Sync Lipsync 2 Pro, Video Retalking  
🎨 **圖片生成** - Nano Banana Pro/2 (含透明去背), FLUX Schnell, FLUX Dev, Luma Photon  
🖼️ **多圖輸入** - 多張參考圖片一次餵給模型（尺寸可不同，最多 14 張）  
🔊 **自動轉換** - 音訊載入、影音合併等轉換全部藏在後端自動處理  
💾 **不重複存檔** - 結果放暫存目錄，保存交給下游 Save 節點  

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

## 可用節點（v2.5 起只有兩顆）

- **🤖 Replicate 萬用生成 / Universal Generator (All Models)** - 唯一的生成節點，下拉選擇任何模型；輸出：
  - `video`（VIDEO）→ 直接接 **Save Video**
  - `audio`（AUDIO）→ 直接接 **Save Audio**（音訊模型結果，或影片音軌）
  - `image`（IMAGE）→ 直接接 **Save Image**（圖片模型結果，或影片第一幀）
  - `file_path`（STRING）→ 3D 模型檔路徑（.glb 等）
  - `info`（STRING）→ 執行資訊
- **🖼️ 多圖輸入 / Multi Image Input** - 貼上多行圖片路徑一次載入多張（每行一個路徑，支援絕對路徑或 ComfyUI input 目錄相對路徑），也可接線輸入；各圖尺寸可不同，可串接載入更多

需要的格式轉換（影片包裝、音訊載入、影音合併）全部在後端自動處理，不需要也沒有獨立轉換節點。

## 支援的模型

### 影片生成
- **Sora 2** (openai/sora-2) - OpenAI 文字/圖片轉影片
- **Grok Imagine Video** (xai/grok-imagine-video) - xAI 文字/圖片轉影片與影片編輯
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
2. 新增「🤖 Replicate 萬用生成」節點，選擇模型：`nano-banana-pro` 或 `nano-banana-2`
3. 將多圖輸入的 `image_list` 接到萬用生成節點的 **`images`**（統一圖片接口，單張圖或 batch 也接這裡；其他套件多圖節點的清單輸出也可以）
4. 輸入提示詞，選擇解析度（1K/2K/4K）與長寬比（`match_input_image` 可跟隨輸入圖）
5. `image` 輸出接 **Save Image**

```
image_paths 範例：
D:\photos\ref1.jpg
"C:\Users\me\Pictures\ref 2.png"
my_input_image.png        ← ComfyUI input 目錄內的檔案
```

### 透明去背（Nano Banana 2 Transparent）

1. 萬用生成節點選擇模型：`nano-banana-2-transparent`
2. 把要去背的圖片接到 `images`（後端自動送到模型的 image 端點）
3. （可選）prompt 指定要保留的主體，例如 `the car`
4. `image` 輸出為含 alpha 通道的 RGBA 圖片，接 Save Image

### 影片生成（Sora / Veo / Seedance / Grok…）

1. 萬用生成節點選擇模型（例如 `sora-2`、`veo-3.1-fast`、`seedance-2.0`）
2. 輸入提示詞；需要輸入圖的模型把圖接到 `images`（後端自動路由到該模型的圖片端點），Veo 末幀接 `last_frame`
3. `video` 輸出**直接接 Save Video**（不需轉換節點）；有聲音的模型音軌已含在影片內，`audio` 輸出另可接 Save Audio

### 唇語同步 / 音訊 / 3D

- 唇語同步：模型選 `lipsync-2-pro` 或 `video-retalking`，接 `video` + `audio` 輸入，輸出接 Save Video
- 音訊生成：模型選 `musicgen`，`audio` 輸出直接接 **Save Audio**
- 3D 生成：`file_path` 輸出為 .glb 檔路徑（在暫存目錄，重啟會清除，需要保留請自行複製）

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

### v2.5.1 (2026-07)
- 🐛 修正 Grok 圖生影片報「Invalid image format」：xai 後端讀不到 Replicate 檔案 API 的授權 URL，Grok 的圖片改以 base64 data URI 內嵌傳送（其他模型維持檔案上傳）

### v2.5.0 (2026-07)
- ✅ **只留兩顆節點**：🤖 萬用生成（原「動態」節點改名）+ 🖼️ 多圖輸入；分類節點、輸出轉換節點、合併節點、舊版專門化節點全部移除
- ✅ **直接輸出原生格式**：`video`（VIDEO）/ `audio`（AUDIO）/ `image`（IMAGE）/ `file_path`（3D）/ `info`，可直接接 Save Video / Save Audio / Save Image，不需轉換節點
- ✅ 需要的轉換藏在後端自動處理：音訊檔自動載入為 AUDIO、影音分離的模型自動用 ffmpeg 合併回影片、音訊模型結果不再誤判為影片
- ✅ 分類節點專屬參數（alpha_ceil/floor、image_search、google_search、model_version、num_samples、prompt_upsampling 等）已併入萬用節點
- ✅ 送出防手震：1 秒內的重複 Run（連點、按鍵重複）自動忽略，避免同一任務重複送 API 扣費
- ⚠️ 舊 workflow 中的分類/輸出/Lipsync 節點會失效，請改用萬用生成節點直接接 Save 節點

### v2.4.0 (2026-07)
- ✅ **統一圖片接口**：所有圖片輸入收斂為單一 `images` 孔（接單張、batch 或多圖輸入節點皆可）
- ✅ 分配邏輯藏在後端：依模型設定自動路由到對應端點（Nano Banana→image_input、Seedance→reference_images、Veo/Wan→image、Sora→input_reference、MiniMax→首幀、Kling→起始圖）
- ✅ `last_frame`（末幀）保留獨立輸入，不參與自動分配
- ✅ **相容其他套件的清單輸出**：生成節點改為整批接收（INPUT_IS_LIST），接其他套件多圖節點的清單輸出時只執行一次、所有圖一起送出（不再逐張跑多次）
- ✅ Seed 支援 64-bit randomize：前端上限放寬，後端依各模型上限自動摺回；seed=-1 不送出（由 Replicate 隨機）
- ⚠️ 舊的 image / input_reference / first_frame_image / start_image / reference_images / image_input 輸入孔已移除，舊 workflow 需改接 `images`

### v2.3.2 (2026-07)
- ✅ 圖片輸入誤接補救：圖接到 `image` 等單張輸入但模型只吃 `image_input`（Nano Banana）時自動轉接，反之亦然
- ✅ 接了但模型不使用的圖片輸入，現在會印出明確警告（不再靜默忽略）

### v2.3 (2026-07)
- ✅ 生成結果（影片/圖片/音訊/3D）改下載到 ComfyUI temp 目錄，由 Save Image / Save Video 等節點負責保存，避免 output 目錄出現重複檔案
- ✅ 新增 xAI Grok Imagine Video 模型（文字/圖片轉影片、影片編輯模式）
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

GPL-3.0 License - 詳見 [LICENSE](LICENSE)

## 貢獻

歡迎提交 Issue 和 Pull Request！

### 連結

- Replicate API: https://replicate.com/
- API Tokens: https://replicate.com/account/api-tokens

---

## English

Universal Replicate API integration module supporting multiple AI models (Sora 2, Veo 3.1, MiniMax, Lipsync, etc.).

### Features

🤖 **Universal Generator node** - one node runs every model; outputs native VIDEO / AUDIO / IMAGE directly, no converter nodes  
🎬 **Video Generation** - Sora 2, Veo 3.1, MiniMax, Wan, SVD, Seedance, Kling, LTX, Grok  
🎭 **Lipsync** - Sync Lipsync 2 Pro, Video Retalking  
🎨 **Image Generation** - Nano Banana Pro/2 (incl. transparent matting), FLUX Schnell, FLUX Dev, Luma Photon  
🖼️ **Multi Image Input** - Paste multiple image paths (one per line) to load them at once; sizes can differ, up to 14 images  
🔊 **Automatic conversion** - audio loading and video/audio muxing handled in the backend  
💾 **No duplicate saves** - results go to the temp directory; saving is left to downstream Save nodes  

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

### Available Nodes (only two since v2.5)

- **🤖 Replicate Universal Generator (All Models)** - the only generation node; pick any model from the dropdown. Outputs:
  - `video` (VIDEO) → connect straight to **Save Video**
  - `audio` (AUDIO) → connect straight to **Save Audio** (audio-model results or extracted soundtrack)
  - `image` (IMAGE) → connect straight to **Save Image** (image-model results or first video frame)
  - `file_path` (STRING) → 3D model file path (.glb etc.)
  - `info` (STRING) → execution info
- **🖼️ Multi Image Input** - load multiple images by pasting paths (one per line; absolute or relative to the ComfyUI input directory) or by wiring images; sizes can differ, chainable

All required conversions (video wrapping, audio loading, video/audio muxing) happen automatically in the backend — there are no separate converter nodes.

### Supported Models

#### Video Generation
- **Sora 2** (openai/sora-2) - OpenAI text/image-to-video
- **Grok Imagine Video** (xai/grok-imagine-video) - xAI text/image-to-video and video editing
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

#### Video Generation (Sora / Veo / Seedance / Grok…)

1. Add the "🤖 Replicate Universal Generator" node and select a model (e.g. `sora-2`, `veo-3.1-fast`, `seedance-2.0`)
2. Enter a prompt; for image-conditioned models wire images into `images` (the backend routes them to the model's image endpoint automatically), Veo last frame goes to `last_frame`
3. Connect the `video` output **directly to Save Video** — no converter node needed; for models with sound the soundtrack is embedded in the video, and `audio` can additionally go to Save Audio

#### Lipsync / Audio / 3D

- Lipsync: select `lipsync-2-pro` or `video-retalking`, wire `video` + `audio` inputs, connect output to Save Video
- Audio generation: select `musicgen`; the `audio` output connects straight to **Save Audio**
- 3D generation: `file_path` holds the .glb path (in the temp directory — copy it elsewhere to keep it across restarts)

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

#### v2.5.1 (2026-07)
- 🐛 Fixed Grok image-to-video "Invalid image format": the xai backend cannot read Replicate's authenticated file API URLs, so Grok images are now sent inline as base64 data URIs (other models keep file upload)

#### v2.5.0 (2026-07)
- ✅ **Only two nodes remain**: 🤖 Universal Generator (renamed from "Dynamic") + 🖼️ Multi Image Input; category nodes, output converter nodes, merge node and legacy specialized nodes are all removed
- ✅ **Native outputs**: `video` (VIDEO) / `audio` (AUDIO) / `image` (IMAGE) / `file_path` (3D) / `info` — connect directly to Save Video / Save Audio / Save Image, no converter nodes needed
- ✅ Conversions happen automatically in the backend: audio files are loaded as AUDIO, models returning separate video+audio are muxed back via ffmpeg, audio-model results are no longer misrouted as video
- ✅ Category-node-only parameters (alpha_ceil/floor, image_search, google_search, model_version, num_samples, prompt_upsampling, …) merged into the universal node
- ✅ Queue debounce: duplicate Run submissions within 1 second (double-click, key repeat) are ignored to prevent double API charges
- ⚠️ Category/output/Lipsync nodes in old workflows will break; use the Universal Generator wired straight into Save nodes

#### v2.4.0 (2026-07)
- ✅ **Unified image input**: all image inputs consolidated into a single `images` socket (single image, batch, or Multi Image Input node)
- ✅ Routing hidden in backend: automatically mapped to each model's endpoint (Nano Banana→image_input, Seedance→reference_images, Veo/Wan→image, Sora→input_reference, MiniMax→first frame, Kling→start image)
- ✅ `last_frame` kept as a dedicated input, excluded from auto-routing
- ✅ **Compatible with list outputs from other packages**: generation nodes use INPUT_IS_LIST so list outputs run the node once with all images together (no more one-run-per-image)
- ✅ 64-bit seed randomize supported: frontend limit widened, backend folds values into each model's declared range; seed=-1 is omitted (Replicate randomizes)
- ⚠️ Legacy image sockets removed; reconnect old workflows to `images`

#### v2.3.2 (2026-07)
- ✅ Image input auto-fallback: images wired to `image` are auto-routed to `image_input` for models that only accept lists (Nano Banana), and vice versa
- ✅ Connected-but-unused image inputs now print an explicit warning instead of being silently dropped

#### v2.3 (2026-07)
- ✅ Results (video/image/audio/3D) now download to ComfyUI temp directory; saving is left to Save Image / Save Video nodes to avoid duplicate files in output
- ✅ Added xAI Grok Imagine Video model (text/image-to-video, video editing mode)
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

GPL-3.0 License - see [LICENSE](LICENSE)

### Contributing

Issues and Pull Requests are welcome!

### Links

- Replicate API: https://replicate.com/
- API Tokens: https://replicate.com/account/api-tokens
