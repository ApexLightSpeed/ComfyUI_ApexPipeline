# Apex Pipeline V2

Apex Generator V2 keeps the usual Krea 2 image workflow in four Apex nodes. The controls, saved output and large preview stay on one clear row, so you can focus on the image instead of wiring a long chain of small utility nodes.

## The four nodes

1. **Apex Model Matrix** loads the diffusion model, text encoder and VAE. It uses the installed LC123 optimizer when available.
2. **Apex Generation Nexus** holds the prompt, canvas, seed, sampler and optional LoRAs. The LoRA stack supports up to 64 entries, with independent model and CLIP strengths, reordering, enable/disable, duplicate and remove controls. Strength has a −5 to +5 slider, 0.05 step buttons and a number field for any finite value.
3. **Apex Archive** saves the image and embeds workflow, generation settings and resource hashes through LC123. It includes the run timer and one adjustable Last save preview.
4. **Apex Image Preview** shows the generated image on its own. Drag its lower-right corner to resize it.

The **Find triggers** button checks selected LoRA metadata on your computer first. If that has no trigger words, it can look up the file's SHA-256 against Civitai's public model index. The LoRA file is not uploaded. Results appear as buttons you can click to copy. Civitai may not have a match for every file.

The workflow uses ComfyUI's normal model, image and widget data. The Apex surfaces only change how the controls look and are arranged. The sampler, model loading, decode and save paths remain in the node execution graph.

## Install

1. Install **ComfyUI_LC123_nodes** with ComfyUI Manager, or follow its instructions at [the LC123 GitHub page](https://github.com/lonecatone23/ComfyUI_LC123_nodes). Apex uses LC123 for Speed Boost and metadata-aware image saving; the model optimizer uses LC123 when available and has a native fallback.
2. Install **Apex Pipeline** with ComfyUI Manager, or use a terminal in your active `ComfyUI/custom_nodes` folder:

   ```powershell
   git clone https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline.git
   ```

   If `ComfyUI_ApexPipeline` is already there, open that folder in a terminal and run `git pull` instead of cloning a second copy.
3. Restart ComfyUI. If you added or updated model files, restart once more so the pickers see them.
4. Open `workflows/Apex Generator V2.json` in ComfyUI.

For ComfyUI Desktop, use the `custom_nodes` folder belonging to the installation you actually run. Avoid keeping duplicate Apex Pipeline folders active at the same time.

## Model files

Use model files compatible with Comfy-Org's [Krea 2 release](https://huggingface.co/Comfy-Org/Krea-2), and follow that repository's model license. The standard Turbo setup uses:

| File | ComfyUI folder |
| --- | --- |
| `krea2_turbo_fp8_scaled.safetensors` | `models/diffusion_models/` |
| `qwen3vl_4b_fp8_scaled.safetensors` | `models/text_encoders/` |
| `qwen_image_vae.safetensors` | `models/vae/` |

You can pick other compatible files in Apex Model Matrix. The supplied workflow starts with a blank prompt and no LoRAs, so it will not ask you to download someone else's LoRA collection.

## First run

1. In **Apex Model Matrix**, choose your Krea 2 model, text encoder and VAE.
2. Type a prompt in **Apex Generation Nexus**. The starter uses 896 × 1344, batch 1, a random seed, 8 steps, CFG 1, Euler/simple and LC Speed Boost.
3. Add LoRAs only if you need them. Adjust model and CLIP strengths independently; use **Find triggers** for an optional trigger-word lookup.
4. Choose the filename, folder, image format and metadata options in **Apex Archive**.
5. Queue the prompt. The Archive reports the save and shows a small preview; Apex Image Preview shows the same image larger.

## Notes

- **ComfyUI_LC123_nodes is required.** Apex calls its installed optimizer and save nodes; their source code is not copied into this repository.
- Pixaroma is not required by the V2 graph.
- The Apex preview is separate from saving: Archive writes the file, and Image Preview displays the generated image.
- Find triggers runs only when you press its button. Its public lookup sends a file hash and LoRA name to Civitai, never the LoRA weights.
- If something fails, include your ComfyUI version and the complete console traceback in a GitHub issue. Do not include API keys or access tokens.

## License

Apex Pipeline is MIT licensed; see [LICENSE](LICENSE). LC123 and the model files retain their own licenses. This repository does not redistribute their code or model weights.

## Publishing a Registry version

The Registry package is `apex-pipeline` under publisher `apexlightspeed`. To publish, create a Registry personal access token, add it to this GitHub repository as the Actions secret `REGISTRY_ACCESS_TOKEN`, then run **Actions → Publish to Comfy Registry**. The action reads the version from `pyproject.toml`; published versions cannot be overwritten, so increase that version for each release.
