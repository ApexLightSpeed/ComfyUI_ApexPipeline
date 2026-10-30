# Apex Pipeline 0.1.0 — Generator-only release checklist

## Identity and publishing

- [ ] Create/confirm the GitHub repository and replace `REPLACE_WITH_GITHUB_OWNER` in `pyproject.toml`.
- [ ] Create the Comfy Registry publisher and replace `REPLACE_WITH_COMFY_REGISTRY_PUBLISHER_ID` with the exact PublisherId.
- [ ] Confirm the Registry package ID `apex-pipeline` is available before first publication.
- [ ] Confirm the MIT license and copyright holder are correct.
- [ ] Build the Registry package from the repository root and run `comfy node publish` using the publisher token interactively.

## Generator-only acceptance

- [ ] Confirm the release contains exactly one workflow: `Apex Generator v2.json`.
- [ ] Confirm exactly three Apex nodes are registered: Apex Model Optimizer, Apex Recipe, and Apex Generate.
- [ ] Install into a clean ComfyUI environment and verify all Apex nodes register.
- [ ] Test model, text-encoder, and VAE dropdowns with the target Krea 2 files.
- [ ] Test the Apex Model Optimizer with LC123 installed and verify its goal, Auto/Manual, and advanced controls remain available.
- [ ] Test the native Krea 2 fallback without LC123 (optional; the workflow itself still needs LC123/Pixaroma nodes).
- [ ] Queue a Generator run with Speed Boost enabled and disabled, and compare output with the expected settings.
- [ ] Verify four LoRA names/strengths/tags/hashes and checkpoint provenance in the saved PNG metadata.
- [ ] Verify seed, steps, CFG, sampler, scheduler, prompt and dimensions are present in the saved PNG.
- [ ] Verify the workflow has one image-save path and no Refine, Context Repair, Upscale, or Detailer tabs/files.

## Not claimed as completed by static packaging

- The package has not been pushed to GitHub or published to the ComfyUI Registry.
- No ComfyUI Desktop runtime is available in this packaging environment. A dropdown UI smoke test and actual generation remain required before the public release is considered verified.
