# Apex Pipeline v2.0.7 release

## Changes

- Model, text encoder, VAE and LoRA selectors browse installed subfolders and search filenames/relative paths.
- LoRA search filters the existing dropdowns. Select a result, then Add LoRA or replace a stack entry.
- Local-only model choices; no LC123 recommended/download items.
- Clean four-node starter has no saved prompt, model files or LoRAs.
- Generation, LoRA application, sampling, decode and save execution are unchanged.
- Builder now updates the shipped V2 starter instead of a prototype JSON absent from the release package.

## Verification

- [x] Four-node starter retains its 17 valid links and has Registry identity `apex-pipeline` / `2.0.7` on each Apex node.
- [x] Model optimizer checks: 5 passed.
- [x] Release-scope checks: 19 passed.
- [x] Folder navigation/search harness passed; `node --check web/apex.js` and Python compilation passed.
- [x] Live ComfyUI checked nested model browsing and searched, selected, added, then removed a local LoRA. No model was selected and no generation ran.
- [x] Reviewed and pushed v2.0.7 source to `main` in commit `7b4e06d7ecef92902778fff04b83e58d14e7b0f2`.
- [x] Publish run [41242060774](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline/actions/runs/41242060774) succeeded; `Publish current version` completed.
- [x] Registry version record `b100531f-f4e4-431b-a29b-d63c5a5b24c2` exists with status `NodeVersionStatusPending`.
- [ ] After Registry review, install v2.0.7 and check selectors on a clean install.

Registry package: `apex-pipeline` under publisher `apexlightspeed`. Versions are immutable; do not retry a published version number.
