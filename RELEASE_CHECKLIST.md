# Apex Generator V2 release checklist

## Release package

- [x] Four Apex nodes in a single horizontal row: Model Matrix, Generation Nexus, Archive, Image Preview.
- [x] Starter prompt and LoRA stack are empty; existing graph wiring and generation defaults are preserved.
- [x] LoRA model and CLIP strengths have −5…+5 sliders, ±0.05 buttons, and direct numeric entry for any finite value.
- [x] Archive has one small Last save image; the dedicated Preview displays the same generated image larger.
- [x] README and changelog describe V2 in plain language and include install and model setup steps.
- [x] `node --check web/apex.js` passed; the starter JSON parses and contains 4 nodes and 17 links.
- [ ] Run the ComfyUI embedded Python compile and release checks. Python is not available on the normal shell PATH in the current environment.
- [ ] Live-check LoRA strength entry/buttons, node placement, and a generation in ComfyUI after updating the installed extension.

## Publish sequence

1. Update and verify the `main` branch of [ApexLightSpeed/ComfyUI_ApexPipeline](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline).
2. Publish `apex-pipeline` to the ComfyUI Registry under publisher `apexlightspeed`.
3. Update the existing Civitai workflow listing with the V2 workflow and description.

Apex explicitly authorized this sequence on 2026-10-31. If a Registry or Civitai account action needs a login, key, or browser confirmation that is not available in this session, prepare the submission first and report the specific step that requires Apex.
