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


def test_run_unknown_model_returns_error(nodes, fake_api):
    result = nodes._run_replicate_model("not-a-real-model", prompt="x")
    assert result[0] == []  # 無影片
    assert "未知模型" in result[3]
