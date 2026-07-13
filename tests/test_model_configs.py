"""model_configs.py 單元測試"""

REQUIRED_KEYS = {"name", "display_name", "category", "description", "inputs", "outputs", "return_type"}
VALID_INPUT_TYPES = {"STRING", "IMAGE", "IMAGE_LIST", "VIDEO", "AUDIO", "COMBO", "FLOAT", "INT", "BOOLEAN", "API_TOKEN"}


def test_all_models_have_required_keys(model_configs):
    for model_id, cfg in model_configs.REPLICATE_MODELS.items():
        missing = REQUIRED_KEYS - set(cfg.keys())
        assert not missing, f"{model_id} 缺少欄位: {missing}"


def test_all_input_types_are_valid(model_configs):
    for model_id, cfg in model_configs.REPLICATE_MODELS.items():
        for input_name, input_cfg in cfg["inputs"].items():
            assert input_cfg.get("type") in VALID_INPUT_TYPES, (
                f"{model_id}.{input_name} 型別無效: {input_cfg.get('type')}"
            )


def test_combo_defaults_are_valid_options(model_configs):
    for model_id, cfg in model_configs.REPLICATE_MODELS.items():
        for input_name, input_cfg in cfg["inputs"].items():
            if input_cfg.get("type") == "COMBO":
                options = input_cfg.get("options", [])
                default = input_cfg.get("default")
                assert options, f"{model_id}.{input_name} COMBO 沒有 options"
                assert default in options, (
                    f"{model_id}.{input_name} 預設值 '{default}' 不在 options 中"
                )


def test_every_category_belongs_to_a_group(model_configs):
    grouped = set()
    for prefixes in model_configs.CATEGORY_GROUPS.values():
        grouped.update(prefixes)
    for model_id, cfg in model_configs.REPLICATE_MODELS.items():
        assert cfg["category"] in grouped, (
            f"{model_id} 的分類 '{cfg['category']}' 未被任何分類節點涵蓋"
        )


def test_nano_banana_pro_config(model_configs):
    cfg = model_configs.get_model_config("nano-banana-pro")
    assert cfg is not None
    assert cfg["name"] == "google/nano-banana-pro"
    assert cfg["category"] == "image/generation"
    assert cfg["inputs"]["prompt"]["required"] is True
    assert cfg["inputs"]["image_input"]["type"] == "IMAGE_LIST"
    assert set(cfg["inputs"]["resolution"]["options"]) == {"1K", "2K", "4K"}
    assert cfg["inputs"]["aspect_ratio"]["default"] == "match_input_image"
    assert set(cfg["inputs"]["output_format"]["options"]) == {"jpg", "png"}


def test_nano_banana_2_config(model_configs):
    cfg = model_configs.get_model_config("nano-banana-2")
    assert cfg is not None
    assert cfg["name"] == "google/nano-banana-2"
    assert cfg["inputs"]["image_input"]["type"] == "IMAGE_LIST"
    assert cfg["inputs"]["image_search"]["type"] == "BOOLEAN"
    assert cfg["inputs"]["google_search"]["type"] == "BOOLEAN"


def test_nano_banana_2_transparent_config(model_configs):
    cfg = model_configs.get_model_config("nano-banana-2-transparent")
    assert cfg is not None
    # 需固定版本 hash
    assert cfg["name"].startswith("jide/nano-banana-2-transparent:")
    assert cfg["inputs"]["image"]["required"] is True
    assert cfg["inputs"]["replicate_api_token"]["type"] == "API_TOKEN"
    assert cfg["inputs"]["prompt"]["required"] is False


def test_nano_banana_models_in_image_group(model_configs):
    image_models = model_configs.get_model_names_by_group("image")
    for model_id in ("nano-banana-pro", "nano-banana-2", "nano-banana-2-transparent"):
        assert model_id in image_models
