# Apex Generator V2 — release checklist

Current package: `apex-pipeline` v2.0.4 candidate. Adds automatic Civitai workflow attribution to saved PNG metadata.

## Release contents and verification

- [x] Clean four-node Apex workflow, 17 links, no saved model or LoRA selections.
- [x] Each node includes `cnr_id: apex-pipeline` and `ver: 2.0.4` so ComfyUI can associate missing Apex node types with the Registry pack.
- [x] Apex Archive adds AIR `urn:air:other:unknown:civitai:3027606@3441098` automatically; Civitai's current AIR map uses `unknown` for its Comfy workflow model type. The manual AIR field is hidden and the workflow-embedding checkbox remains visible and on by default.
- [x] Output remains in `output/Apex`; Firefox uploaded from the shared directory, isolating the earlier file-access warning to Opera GX.
- [x] Workflow builder stamps the same identity on regenerated files; a regression assertion checks all four nodes.
- [x] README explains the “Unknown pack” warning and how to install the package.
- [x] `node --check web/apex.js` passes; workflow JSON parses and identity/clean-starter checks pass.
- [x] Previous v2.0.3 Registry artifact verified: 18 entries, four nodes carry the expected CNR id/version, and no workflow widget values are serialized.
- [ ] Python pytest was not run because Python/pytest were unavailable in the shell. Do not report the Python suite as passing.

## Publication

- [x] Previous v2.0.3 source is on GitHub main; code release commit `e7de7608719e595cffec3a45e16b592a48c7934b`.
- [x] GitHub Actions publish run [41217974046](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline/actions/runs/41217974046) completed successfully.
- [x] Comfy Registry v2.0.3 uploaded as version ID `cc48a553-6be5-4075-bbe8-e69dc3f940b9`.
- [ ] Registry review is pending. Until it activates, install from the GitHub repository if needed. Do not republish v2.0.3; versions are immutable.
- [ ] Civitai's older workflow attachment still needs to be replaced by Apex. Upload `workflows/Apex Generator V2.json` from this release when ready; Civitai changes were not made here.

## v2.0.4 candidate status

- Source and workflow edits are prepared locally. They are not yet committed to GitHub or published. Do not call this version published until the GitHub commit, successful Registry publish action, and Registry version record are verified.
- Live ComfyUI installation has not yet been synced/restarted for this candidate.
- User's successful Firefox upload confirms the output folder does not need to change; do not add copies or redirect output into Downloads.
- Verify Civitai recognizes the workflow resource when the candidate PNG is uploaded. Embedded ComfyUI `prompt`/`workflow` chunks are separate from the `civitaiResources` attribution field.
- The Registry publishing workflow is manual (`workflow_dispatch`). The available GitHub connector cannot dispatch it, so Apex must run Actions → Publish to Comfy Registry after the candidate commit is pushed.

The user's personal recovery workflow is local-only and must never be distributed.
