"""replicate_nodes.py 單元測試"""

import torch


# ======================
# 節點註冊
# ======================

def test_node_mappings_consistent(nodes):
    class_keys = set(nodes.NODE_CLASS_MAPPINGS.keys())
    display_keys = set(nodes.NODE_DISPLAY_NAME_MAPPINGS.keys())
    assert class_keys == display_keys, (
        f"註冊不一致: 缺顯示名稱 {class_keys - display_keys}, 缺類別 {display_keys - class_keys}"
    )


def test_all_nodes_build_input_types(nodes):
    for name, cls in nodes.NODE_CLASS_MAPPINGS.items():
        input_types = cls.INPUT_TYPES()
        assert isinstance(input_types, dict), name
        assert "required" in input_types, name


def test_multi_image_input_registered(nodes):
    assert "ReplicateMultiImageInput" in nodes.NODE_CLASS_MAPPINGS


# ======================
# 多圖輸入節點
# ======================

def test_multi_image_combine_different_sizes(nodes):
    node = nodes.ReplicateMultiImageInput()
    a = torch.zeros((1, 64, 64, 3))
    b = torch.zeros((2, 32, 32, 3))  # 尺寸不同也可以
    (result,) = node.combine_images(image_1=a, image_3=b)
    assert len(result) == 2


def test_multi_image_chaining(nodes):
    node = nodes.ReplicateMultiImageInput()
    a = torch.zeros((1, 8, 8, 3))
    (first,) = node.combine_images(image_1=a, image_2=a)
    (chained,) = node.combine_images(image_list=first, image_1=a)
    assert len(chained) == 3


def test_multi_image_empty(nodes):
    node = nodes.ReplicateMultiImageInput()
    (result,) = node.combine_images()
    assert result == []


def test_multi_image_load_from_paths(nodes, tmp_path):
    from PIL import Image
    p1 = tmp_path / "a.png"
    p2 = tmp_path / "b.png"
    Image.new("RGB", (64, 48), (255, 0, 0)).save(p1)
    Image.new("RGB", (32, 32), (0, 255, 0)).save(p2)

    node = nodes.ReplicateMultiImageInput()
    # 第二行帶引號（模擬 Windows「複製路徑」），中間夾空行
    text = f'{p1}\n\n"{p2}"\n'
    (result,) = node.combine_images(image_paths=text)
    assert len(result) == 2
    assert tuple(result[0].shape) == (1, 48, 64, 3)  # [B,H,W,C]
    assert tuple(result[1].shape) == (1, 32, 32, 3)


def test_multi_image_missing_path_skipped(nodes):
    node = nodes.ReplicateMultiImageInput()
    (result,) = node.combine_images(image_paths="Z:/not/exists/nope.png")
    assert result == []


def test_multi_image_paths_and_wired_combined(nodes, tmp_path):
    from PIL import Image
    p1 = tmp_path / "c.png"
    Image.new("RGB", (16, 16), (0, 0, 255)).save(p1)

    node = nodes.ReplicateMultiImageInput()
    wired = torch.zeros((1, 8, 8, 3))
    (result,) = node.combine_images(image_paths=str(p1), image_1=wired)
    # 順序：接線圖片在前，路徑載入在後
    assert len(result) == 2
    assert tuple(result[0].shape) == (1, 8, 8, 3)
    assert tuple(result[1].shape) == (1, 16, 16, 3)


def test_multi_image_is_changed_tracks_mtime(nodes, tmp_path):
    from PIL import Image
    p1 = tmp_path / "d.png"
    Image.new("RGB", (8, 8)).save(p1)
    key1 = nodes.ReplicateMultiImageInput.IS_CHANGED(image_paths=str(p1))
    assert str(p1) in key1 and "missing" not in key1
    key_missing = nodes.ReplicateMultiImageInput.IS_CHANGED(image_paths="Z:/no/such.png")
    assert "missing" in key_missing


# ======================
# 節點輸入/輸出定義
# ======================

def test_only_two_nodes_registered(nodes):
    """v2.5：只留萬用生成節點與多圖輸入節點"""
    assert set(nodes.NODE_CLASS_MAPPINGS.keys()) == {
        "ReplicateDynamicNode", "ReplicateMultiImageInput",
    }


def test_dynamic_node_has_unified_images_and_last_frame(nodes):
    optional = nodes.ReplicateDynamicNode.INPUT_TYPES()["optional"]
    assert optional["images"][0] == "IMAGE,REPLICATE_IMAGE_LIST"
    assert "last_frame" in optional  # 末幀保留獨立輸入
    for legacy in ("image", "input_reference", "first_frame_image", "start_image",
                   "reference_images", "image_input"):
        assert legacy not in optional, f"'{legacy}' 應收斂到統一 images 接口"


def test_dynamic_node_covers_category_node_params(nodes):
    """分類節點移除後，其專屬參數需併入萬用節點"""
    optional = nodes.ReplicateDynamicNode.INPUT_TYPES()["optional"]
    for key in ("alpha_ceil", "alpha_floor", "image_search", "google_search",
                "prompt_upsampling", "model_version", "num_samples",
                "scale", "face_enhance", "generate_audio"):
        assert key in optional, f"萬用節點缺少 '{key}'"


def test_dynamic_node_outputs_native_types(nodes):
    """輸出直接是 VIDEO/AUDIO/IMAGE，不需轉換節點"""
    assert nodes.ReplicateDynamicNode.RETURN_TYPES == (
        "VIDEO", "AUDIO", "IMAGE", "STRING", "STRING")
    assert nodes.ReplicateDynamicNode.RETURN_NAMES == (
        "video", "audio", "image", "file_path", "info")


# ======================
# 模型執行參數組裝
# ======================

def test_run_nano_banana_2_with_image_list(nodes, fake_api):
    images = [torch.zeros((1, 16, 16, 3)), torch.zeros((2, 16, 16, 3))]
    nodes._run_replicate_model(
        "nano-banana-2", prompt="a cat",
        image_input=images, aspect_ratio="16:9",
        resolution="2K", output_format="png",
        image_search=False, google_search=True,
    )
    sent = fake_api.captured["inputs"]
    # 清單中 1 張 + 2 張 batch = 3 個 URL
    assert len(sent["image_input"]) == 3
    assert all(url.startswith("https://") for url in sent["image_input"])
    assert sent["prompt"] == "a cat"
    assert sent["aspect_ratio"] == "16:9"
    assert sent["resolution"] == "2K"
    assert sent["output_format"] == "png"
    assert sent["google_search"] is True


def test_run_nano_banana_combo_fallback(nodes, fake_api):
    # 不支援的 COMBO 值應改用模型預設值
    nodes._run_replicate_model(
        "nano-banana-2", prompt="hi",
        resolution="720p", aspect_ratio="portrait",
    )
    sent = fake_api.captured["inputs"]
    assert sent["resolution"] == "1K"
    assert sent["aspect_ratio"] == "match_input_image"


def test_run_transparent_injects_api_token(nodes, fake_api):
    nodes._run_replicate_model(
        "nano-banana-2-transparent", prompt="",
        image=torch.zeros((1, 16, 16, 3)),
        alpha_ceil=250, alpha_floor=6,
    )
    sent = fake_api.captured["inputs"]
    assert sent["replicate_api_token"] == "test-token-123"
    assert "image" in sent
    assert "prompt" not in sent  # 空白選填 prompt 不送出
    assert sent["alpha_ceil"] == 250
    assert sent["alpha_floor"] == 6


def test_run_nano_banana_pro_basic(nodes, fake_api):
    nodes._run_replicate_model(
        "nano-banana-pro", prompt="engineers see the bridge",
        aspect_ratio="4:3", resolution="4K", output_format="png",
    )
    sent = fake_api.captured["inputs"]
    assert sent == {
        "prompt": "engineers see the bridge",
        "aspect_ratio": "4:3",
        "resolution": "4K",
        "output_format": "png",
    }


def test_run_grok_imagine_video(nodes, fake_api, tmp_path, monkeypatch):
    """Grok 後端讀不到 Replicate 檔案 API 的授權 URL，圖片應以 data URI 內嵌"""
    png = tmp_path / "in.png"
    png.write_bytes(b"\x89PNG-fake-bytes")
    monkeypatch.setattr(nodes.ImageUtils, "save_image_tensor",
                        staticmethod(lambda tensor: str(png)))
    nodes._run_replicate_model(
        "grok-imagine-video", prompt="a penguin walks away",
        image=torch.zeros((1, 16, 16, 3)),
        duration=5, resolution="720p", aspect_ratio="16:9",
    )
    assert fake_api.captured["model"] == "grok-imagine-video"
    sent = fake_api.captured["inputs"]
    assert sent["prompt"] == "a penguin walks away"
    assert sent["image"].startswith("data:image/png;base64,")
    assert sent["duration"] == 5
    assert sent["resolution"] == "720p"
    assert sent["aspect_ratio"] == "16:9"


def test_other_models_still_upload_by_url(nodes, fake_api):
    """未標記 image_as_data_uri 的模型維持檔案上傳 URL"""
    nodes._run_replicate_model(
        "veo-3.1-fast", prompt="x",
        images=torch.zeros((1, 8, 8, 3)),
    )
    assert fake_api.captured["inputs"]["image"].startswith("https://")


def test_run_grok_aspect_fallback(nodes, fake_api):
    # 節點預設 landscape 不被 grok 支援，應 fallback 到 auto
    nodes._run_replicate_model(
        "grok-imagine-video", prompt="x", aspect_ratio="landscape",
    )
    assert fake_api.captured["inputs"]["aspect_ratio"] == "auto"


def test_run_unknown_model_returns_error(nodes, fake_api):
    result = nodes._run_replicate_model("not-a-real-model", prompt="x")
    assert result[0] is None  # 無影片
    assert result[1] is None  # 無音訊
    assert "未知模型" in result[3]


# ======================
# 統一圖片接口路由 / Unified images routing
# ======================

def test_unified_images_routes_to_image_list(nodes, fake_api):
    """Nano Banana（吃 image_input 清單）：所有圖片都送進 image_input"""
    imgs = [torch.zeros((1, 16, 16, 3)), torch.zeros((2, 8, 8, 3))]  # 1 + batch 2
    nodes._run_replicate_model("nano-banana-pro", prompt="x", images=imgs)
    sent = fake_api.captured["inputs"]
    assert len(sent["image_input"]) == 3


def test_unified_images_single_tensor(nodes, fake_api):
    """單張張量直接接 images 也能路由"""
    nodes._run_replicate_model("nano-banana-2", prompt="x",
                               images=torch.zeros((1, 16, 16, 3)))
    assert len(fake_api.captured["inputs"]["image_input"]) == 1


def test_unified_images_routes_to_single_image(nodes, fake_api):
    """吃單張 image 的模型（Veo）：第一張進 image，last_frame 不參與自動分配"""
    nodes._run_replicate_model(
        "veo-3.1-fast", prompt="x",
        images=torch.zeros((1, 16, 16, 3)),
        last_frame=torch.zeros((1, 8, 8, 3)),  # 獨立輸入
    )
    sent = fake_api.captured["inputs"]
    assert "image" in sent
    assert "last_frame" in sent


def test_unified_images_routes_to_seedance_reference(nodes, fake_api):
    """Seedance 2.0（吃 reference_images 清單）"""
    nodes._run_replicate_model(
        "seedance-2.0", prompt="x", duration=7, resolution="720p",
        aspect_ratio="16:9", generate_audio=True, seed=-1,
        images=[torch.zeros((1, 8, 8, 3)), torch.zeros((1, 4, 4, 3))],
    )
    assert len(fake_api.captured["inputs"]["reference_images"]) == 2


def test_unified_images_routes_to_transparent_image(nodes, fake_api):
    """透明去背（吃單張 image）：用第一張"""
    nodes._run_replicate_model(
        "nano-banana-2-transparent", prompt="",
        images=[torch.zeros((1, 8, 8, 3)), torch.zeros((1, 4, 4, 3))],
        alpha_ceil=250, alpha_floor=6,
    )
    assert "image" in fake_api.captured["inputs"]


def test_unified_images_ignored_by_text_only_model(nodes, fake_api):
    """不吃圖的模型：忽略且不誤送參數"""
    nodes._run_replicate_model("flux-schnell", prompt="x",
                               images=torch.zeros((1, 8, 8, 3)))
    sent = fake_api.captured["inputs"]
    assert "image" not in sent and "image_input" not in sent


# ======================
# 圖片輸入誤接補救 / Image input fallback
# ======================

def test_image_wired_to_wrong_slot_falls_back_to_image_input(nodes, fake_api):
    """使用者把圖接到 image 而非 image_input 時，Nano Banana 仍應吃到圖"""
    nodes._run_replicate_model(
        "nano-banana-pro", prompt="a person in a tree",
        image=torch.zeros((1, 16, 16, 3)),  # 誤接到 image
    )
    sent = fake_api.captured["inputs"]
    assert "image_input" in sent, "接錯孔的圖片應自動轉為 image_input"
    assert len(sent["image_input"]) == 1


def test_empty_image_list_falls_back_to_wired_image(nodes, fake_api):
    """image_input 接了空清單時，改用 image 輸入的圖"""
    nodes._run_replicate_model(
        "nano-banana-2", prompt="x",
        image_input=[], image=torch.zeros((2, 8, 8, 3)),
    )
    sent = fake_api.captured["inputs"]
    assert len(sent["image_input"]) == 2  # batch 2 張


def test_image_list_falls_back_to_single_image_input(nodes, fake_api):
    """只吃單張 image 的模型（透明去背）接到多圖清單時，用第一張"""
    nodes._run_replicate_model(
        "nano-banana-2-transparent", prompt="",
        image_input=[torch.zeros((1, 8, 8, 3)), torch.zeros((1, 4, 4, 3))],
    )
    sent = fake_api.captured["inputs"]
    assert "image" in sent


def test_unsupported_image_input_is_ignored(nodes, fake_api):
    """模型不吃圖時，接了圖也不會誤送參數"""
    nodes._run_replicate_model(
        "flux-schnell", prompt="x",
        image=torch.zeros((1, 8, 8, 3)),
    )
    sent = fake_api.captured["inputs"]
    assert "image" not in sent
    assert "image_input" not in sent


# ======================
# 下載目錄（避免與 Save 節點重複存檔）
# ======================

def test_download_directory_uses_comfyui_temp(api_module, monkeypatch):
    """結果應下載到 ComfyUI temp 目錄，不是 output 目錄"""
    class FakeFolderPaths:
        @staticmethod
        def get_temp_directory():
            return "X:/comfy_temp"
        @staticmethod
        def get_output_directory():
            return "X:/comfy_output"
    monkeypatch.setattr(api_module, "folder_paths", FakeFolderPaths)
    assert api_module.get_download_directory() == "X:/comfy_temp"


def test_download_directory_fallback_without_comfyui(api_module, monkeypatch):
    class NoTempFolderPaths:
        @staticmethod
        def get_output_directory():
            return "X:/comfy_output"
    monkeypatch.setattr(api_module, "folder_paths", NoTempFolderPaths)
    path = api_module.get_download_directory()
    assert "comfyui_replicate" in path
    assert "comfy_output" not in path


# ======================
# Seed 範圍處理（前端 64-bit，後端依模型摺回）
# ======================

def test_seed_above_model_max_is_folded(nodes, fake_api):
    """ComfyUI randomize 產生的 64-bit seed 應摺回模型宣告的上限內"""
    nodes._run_replicate_model("seedance-2.0", prompt="x", seed=3369995675)
    sent = fake_api.captured["inputs"]
    assert sent["seed"] == 3369995675 % (2147483647 + 1)
    assert 0 <= sent["seed"] <= 2147483647


def test_seed_within_model_max_is_untouched(nodes, fake_api):
    nodes._run_replicate_model("seedance-2.0", prompt="x", seed=12345)
    assert fake_api.captured["inputs"]["seed"] == 12345


def test_seed_negative_is_omitted(nodes, fake_api):
    """seed=-1 表示隨機，不應送出，由 Replicate 自行決定"""
    nodes._run_replicate_model("seedance-2.0", prompt="x", seed=-1)
    assert "seed" not in fake_api.captured["inputs"]


def test_seed_not_sent_to_models_without_seed(nodes, fake_api):
    """未宣告 seed 的模型不應收到 seed 參數"""
    nodes._run_replicate_model("nano-banana-pro", prompt="x", seed=42)
    assert "seed" not in fake_api.captured["inputs"]


def test_node_seed_max_is_64bit(nodes):
    """前端 seed 上限放寬到 64-bit，避免 randomize 被 ComfyUI 驗證擋下"""
    seed_cfg = nodes.ReplicateDynamicNode.INPUT_TYPES()["optional"]["seed"][1]
    assert seed_cfg["max"] == 0xffffffffffffffff


# ======================
# INPUT_IS_LIST：整批接收其他套件的清單輸出
# ======================

def test_generation_nodes_declare_input_is_list(nodes):
    """生成節點應宣告 INPUT_IS_LIST，清單輸出才不會造成逐張多次執行"""
    assert getattr(nodes.ReplicateDynamicNode, "INPUT_IS_LIST", False) is True


def test_unwrap_list_inputs_keeps_images_whole(nodes):
    """images 保留整份清單，其他參數還原成單值"""
    t1, t2 = torch.zeros((1, 8, 8, 3)), torch.zeros((1, 4, 4, 3))
    out = nodes._unwrap_list_inputs({
        "images": [t1, t2],
        "prompt": ["hello"],
        "seed": [42],
        "video": [],
    })
    assert out["images"] == [t1, t2]
    assert out["prompt"] == "hello"
    assert out["seed"] == 42
    assert out["video"] is None


def test_unwrap_list_inputs_passes_plain_values(nodes):
    """非清單值（直接呼叫時）原樣通過"""
    out = nodes._unwrap_list_inputs({"prompt": "x", "seed": 7})
    assert out == {"prompt": "x", "seed": 7}


def test_dynamic_node_list_output_runs_once_with_all_images(nodes, fake_api):
    """模擬其他套件（如 Muse 多圖節點）的清單輸出：
    INPUT_IS_LIST 模式下節點只執行一次，兩張圖一起送進 image_input"""
    node = nodes.ReplicateDynamicNode()
    node.run_model(
        model=["nano-banana-pro"],
        prompt=["讓圖1人物在圖2場景互動"],
        images=[torch.zeros((1, 8, 8, 3)), torch.zeros((1, 4, 4, 3))],
        resolution=["2K"],
        aspect_ratio=["match_input_image"],
        output_format=["jpg"],
    )
    sent = fake_api.captured["inputs"]
    assert len(sent["image_input"]) == 2
    assert sent["prompt"] == "讓圖1人物在圖2場景互動"


def test_dynamic_node_replicate_image_list_still_works(nodes, fake_api):
    """自家多圖節點的 REPLICATE_IMAGE_LIST（會被再包一層清單）也正常"""
    node = nodes.ReplicateDynamicNode()
    node.run_model(
        model=["nano-banana-2"],
        prompt=["x"],
        images=[[torch.zeros((1, 8, 8, 3)), torch.zeros((1, 4, 4, 3))]],
    )
    assert len(fake_api.captured["inputs"]["image_input"]) == 2


def test_dynamic_node_batch_input_single_call(nodes, fake_api):
    node = nodes.ReplicateDynamicNode()
    node.run_model(
        model=["nano-banana-pro"],
        prompt=["x"],
        images=[torch.zeros((2, 8, 8, 3))],  # batch 也照樣攤平
    )
    assert len(fake_api.captured["inputs"]["image_input"]) == 2


# ======================
# 原生輸出打包（免轉換節點）
# ======================

def test_video_result_wrapped_as_native_video(nodes, fake_api, tmp_path, monkeypatch):
    """影片結果應直接包成 VIDEO 物件，可接 Save Video"""
    mp4 = tmp_path / "veo.mp4"
    mp4.write_bytes(b"\x00\x00")
    monkeypatch.setattr(fake_api, "run_model",
                        lambda self, m, i, o="out": str(mp4), raising=False)
    result = nodes._run_replicate_model("veo-3.1-fast", prompt="x")
    assert result[0] is not None
    assert result[0].get_path() == str(mp4)


def test_audio_model_result_becomes_audio_output(nodes, fake_api, tmp_path, monkeypatch):
    """音訊模型（MusicGen）的結果應包成 AUDIO dict，而不是誤判成影片"""
    wav = tmp_path / "musicgen.wav"
    wav.write_bytes(b"\x00\x00")
    monkeypatch.setattr(fake_api, "run_model",
                        lambda self, m, i, o="out": str(wav), raising=False)
    marker = {"waveform": None, "sample_rate": 44100}
    monkeypatch.setattr(nodes, "_load_audio_file", lambda p: marker)
    result = nodes._run_replicate_model("musicgen", prompt="jazz", duration=8)
    assert result[0] is None      # 不是影片
    assert result[1] is marker    # AUDIO 輸出


def test_3d_result_returned_as_file_path(nodes, fake_api, tmp_path, monkeypatch):
    """3D 模型結果走 file_path 輸出"""
    glb = tmp_path / "model.glb"
    glb.write_bytes(b"\x00")
    monkeypatch.setattr(fake_api, "run_model",
                        lambda self, m, i, o="out": str(glb), raising=False)
    result = nodes._run_replicate_model("veo-3.1-fast", prompt="x")
    assert result[0] is None
    assert result[4] == str(glb)
