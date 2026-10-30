# Changelog

## 0.1.1 — Generator defaults and compatibility update

- Defaulted the Apex Model Optimizer Spectrum option to `off` for Krea 2 compatibility.
- Selected the standard Comfy-Org Krea 2 Turbo FP8 diffusion model, Qwen3-VL 4B FP8 text encoder, and Qwen Image VAE in the shipped workflow.
- Removed all preconfigured third-party LoRAs from the Pixaroma stack; the stack now starts empty and does not request LoRA downloads.
- Set the permanent Comfy Registry Publisher ID and the actual GitHub repository URLs in `pyproject.toml`.
- Removed the unsupported generic GPU environment classifier from package metadata.

# Changelog

## 0.1.0 — Generator-only first public release

- Published one workflow: Apex Generator v2.
- Limited registered Apex nodes to Apex Model Optimizer, Apex Recipe, and Apex Generate.
- Added the Apex-owned Krea 2 Model Optimizer adapter with constrained LC123 model-list access.
- Preserved the Generator's model, LoRA stack, prompt, seed, resolution, sampler, metadata, and save graph.
- Added Registry metadata, MIT license, Generator-specific documentation, and Model Optimizer adapter tests.
- Excluded Refine, Context Repair, Upscale, and Detailer nodes and workflows from this release.
