"""
Pytest 共用設定
以套件方式匯入本 repo（目錄名含連字號，需透過 importlib）
缺少的外部相依（cv2, replicate 等）會以最小 stub 取代，
讓測試在沒有完整 ComfyUI 環境的機器與 CI 上都能執行。
"""

import importlib
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_NAME = REPO_ROOT.name

# 讓 "ComfyUI-replicate-api-NM" 可作為套件匯入
if str(REPO_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT.parent))


def _stub_missing(name, attrs=None):
    """若模組無法匯入，註冊一個最小 stub"""
    try:
        importlib.import_module(name)
    except ImportError:
        mod = types.ModuleType(name)
        for key, value in (attrs or {}).items():
            setattr(mod, key, value)
        sys.modules[name] = mod


_stub_missing("cv2", {
    "VideoCapture": object,
    "IMREAD_UNCHANGED": -1,
    "imread": lambda *a, **k: None,
})
_stub_missing("replicate")
_stub_missing("dotenv", {"load_dotenv": lambda *a, **k: None})
_stub_missing("requests")
_stub_missing("soundfile")


@pytest.fixture(scope="session")
def model_configs():
    return importlib.import_module(f"{PKG_NAME}.model_configs")


@pytest.fixture(scope="session")
def nodes():
    return importlib.import_module(f"{PKG_NAME}.replicate_nodes")


class FakeReplicateAPI:
    """攔截 run_model / upload_file 的假 API，記錄實際送出的參數"""

    api_token = "test-token-123"
    captured = {}

    def __init__(self, *args, **kwargs):
        pass

    def upload_file(self, file_path):
        return f"https://fake.replicate.delivery/{Path(file_path).name}"

    def run_model(self, model_id, inputs, output_filename="out"):
        FakeReplicateAPI.captured = {
            "model": model_id,
            "inputs": dict(inputs),
            "output_filename": output_filename,
        }
        return None


@pytest.fixture
def fake_api(nodes, monkeypatch):
    """將節點模組中的 ReplicateAPI 換成假 API，並停用檔案存取"""
    FakeReplicateAPI.captured = {}
    monkeypatch.setattr(nodes, "ReplicateAPI", FakeReplicateAPI)
    monkeypatch.setattr(
        nodes.ImageUtils, "save_image_tensor",
        staticmethod(lambda tensor: "fake_image.png"),
    )
    monkeypatch.setattr(nodes, "cleanup_temp_file", lambda path: None)
    return FakeReplicateAPI
