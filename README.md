# Apex Generator V1

I built Apex Generator to make Krea 2 Turbo easier to run in ComfyUI. The workflow connects the model loader, prompt, optional LoRA stack, sampler and PNG metadata saver in one place.

This repository contains the Apex nodes and one workflow: **Apex Generator V1**. It does not contain model weights or third-party node packs.

## What you need

- A working ComfyUI installation with current Krea 2 support. If you still need ComfyUI, start at the [official download page](https://www.comfy.org/download).
- The three model files listed under [Download the models](#download-the-models).
- The LC123 and Pixaroma custom nodes. They are separate projects and must be installed separately.
- Git, if you use the manual install steps below.

**For the V1 workflow, use the Git install below.** The ComfyUI Registry copy is still v0.1.1 and does not include this V1 workflow yet.

## Install the nodes

The V1 workflow uses nodes from all three repositories below. In a terminal, change to your ComfyUI `custom_nodes` folder and clone each project there:

```bash
cd /path/to/ComfyUI/custom_nodes

git clone https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline.git
git clone https://github.com/lonecatone23/ComfyUI_LC123_nodes.git
git clone https://gitlab.com/pixaroma/comfyui-pixaroma.git
```

On Windows, the folder is usually inside your ComfyUI install, for example:

```powershell
cd "C:\path\to\ComfyUI\custom_nodes"
```

Replace the example path with your actual ComfyUI location, then run the three `git clone` commands. If you already have one of these folders, do not clone it again; update that folder using the instructions from its project instead.

Close and restart ComfyUI after installing the nodes. If Pixaroma nodes appear blank or missing after an update, refresh the ComfyUI page with **Ctrl+Shift+R**.

### What each node pack provides

- **Apex Pipeline** provides Apex Model Optimizer, Apex Recipe and Apex Generate.
- **LC123** provides the image saver and metadata nodes used by this workflow, plus the Speed Boost sampler and optimizer engine when available. The Apex optimizer has a native loader fallback, but LC123 is still needed for the workflow's save stage.
- **Pixaroma** provides the LoRA stack, prompt, seed, resolution and run timer nodes.

These are independent projects. Apex does not copy or redistribute their code. If you prefer ComfyUI Manager, install the same projects there and check that the node names above are available; the Pixaroma Registry listing may lag behind its upstream release.

## Download the models

Download these files from the [Comfy-Org Krea 2 model repository](https://huggingface.co/Comfy-Org/Krea-2). The Krea 2 files have their own license; please read and accept it on Hugging Face before downloading.

| File | Put it in |
|---|---|
| [krea2_turbo_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/Krea-2/blob/main/diffusion_models/krea2_turbo_fp8_scaled.safetensors) | `ComfyUI/models/diffusion_models/` |
| [qwen3vl_4b_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/Krea-2/blob/main/text_encoders/qwen3vl_4b_fp8_scaled.safetensors) | `ComfyUI/models/text_encoders/` |
| [qwen_image_vae.safetensors](https://huggingface.co/Comfy-Org/Krea-2/blob/main/vae/qwen_image_vae.safetensors) | `ComfyUI/models/vae/` |

Create a folder if it is missing. Restart ComfyUI after adding the files so the model lists refresh.

## Open the workflow

1. Download [`Apex Generator V1.json`](workflows/Apex%20Generator%20V1.json) from this repository.
2. Open it in ComfyUI, or drag the JSON file onto the ComfyUI canvas.
3. Enter a prompt and press **Queue Prompt**.

The workflow opens with an empty LoRA stack, a blank prompt and a random seed. No author-specific LoRAs are needed. Add your own LoRAs in the Pixaroma stack when you want to use them; Apex Recipe reads that live stack and records LoRA names, strengths and Civitai-compatible hashes in the PNG metadata.

The defaults are 8 steps, CFG 1, Euler and the simple scheduler. The workflow saves one PNG per run. Keep the PNG intact when uploading it to Civitai so its embedded generation metadata stays available.

## If something is missing

- **Red or missing nodes:** install the Apex, LC123 and Pixaroma node packs above, restart ComfyUI, then reload the workflow.
- **Model names are missing from Apex Model Optimizer:** check the three folder locations above and restart ComfyUI.
- **The LC123 optimizer picker fails:** include the full ComfyUI console traceback in a bug report. The Apex adapter narrows model discovery, but the fallback loader does not reproduce LC123's hardware-aware optimization patches.
- **PNG does not show the expected Civitai details:** use the PNG produced by the workflow without converting or re-saving it in another application.

For support, include your ComfyUI version, operating system, the node that failed and the complete console traceback. Never include API keys or access tokens.

## License and project scope

Apex Pipeline is licensed under MIT; see [LICENSE](LICENSE). The Krea 2 model files and the LC123 and Pixaroma node packs are governed by their respective projects' terms. No model weights or third-party source code are included here.

This repository is for the Generator workflow only. Refine, Context Repair, Upscale and Detailer workflows are separate projects and are not part of this package.
