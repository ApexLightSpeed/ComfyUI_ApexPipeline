# Apex Generator V2 — release checklist

Current package: `apex-pipeline` v2.0.3. This release fixes node-pack identity in the distributed workflow.

## Release contents and verification

- [x] Clean four-node Apex workflow, 17 links, no saved model or LoRA selections.
- [x] Each node includes `cnr_id: apex-pipeline` and `ver: 2.0.3` so ComfyUI can associate missing Apex node types with the Registry pack.
- [x] Workflow builder stamps the same identity on regenerated files; a regression assertion checks all four nodes.
- [x] README explains the “Unknown pack” warning and how to install the package.
- [x] `node --check web/apex.js` passes; workflow JSON parses and identity/clean-starter checks pass.
- [x] Registry artifact verified: 18 entries, package version 2.0.3, four nodes carry the expected CNR id/version, and no workflow widget values are serialized.
- [ ] Python pytest was not run because Python/pytest were unavailable in the shell. Do not report the Python suite as passing.

## Publication

- [x] Source is on GitHub main; code release commit `e7de7608719e595cffec3a45e16b592a48c7934b`.
- [x] GitHub Actions publish run [41217974046](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline/actions/runs/41217974046) completed successfully.
- [x] Comfy Registry v2.0.3 uploaded as version ID `cc48a553-6be5-4075-bbe8-e69dc3f940b9`.
- [ ] Registry review is pending. Until it activates, install from the GitHub repository if needed. Do not republish v2.0.3; versions are immutable.
- [ ] Civitai's older workflow attachment still needs to be replaced by Apex. Upload `workflows/Apex Generator V2.json` from this release when ready; Civitai changes were not made here.

The user's personal recovery workflow is local-only and must never be distributed.
