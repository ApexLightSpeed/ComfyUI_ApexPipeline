# Apex Pipeline 0.1.1 — Generator-only patch release checklist

## Registry identity and publishing

- [x] GitHub repository: https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline
- [x] Comfy Registry Publisher ID: `apexlightspeed`
- [x] Package ID: `apex-pipeline`
- [ ] Commit and push the 0.1.1 changes to GitHub.
- [ ] Publish version 0.1.1 with `comfy node publish` using the Registry token interactively.

## Generator-only acceptance

- [x] Exactly one workflow is shipped: `Apex Generator v2.json`.
- [x] Exactly three Apex nodes are registered: Apex Model Optimizer, Apex Recipe, and Apex Generate.
- [x] Workflow defaults to `krea2_turbo_fp8_scaled.safetensors`, `qwen3vl_4b_fp8_scaled.safetensors`, and `qwen_image_vae.safetensors`.
- [x] Spectrum defaults to `off` in both the workflow and newly-created Apex Model Optimizer nodes.
- [x] Pixaroma LoRA state has an empty `loras` list; no specific LoRA is preselected.
- [ ] Install Registry version 0.1.1 over the prior 0.1.0 install and verify all three Apex nodes register.
- [ ] Test the three Krea 2 model dropdown selections with the standard base files installed.
- [ ] Queue a generation and verify image output plus PNG prompt / seed / sampler / scheduler metadata.
- [ ] Confirm no missing-LoRA download prompts appear on workflow open.

## External dependencies

- LC123 remains an external dependency for the optimizer engine, Speed Boost, and LC Save Image / metadata nodes.
- Pixaroma remains an external dependency for the LoRA stack, prompt, seed, resolution, and runtime nodes.
- No checkpoint, text encoder, VAE, or LoRA weights are bundled by Apex.

## Release scope

This remains a Generator-only package. Refine, Context Repair, Upscale, and Detailer are not included.
