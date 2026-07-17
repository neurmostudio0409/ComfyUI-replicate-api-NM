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
# 節點輸入定義
# ======================

def test_image_node_has_nano_banana_inputs(nodes):
    optional = nodes.ReplicateImageNode.INPUT_TYPES()["optional"]
    for key in ("image", "image_input", "resolution", "alpha_ceil", "alpha_floor",
                "image_search", "google_search"):
        assert key in optional, f"ReplicateImageNode 缺少 '{key}'"
    assert optional["image_input"][0] == "REPLICATE_IMAGE_LIST"
    assert "match_input_image" in optional["aspect_ratio"][0]


def test_dynamic_node_has_image_input(nodes):
    optional = nodes.ReplicateDynamicNode.INPUT_TYPES()["optional"]
    assert "image_input" in optional
    assert optional["image_input"][0] == "REPLICATE_IMAGE_LIST"


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


def test_run_grok_imagine_video(nodes, fake_api):
    nodes._run_replicate_model(
        "grok-imagine-video", prompt="a penguin walks away",
        image=torch.zeros((1, 16, 16, 3)),
        duration=5, resolution="720p", aspect_ratio="16:9",
    )
    assert fake_api.captured["model"] == "grok-imagine-video"
    sent = fake_api.captured["inputs"]
    assert sent["prompt"] == "a penguin walks away"
    assert sent["image"].startswith("https://")
    assert sent["duration"] == 5
    assert sent["resolution"] == "720p"
    assert sent["aspect_ratio"] == "16:9"


def test_run_grok_aspect_fallback(nodes, fake_api):
    # 節點預設 landscape 不被 grok 支援，應 fallback 到 auto
    nodes._run_replicate_model(
        "grok-imagine-video", prompt="x", aspect_ratio="landscape",
    )
    assert fake_api.captured["inputs"]["aspect_ratio"] == "auto"


def test_run_unknown_model_returns_error(nodes, fake_api):
    result = nodes._run_replicate_model("not-a-real-model", prompt="x")
    assert result[0] == []  # 無影片
    assert "未知模型" in result[3]


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
