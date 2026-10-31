import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / "workflows" / "Apex Generator V2.json"


def load_workflow():
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def test_only_v2_workflow_is_in_release_package():
    ignore = (ROOT / ".comfyignore").read_text(encoding="utf-8")
    excluded = (
        "workflows/Apex Generator V1.json", "workflows/Apex Generator V2 Prototype.json",
        "runtime/", "build_v2_workflow.py", "V2_REDESIGN_NOTES.md", "RELEASE_CHECKLIST.md",
    )
    assert all(entry in ignore for entry in excluded)


def test_v2_workflow_uses_four_apex_nodes_and_no_external_canvas_nodes():
    data = load_workflow()
    assert [n["type"] for n in data["nodes"]] == [
        "ApexModelOptimizer", "ApexLoraGenerationCore", "ApexOutput", "ApexPreview"
    ]
    assert len(data["links"]) == 17
    assert all(n["type"].startswith("Apex") for n in data["nodes"])


def test_v2_workflow_id_is_unique_from_legacy_templates():
    data = load_workflow()
    template_ids = {
        json.loads((ROOT / "workflows" / name).read_text(encoding="utf-8"))["id"]
        for name in ("Apex Generator V1.json", "Apex Generator V2 Prototype.json")
    }
    assert data["id"] not in template_ids


def test_apex_ui_surface_is_trailing_and_excluded_from_workflow_values():
    source = (ROOT / "web" / "apex.js").read_text(encoding="utf-8")
    add_surface = source.index('node.addDOMWidget("apex_ui_surface"')
    hide_native = source.index("hideNativeWidgets(node,surface)", add_surface)
    marker = source.index("Keep the UI-only surface after backing controls.", hide_native)
    next_step = source.index("node._apxSurfaceAdded=true", marker)
    block = source[add_surface:next_step]
    assert "serialize:false" in block
    assert "surface.serialize=false" in block
    assert "node.widgets.unshift(surface)" not in block
    assert "node.widgets.splice" not in block


def test_v2_frontend_surface_is_scoped_away_from_legacy_workflows():
    source = (ROOT / "web" / "apex.js").read_text(encoding="utf-8")
    types = re.search(r'const TYPES = new Set\(\[(.*?)\]\);', source)
    assert types is not None
    assert set(re.findall(r'"([A-Za-z0-9_]+)"', types.group(1))) == {
        "ApexModelOptimizer", "ApexLoraGenerationCore", "ApexOutput", "ApexPreview"
    }
    assert "function isV2Graph(graph=app.graph)" in source
    assert "function applyGraphTitleMode(graph=app.graph)" in source
    assert 'if(!isV2Graph(this.graph))' in source
    assert "node.title_mode=" not in source
    assert "for(let gx=" not in source and "for(let gy=" not in source
    assert "ApexRecipe" not in types.group(1)
    assert "ApexGenerate" not in types.group(1)


def test_v2_graph_links_resolve_between_generation_and_output():
    data = load_workflow()
    nodes = {n["id"]: n for n in data["nodes"]}
    for link in data["links"]:
        link_id, source_id, source_slot, target_id, target_slot, _ = link
        assert source_id in nodes and target_id in nodes
        assert nodes[source_id]["outputs"][source_slot]["links"] is not None
        assert link_id in nodes[source_id]["outputs"][source_slot]["links"]
        assert nodes[target_id]["inputs"][target_slot]["link"] == link_id
        assert nodes[source_id]["outputs"][source_slot]["type"] == nodes[target_id]["inputs"][target_slot]["type"]


def test_generation_metadata_outputs_land_on_the_named_output_inputs():
    data = load_workflow()
    nodes = {n["id"]: n for n in data["nodes"]}
    generation = next(n for n in data["nodes"] if n["type"] == "ApexLoraGenerationCore")
    output = next(n for n in data["nodes"] if n["type"] == "ApexOutput")
    targets = {
        "image": "images", "metadata_positive": "positive", "seed": "seed",
        "steps": "steps", "cfg": "cfg", "sampler": "sampler",
        "scheduler": "scheduler", "extra_params": "extra_params",
        "width": "width", "height": "height", "model_name": "model_name",
        "model_summary": "model_summary",
    }
    for link in data["links"]:
        _, source_id, source_slot, target_id, target_slot, _ = link
        if source_id == generation["id"] and target_id == output["id"]:
            source_name = nodes[source_id]["outputs"][source_slot]["name"]
            target_name = nodes[target_id]["inputs"][target_slot]["name"]
            assert targets[source_name] == target_name


def test_resolved_model_summary_reaches_generation_for_provenance():
    data = load_workflow()
    nodes = {n["id"]: n for n in data["nodes"]}
    link = next(link for link in data["links"] if link[0] == 15)
    _, source_id, source_slot, target_id, target_slot, link_type = link
    assert (source_id, target_id, link_type) == (1, 2, "STRING")
    assert nodes[source_id]["outputs"][source_slot]["name"] == "summary"
    assert nodes[target_id]["inputs"][target_slot]["name"] == "model_summary"
    schema_source = (ROOT / "generator_nodes.py").read_text(encoding="utf-8")
    assert '"model_summary": ("STRING", {"forceInput": True})' in schema_source
    assert "_resolved_model_from_summary(model_summary)" in schema_source


def test_model_summary_reaches_output_for_lc123_resource_hashing():
    data = load_workflow()
    nodes = {n["id"]: n for n in data["nodes"]}
    link = next(link for link in data["links"] if link[0] == 16)
    _, source_id, source_slot, target_id, target_slot, link_type = link
    assert (source_id, target_id, link_type) == (2, 3, "STRING")
    assert nodes[source_id]["outputs"][source_slot]["name"] == "model_summary"
    assert nodes[target_id]["inputs"][target_slot]["name"] == "model_summary"
    source = (ROOT / "generator_nodes.py").read_text(encoding="utf-8")
    assert "_prompt_with_resolved_resources(graph, model_summary)" in source


def test_lc123_hash_prompt_uses_selected_resource_files_without_mutating_prompt():
    source = (ROOT / "generator_nodes.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name in {"_resolved_resources_from_summary", "_prompt_with_resolved_resources"}]
    namespace = {"re": re, "json": json}
    exec(compile(ast.Module(body=helpers, type_ignores=[]), str(ROOT / "generator_nodes.py"), "exec"), namespace)
    summary = (
        "Model: krea2_turbo_int8_convrot.safetensors (diffusion model)\n"
        "Text encoder: qwen3vl_4b_fp8_scaled.safetensors · krea2\n"
        "VAE: qwen_image_vae.safetensors"
    )
    prompt = {"1": {"class_type": "ApexModelOptimizer", "inputs": {
        "model_file": "★ Recommended", "text_encoder": "★ Recommended", "vae": "★ Recommended"
    }}}
    patched = namespace["_prompt_with_resolved_resources"](prompt, summary)
    assert patched["1"]["inputs"] == {
        "model_file": "krea2_turbo_int8_convrot.safetensors",
        "text_encoder": "qwen3vl_4b_fp8_scaled.safetensors",
        "vae": "qwen_image_vae.safetensors",
    }
    assert prompt["1"]["inputs"]["model_file"] == "★ Recommended"


def test_resolved_model_summary_parser_ignores_recommendation_token():
    source = (ROOT / "generator_nodes.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == "_resolved_model_from_summary")
    namespace = {"re": re}
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(ROOT / "generator_nodes.py"), "exec"), namespace)
    parse = namespace["_resolved_model_from_summary"]
    assert parse("LC Optimizer: Krea 2 (Turbo)\nmodel: krea2_turbo_int8_convrot.safetensors (diffusion model)") == "krea2_turbo_int8_convrot.safetensors"
    assert parse("Diffusion model: krea2_turbo_fp8_scaled.safetensors\nVAE: qwen_image_vae.safetensors") == "krea2_turbo_fp8_scaled.safetensors"
    assert parse("model: ★ Recommended") == ""


def test_generation_starts_without_prompt_or_loras_and_uses_random_seed():
    data = load_workflow()
    node = next(n for n in data["nodes"] if n["type"] == "ApexLoraGenerationCore")
    assert "widgets_values" not in node
    assert "widgets_values_named" not in node
    assert "widgets_values" not in next(n for n in data["nodes"] if n["type"] == "ApexModelOptimizer")
    source = (ROOT / "generator_nodes.py").read_text(encoding="utf-8")
    assert "MAX_LORA_ROWS = 64" in source or "len(rows) > 64" in source


def test_apex_output_contains_full_lc123_save_configuration():
    data = load_workflow()
    node = next(n for n in data["nodes"] if n["type"] == "ApexOutput")
    assert "widgets_values" not in node
    assert "widgets_values_named" not in node


def test_preview_is_a_minimal_image_only_output_and_receives_archived_image():
    data = load_workflow()
    nodes = {n["id"]: n for n in data["nodes"]}
    preview = next(n for n in data["nodes"] if n["type"] == "ApexPreview")
    link = next(link for link in data["links"] if link[0] == 17)
    assert preview["inputs"] == [{"name": "image", "type": "IMAGE", "link": 17}]
    assert link == [17, 2, 0, 4, 0, "IMAGE"]
    assert nodes[2]["outputs"][0]["links"] == [4, 17]
    source = (ROOT / "generator_nodes.py").read_text(encoding="utf-8")
    assert "class ApexPreview" in source
    assert '"ApexPreview": ApexPreview' in source
    frontend = (ROOT / "web" / "apex.js").read_text(encoding="utf-8")
    assert "function addPreviewSurface(node)" in frontend
    assert 'className="apx-preview-grip"' in frontend


def test_v2_node_mappings_include_integrated_generation_and_output_nodes():
    tree = ast.parse((ROOT / "generator_nodes.py").read_text(encoding="utf-8"))
    mapping = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "NODE_CLASS_MAPPINGS" for t in n.targets))
    names = {key.value for key in mapping.keys}
    assert {"ApexModelOptimizer", "ApexGenerationCore", "ApexLoraGenerationCore", "ApexOutput", "ApexPreview"} <= names
    assert "LCSaveImage" not in names and "LCSaveImageMetadata" not in names
