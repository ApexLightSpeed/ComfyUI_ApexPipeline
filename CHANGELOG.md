# Changelog

## 1.0.0 — Apex Generator V1

- Establishes a coordinated V1 release name for the Generator-only workflow and the three Apex nodes.
- Ships a fresh workflow with an empty LoRA stack, blank prompt, Random seed, standard Krea 2 Turbo model files, and Spectrum off.
- Preserves Apex node class identifiers, graph connections, sampling settings, LoRA metadata handling, PNG metadata path, and third-party runtime dependencies.

## 0.1.1 — Generator defaults and compatibility update

- Defaulted the Apex Model Optimizer Spectrum option to `off` for Krea 2 compatibility.
- Selected the standard Krea 2 Turbo FP8 diffusion model, Qwen3-VL 4B FP8 text encoder, and Qwen Image VAE.
- Set the Comfy Registry Publisher ID and GitHub repository URLs.

## 0.1.0 — Generator-only first public release

- Published one Generator workflow and the three Apex nodes used by it.
- Added the Apex-owned Krea 2 Model Optimizer adapter with constrained LC123 model-list access.
- Preserved the model, LoRA stack, prompt, seed, resolution, sampler, metadata, and save graph.
- Excluded Refine, Context Repair, Upscale, and Detailer workflows and nodes.