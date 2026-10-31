"""Refresh the clean V2 starter's package identity and strip saved widget state."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
WORKFLOW_PATH = ROOT / "workflows" / "Apex Generator V2.json"
RELEASE_VERSION = "2.0.7"

# Build from the actual shipped starter. The old script read an excluded
# "Prototype" JSON that is not present in a release checkout.
workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
expected = {"ApexModelOptimizer", "ApexLoraGenerationCore", "ApexOutput", "ApexPreview"}
actual = {node.get("type") for node in workflow.get("nodes", [])}
if actual != expected or len(workflow["nodes"]) != 4:
    raise ValueError(f"Expected the clean four-node Apex V2 graph, got {sorted(actual)}")

for node in workflow["nodes"]:
    node.pop("widgets_values", None)
    node.pop("widgets_values_named", None)
    properties = node.setdefault("properties", {})
    properties["cnr_id"] = "apex-pipeline"
    properties["ver"] = RELEASE_VERSION

WORKFLOW_PATH.write_text(
    json.dumps(workflow, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
