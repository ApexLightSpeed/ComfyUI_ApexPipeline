"""Isolated tests for the Apex Model Optimizer safe picker adapter."""
import importlib.util
import pathlib
import sys
import types

MODULE_PATH = pathlib.Path(__file__).parents[1] / "model_optimizer.py"


def load_module(monkeypatch, *, lc_enabled=True):
    fake_paths = types.ModuleType("folder_paths")
    categories = {
        "diffusion_models": ["Lustify.safetensors", "subfolder/Other.safetensors"],
        "text_encoders": ["Qwen3VL.safetensors"],
        "vae": ["qwen_image_vae.safetensors"],
        "unet_gguf": ["model.gguf"],
    }
    fake_paths.folder_names_and_paths = {key: [] for key in categories}
    fake_paths.get_filename_list = lambda name: list(categories.get(name, []))
    fake_nodes = types.ModuleType("nodes")
    fake_nodes.NODE_CLASS_MAPPINGS = {}
    monkeypatch.setitem(sys.modules, "folder_paths", fake_paths)
    monkeypatch.setitem(sys.modules, "nodes", fake_nodes)
    if lc_enabled:
        engine = types.ModuleType("fake_lc_engine")
        engine._list = lambda category: ["ORIGINAL-LC-LIST"]
        engine.local_files = lambda role: [("diffusion_models", x) for x in engine._list("diffusion_models")]
        lc_mod = types.ModuleType("fake_lc_node")
        lc_mod.E = engine
        class FakeLCOptimizer:
            __module__ = "fake_lc_node"
            @classmethod
            def INPUT_TYPES(cls):
                local = [name for _, name in engine.local_files("model")]
                return {"required": {"base_model": (["Krea 2 (Turbo)"], {}), "goal": (["Optimal"], {}), "model_file": (local, {})}, "optional": {"spectrum": (["auto", "on", "off"], {"default": "auto"})}}
            @classmethod
            def IS_CHANGED(cls, **kwargs):
                return "lc-change-token"
            def run(self, base_model, goal, **kwargs):
                scanned = engine._list("diffusion_models")
                return {"ui": {"lc_optimizer": ["preserved"]}, "result": ("MODEL", "CLIP", "VAE", "SUMMARY:" + ",".join(scanned))}
        lc_mod.LCOptimizer = FakeLCOptimizer
        fake_nodes.NODE_CLASS_MAPPINGS["LCOptimizer"] = FakeLCOptimizer
        monkeypatch.setitem(sys.modules, "fake_lc_node", lc_mod)
    spec = importlib.util.spec_from_file_location("apex_model_optimizer_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, fake_paths, fake_nodes


def test_lc_schema_uses_safe_comfy_lists_and_restores_engine(monkeypatch):
    module, _, fake_nodes = load_module(monkeypatch)
    engine = sys.modules["fake_lc_node"].E
    original = engine._list
    schema = module.ApexModelOptimizer.INPUT_TYPES()
    assert schema["required"]["model_file"][0] == ["Lustify.safetensors", "subfolder/Other.safetensors", "model.gguf"]
    assert schema["optional"]["spectrum"][1]["default"] == "off"
    assert engine._list is original


def test_lc_run_preserves_engine_execution_and_safe_listing(monkeypatch):
    module, _, _ = load_module(monkeypatch)
    result = module.ApexModelOptimizer().run("Krea 2 (Turbo)", "Optimal", model_file="Lustify.safetensors", text_encoder="Qwen3VL.safetensors", vae="qwen_image_vae.safetensors", speed_ups="Auto")
    assert result["result"] == ("MODEL", "CLIP", "VAE", "SUMMARY:Lustify.safetensors,subfolder/Other.safetensors,model.gguf")
    assert result["ui"]["lc_optimizer"] == ["preserved"]
    assert result["ui"]["apex_status"] == ["SUMMARY:Lustify.safetensors,subfolder/Other.safetensors,model.gguf"]


def test_native_fallback_schema_and_loader(monkeypatch):
    module, _, fake_nodes = load_module(monkeypatch, lc_enabled=False)
    class UNET:
        def load_unet(self, unet_name, weight_dtype):
            assert unet_name == "Lustify.safetensors" and weight_dtype == "default"
            return ("MODEL",)
    class CLIP:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"type": (["krea2"], {})}}
        def load_clip(self, clip_name, type):
            assert clip_name == "Qwen3VL.safetensors" and type == "krea2"
            return ("CLIP",)
    class VAE:
        def load_vae(self, vae_name):
            assert vae_name == "qwen_image_vae.safetensors"
            return ("VAE",)
    fake_nodes.NODE_CLASS_MAPPINGS.update({"UNETLoader": UNET, "CLIPLoader": CLIP, "VAELoader": VAE})
    schema = module.ApexModelOptimizer.INPUT_TYPES()
    assert "model_file" in schema["required"]
    assert schema["optional"]["spectrum"][1]["default"] == "off"
    out = module.ApexModelOptimizer().run("Krea 2 (Turbo)", "Optimal", "Lustify.safetensors", "Qwen3VL.safetensors", "qwen_image_vae.safetensors")
    assert out["result"][:3] == ("MODEL", "CLIP", "VAE")


def test_memory_error_becomes_empty_category_not_schema_crash(monkeypatch):
    module, fake_paths, _ = load_module(monkeypatch, lc_enabled=False)
    def fail(_name):
        raise MemoryError("simulated oversized model list")
    fake_paths.get_filename_list = fail
    schema = module.ApexModelOptimizer.INPUT_TYPES()
    assert schema["required"]["model_file"][0] == [module._EMPTY]
