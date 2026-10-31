# Apex Generator V2 release checklist

## Release package

- [x] Four Apex nodes in a single horizontal row: Model Matrix, Generation Nexus, Archive, Image Preview.
- [x] Starter prompt and LoRA stack are empty; existing graph wiring and generation defaults are preserved.
- [x] LoRA model and CLIP strengths have −5…+5 sliders, ±0.05 buttons, and direct numeric entry for any finite value.
- [x] Archive has one small Last save image; the dedicated Preview displays the same generated image larger.
- [x] README and changelog describe V2 in plain language and include install and model setup steps.
- [x] `node --check web/apex.js` passed; the starter JSON parses and contains 4 nodes, 17 links, and the requested node positions.
- [x] Static release assertions cover the exact node row and LoRA control range/step/buttons/manual-entry contract in `tests/test_release_scope.py`.
- [ ] Run the ComfyUI embedded Python compile and release checks. Python is not available on the normal shell PATH in the current environment.
- [ ] Live-check LoRA strength entry/buttons, node placement, and a generation in ComfyUI after updating the installed extension.
- [x] GitHub root updated; remote main verified at commit `5618b99b48938f1f54f409812a984ca935f9f943`.
- [x] Manual Registry publish workflow added to GitHub under `.github/workflows/publish-comfy-registry.yml`.
- [ ] Publish package `apex-pipeline` v2.0.0. Registry listing currently has v0.1.1; requires Apex to store the Registry personal access token as GitHub Actions secret `REGISTRY_ACCESS_TOKEN` and dispatch the publish action.
- [x] Prepared `../CIVITAI_V2_LISTING_DRAFT.md` and identified the V2 workflow file for upload.
- [ ] Publish Civitai update; browser site-safety blocks the domain in this session, so Apex must upload the prepared workflow and description manually.

## Publish sequence

1. **Done:** updated and verified the `main` branch of [ApexLightSpeed/ComfyUI_ApexPipeline](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline).
2. **Ready, awaiting Apex:** add Registry personal access token as GitHub Actions secret `REGISTRY_ACCESS_TOKEN`, then run the manual publish workflow for `apex-pipeline` v2.0.0. Never paste the token into chat.
3. **Prepared, access blocked:** upload the V2 workflow and use `../CIVITAI_V2_LISTING_DRAFT.md` on the existing Civitai listing. Browser access is blocked by site-safety controls; do not use another route to bypass that block.

Apex explicitly authorized this sequence on 2026-10-31. If a Registry or Civitai account action needs login, a key, or browser access that is not available in this session, provide the prepared submission and the specific next step.
