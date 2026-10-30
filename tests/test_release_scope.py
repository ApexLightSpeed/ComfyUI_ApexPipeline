import json
import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_only_generator_workflow_is_shipped():
    workflows = sorted(p.name for p in (ROOT / "workflows").glob("*.json"))
    assert workflows == ["Apex Generator v2.json"]


def test_only_generator_apex_nodes_are_registered():
    tree = ast.parse((ROOT / "generator_nodes.py").read_text(encoding="utf-8"))
    mappings = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "NODE_CLASS_MAPPINGS" for t in n.targets))
    names = [k.value for k in mappings.keys]
    assert names == ["ApexModelOptimizer", "ApexRecipe", "ApexGenerate"]


def test_generator_workflow_uses_only_released_apex_nodes():
    data = json.loads((ROOT / "workflows" / "Apex Generator v2.json").read_text(encoding="utf-8"))
    released = {"ApexModelOptimizer", "ApexRecipe", "ApexGenerate"}
    used = {n.get("type") for n in data.get("nodes", []) if str(n.get("type", "")).startswith("Apex")}
    assert used == released


def test_generator_workflow_uses_standard_krea2_turbo_files_and_safe_defaults():
    data = json.loads((ROOT / "workflows" / "Apex Generator v2.json").read_text(encoding="utf-8"))
    optimizer = next(n for n in data["nodes"] if n.get("type") == "ApexModelOptimizer")
    values = optimizer["widgets_values"]
    assert values[2] == "krea2_turbo_fp8_scaled.safetensors"
    assert values[3] == "qwen3vl_4b_fp8_scaled.safetensors"
    assert values[4] == "qwen_image_vae.safetensors"
    assert values[12] == "off"

    lora_stack = next(n for n in data["nodes"] if n.get("type") == "PixaromaLoraLoader")
    assert lora_stack["widgets_values"][0]["loras"] == []
