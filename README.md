# Apex Pipeline — Generator Edition

**This Generator-only package contains one workflow: Apex Generator.** The default workflow uses the official base Krea 2 Turbo model files, starts with an empty Pixaroma LoRA stack, and preserves Civitai-compatible recipe metadata and PNG saving.

- **Release:** 0.1.1
- **Publisher:** ApexLightSpeed (`apexlightspeed`)
- **Workflow included:** `Apex Generator v2.json` — no Refine, Context Repair, Upscale, or Detailer workflow tabs are included.
- **Apex nodes registered:** Apex Model Optimizer, Apex Recipe, and Apex Generate.
- **Python dependencies:** none added by this package; ComfyUI provides the runtime libraries.

## What this release includes

| Apex node | Role in the Generator workflow |
|---|---|
| **Apex Model Optimizer** | Loads the Krea 2 diffusion model, Qwen3-VL text encoder, and VAE. When LC123 is installed, it delegates to its optimizer engine through Apex's constrained model-list adapter. |
| **Apex Recipe** | Reads the live upstream LoRA stack. The shipped workflow starts empty and has no LoRA download requirements; if users add their own LoRAs, Apex builds `<lora:name:model:clip>` tags, calculates Civitai AutoV2 hashes, and records checkpoint provenance. |
| **Apex Generate** | Encodes the prompt, creates the latent, samples, decodes, and outputs generation settings and metadata for the saver. It uses LC123 Speed Boost when available and otherwise falls back to ComfyUI's core sampler. |

The included workflow also uses third-party Pixaroma and LC123 nodes. They are not bundled or redistributed by Apex.

## Install

### ComfyUI Registry / Manager

After publication, search for **Apex Pipeline** in ComfyUI Manager, install it, and restart ComfyUI.

### Manual installation

1. Copy the `ComfyUI_ApexPipeline` folder into `ComfyUI/custom_nodes/`.
2. Confirm the final path is `ComfyUI/custom_nodes/ComfyUI_ApexPipeline/__init__.py`.
3. Restart ComfyUI completely.
4. Check the startup console for `[Apex Pipeline]` import errors.
5. Open the sole included workflow, `workflows/Apex Generator v2.json`.

## External node requirements

- **ComfyUI LC123 Nodes:** used for the original optimizer execution engine when present, LC Speed Boost sampling, and LC Save Image / metadata nodes in the Generator graph. Apex does not install or update LC123.
- **Pixaroma nodes:** used for the live LoRA stack, prompt helper, seed, resolution, and runtime display in the Generator graph. Apex does not bundle Pixaroma code.
- **ComfyUI build with native Krea 2 / `krea2` CLIP support:** needed by the Model Optimizer's native fallback loader.

Apex does not include checkpoints, LoRAs, VAE files, or other model assets. The workflow does not bundle or select any third-party LoRAs by default; users may add their own.

## Model locations

| Component | ComfyUI model folder |
|---|---|
| Krea 2 Turbo diffusion model: `krea2_turbo_fp8_scaled.safetensors` | `models/diffusion_models/` |
| Qwen3-VL 4B text encoder: `qwen3vl_4b_fp8_scaled.safetensors` | `models/text_encoders/` |
| Qwen Image VAE: `qwen_image_vae.safetensors` | `models/vae/` |

After adding model files, refresh the model list if your ComfyUI build offers that control, or restart ComfyUI.

The workflow selects these three standard Krea 2 Turbo files by default. Spectrum is explicitly set to `off` in the optimizer widget; users can change it later. The Pixaroma LoRA stack starts empty, so no author-specific LoRA files are requested.

## Model Optimizer picker and MemoryError

The Apex Model Optimizer is an Apex-owned node. Its LC123 adapter temporarily constrains the LC optimizer's file-list function to ComfyUI's registered, cached model categories and avoids the LC fallback recursive GGUF scan that follows directory links. The adapter is restored after each call; it does not permanently modify LC123.

When LC123 is present, the node delegates its optimization run to the LC123 engine so its original goal, speed-up, and advanced controls remain available. When LC123 is absent or its adapter cannot be used, Apex provides a native Krea 2 loader; the native fallback does not emulate LC123's hardware-aware optimization patches.

The browser's `500: Internal Server Error (MemoryError)` does not reveal the exact failing line. The constrained adapter addresses a plausible source in file discovery, but a clean ComfyUI runtime test on the target machine is still required to confirm the dropdown behaves correctly there. If it still fails, include the full ComfyUI console traceback in a bug report.

## Generation metadata

Apex Recipe records checkpoint provenance and, when users add LoRAs to the empty-by-default Pixaroma stack, their trigger tags, strengths, and Civitai AutoV2 hashes. Apex Generate provides the prompt plus seed, steps, CFG, sampler, scheduler, and extra settings. The workflow routes these values through the single LC Save Image Metadata / LC Save Image stage. Keep the saved PNG intact when uploading to Civitai so its embedded metadata remains available for parsing.

## Support

For a bug report, include the ComfyUI version, Python version, Apex Pipeline version, the affected Apex node, and the complete console traceback. Do not include API keys or access tokens.

## Release scope

This is intentionally a **Generator-only** first release. Apex Refine, Context Repair, Upscale, and Detailer remain separate development work and are not registered or distributed in this package.

## License

MIT. See `LICENSE`.
