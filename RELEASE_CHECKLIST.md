# Apex Generator V2 release checklist

Current release candidate: `apex-pipeline` v2.0.1. It carries the already verified V2 workflow and frontend in a fresh Registry version, with clearer wording that the workflow does not save model or LoRA selections.

## Release package

- [x] Four Apex nodes in a single horizontal row: Model Matrix, Generation Nexus, Archive, Image Preview.
- [x] Starter prompt and LoRA stack are empty; existing graph wiring and generation defaults are preserved.
- [x] Distributed workflow contains no serialized widget values, model filenames, or LoRA selections.
- [x] LoRA model and CLIP strengths have −5…+5 sliders, ±0.05 buttons, and direct numeric entry for any finite value.
- [x] Archive has one small Last save image; the dedicated Preview displays the same generated image larger.
- [x] README and changelog describe V2 in plain language and include install and model setup steps.
- [x] `node --check web/apex.js` passed; the starter JSON parses and contains 4 nodes, 17 links, and the requested node positions.
- [x] Static release assertions cover the exact node row and LoRA control range/step/buttons/manual-entry contract in `tests/test_release_scope.py`.
- [x] ComfyUI embedded-Python compile and 13 release-scope assertions passed during the V2 implementation pass; see the handoff for evidence and environment details.
- [x] Live Krea 2 generation succeeded during final backend verification. After the later frontend-only LoRA UI sync, reloaded Comfy Desktop and confirmed the − / + controls and editable strength fields render. No sampling/model code changed during that UI sync.
- [ ] Independently exercise the ± buttons and manual numeric entry in the live UI; the control contract is verified in source, but those click/entry interactions were not re-tested after sync.
- [x] GitHub root updated; remote main verified at commit `7ae33de`.
- [x] Manual Registry publish workflow added to GitHub under `.github/workflows/publish-comfy-registry.yml`.
- [x] Publish package `apex-pipeline` v2.0.0. GitHub Actions run `41180870668` completed successfully. Public Registry versions API confirms v2.0.0 was uploaded and is `NodeVersionStatusPending`; the listing's `latest_version` still shows active v0.1.1 until the new version's status changes. Do not rerun the publish action.
- [ ] Publish the v2.0.1 release candidate after pushing its version bump and changelog. Do not publish before reviewing the final diff.
- [x] Prepared `../CIVITAI_V2_LISTING_DRAFT.md` and identified the V2 workflow file for upload.
- [ ] Civitai upload is separate. Apex said Civitai assistance is not needed and will handle any listing update.

## Publish sequence

1. **Done:** updated and verified the `main` branch of [ApexLightSpeed/ComfyUI_ApexPipeline](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline).
2. **Submitted, pending Registry review:** GitHub Actions run `41180870668` published `apex-pipeline` v2.0.0. Wait for status to move from Pending, then verify the public listing. Do not rerun; published versions are immutable.
3. **Prepare v2.0.1:** review the fresh-version changelog and starter-cleanliness notes, push the versioned package source, then dispatch the existing **Publish to Comfy Registry** workflow once.
4. **Civitai is separate:** the description and workflow are prepared at `../CIVITAI_V2_LISTING_DRAFT.md` and `workflows/Apex Generator V2.json`; Apex said assistance with Civitai is not needed.

Apex authorized GitHub and Registry publishing on 2026-10-31. The Registry version is submitted and pending review; do not rerun the workflow. Keep Civitai outside this assistance scope.
