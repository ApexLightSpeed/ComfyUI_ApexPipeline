# Apex Pipeline V1 (1.0.0) — Generator-only release checklist

## Registry identity and publishing

- [x] GitHub repository: https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline
- [x] Comfy Registry Publisher ID: `apexlightspeed`
- [x] Package ID: `apex-pipeline`
- [ ] Commit and push the 1.0.0 changes to GitHub.
- [ ] Publish version 1.0.0 with `comfy node publish` using the Registry token interactively.

## Generator-only acceptance

- [x] Exactly one workflow is shipped: `Apex Generator V1.json`.
- [x] Exactly three Apex nodes are registered: Apex Model Optimizer, Apex Recipe, and Apex Generate.
- [x] Workflow selects the standard Krea 2 Turbo diffusion model, Qwen3-VL 4B text encoder, and Qwen Image VAE.
- [x] Spectrum is `off` in the workflow and newly-created Apex Model Optimizer nodes.
- [x] Pixaroma LoRA state is empty in the widget, named snapshot, and serialized frontend state.
- [x] Prompt is blank in the widget, named snapshot, and serialized frontend state.
- [x] Seed widget and saved frontend state agree on Random mode.
- [x] Model Optimizer named widget metadata matches its visible widget values.
- [x] Obsolete workflow v8 and Refine-stage notes are removed.
- [ ] Install Registry version 1.0.0 over the prior version and verify all three Apex nodes register.
- [ ] Queue a generation and verify image output plus PNG prompt / seed / sampler / scheduler metadata.
- [ ] Confirm no missing-LoRA download prompts appear on workflow open.

## External dependencies

- LC123 remains an external dependency for the optimizer engine, Speed Boost, and LC Save Image / metadata nodes.
- Pixaroma remains an external dependency for the LoRA stack, prompt, seed, resolution, and runtime nodes.
- No checkpoint, text encoder, VAE, or LoRA weights are bundled by Apex.
- LC123 and Pixaroma source code are not copied into this repository.

## Release scope

This remains a Generator-only package. Refine, Context Repair, Upscale, and Detailer are not included.
