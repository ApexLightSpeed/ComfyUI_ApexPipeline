import json
import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_only_generator_workflow_is_shipped():
    workflows = sorted(p.name for p in (ROOT / "workflows").glob("*.json"))
    assert workflows == ["Apex Generator V1.json"]


def test_only_generator_apex_nodes_are_registered():
    tree = ast.parse((ROOT / "generator_nodes.py").read_text(encoding="utf-8"))
    mappings = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "NODE_CLASS_MAPPINGS" for t in n.targets))
    names = [k.value for k in mappings.keys]
    assert names == ["ApexModelOptimizer", "ApexRecipe", "ApexGenerate"]


def test_generator_workflow_uses_only_released_apex_nodes():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    released = {"ApexModelOptimizer", "ApexRecipe", "ApexGenerate"}
    used = {n.get("type") for n in data.get("nodes", []) if str(n.get("type", "")).startswith("Apex")}
    assert used == released


def test_generator_workflow_uses_standard_krea2_turbo_files_and_safe_defaults():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    optimizer = next(n for n in data["nodes"] if n.get("type") == "ApexModelOptimizer")
    values = optimizer["widgets_values"]
    assert values[2] == "krea2_turbo_fp8_scaled.safetensors"
    assert values[3] == "qwen3vl_4b_fp8_scaled.safetensors"
    assert values[4] == "qwen_image_vae.safetensors"
    assert values[12] == "off"

    lora_stack = next(n for n in data["nodes"] if n.get("type") == "PixaromaLoraLoader")
    assert lora_stack["widgets_values"][0]["loras"] == []


def test_workflow_starts_fresh_with_no_saved_loras_or_prompt():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    lora = next(n for n in data["nodes"] if n.get("type") == "PixaromaLoraLoader")
    prompt = next(n for n in data["nodes"] if n.get("type") == "PixaromaPrompt")

    assert lora["widgets_values"][0]["loras"] == []
    assert lora["widgets_values_named"]["loras_ui"]["loras"] == []
    serialized_lora_state = json.loads(lora["properties"]["loraLoaderState"])
    assert serialized_lora_state["loras"] == []
    assert "NYL" not in lora["properties"]["loraLoaderState"]
    assert "Jackerman" not in lora["properties"]["loraLoaderState"]

    assert prompt["widgets_values"] == [""]
    assert prompt["widgets_values_named"]["pix_prompt_ui"] == ""
    assert prompt["properties"]["promptState"]["text"] == ""


def test_workflow_seed_state_is_random_in_every_saved_representation():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    seed = next(n for n in data["nodes"] if n.get("type") == "PixaromaSeed")
    widget = seed["widgets_values"][0]
    named = seed["widgets_values_named"]["seed_ui"]
    state = seed["properties"]["seedState"]
    assert widget["mode"] == named["mode"] == state["mode"] == "random"
    assert widget["seed"] == named["seed"] == state["seed"] == 0
    assert state["runSeed"] == 0


def test_optimizer_named_snapshot_matches_visible_krea2_defaults():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    optimizer = next(n for n in data["nodes"] if n.get("type") == "ApexModelOptimizer")
    keys = ["base_model", "goal", "model_file", "text_encoder", "vae", "speed_ups",
            "attention", "fp16_accumulation", "step_cache", "torch_compile", "qwen21_cache",
            "clip_type", "spectrum", "lc_optimizer_face"]
    assert optimizer["widgets_values_named"] == dict(zip(keys, optimizer["widgets_values"]))
    assert optimizer["widgets_values_named"]["model_file"] == "krea2_turbo_fp8_scaled.safetensors"
    assert optimizer["widgets_values_named"]["text_encoder"] == "qwen3vl_4b_fp8_scaled.safetensors"
    assert optimizer["widgets_values_named"]["vae"] == "qwen_image_vae.safetensors"
    assert optimizer["widgets_values_named"]["spectrum"] == "off"


def test_workflow_notes_do_not_reference_stale_release_or_refine_stage():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    note = next(n for n in data["nodes"] if n.get("type") == "Note")
    text = note["widgets_values"][0] + note["widgets_values_named"]["text"] + data["extra"]["workflow_notes"]
    lowered = text.lower()
    assert "v8" not in lowered
    assert "refine stage" not in lowered
    assert "propmt" not in lowered


def test_only_one_saver_and_preview_is_not_a_file_save():
    data = json.loads((ROOT / "workflows" / "Apex Generator V1.json").read_text(encoding="utf-8"))
    assert sum(n.get("type") == "LCSaveImage" for n in data["nodes"]) == 1
    preview = next(n for n in data["nodes"] if n.get("type") == "PreviewImage")
    assert preview.get("type") == "PreviewImage"
