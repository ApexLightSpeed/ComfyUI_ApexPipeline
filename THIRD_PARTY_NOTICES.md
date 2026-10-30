# Third-party notices

Apex Pipeline is a separate custom-node package. The Generator workflow depends on these separately installed projects; no source code from their node packs is bundled here.

- **ComfyUI LC123 Nodes** by lonecatone23 — provides the original LCOptimizer engine (when installed), LCSpeedBoostKSampler, and LC Save Image / metadata nodes used by the workflow. Repository: https://github.com/lonecatone23/ComfyUI_LC123_nodes. The upstream repository identifies its license as MIT.
- **Pixaroma ComfyUI nodes** — provides the LoRA stack, prompt, seed, resolution, and runtime helper nodes used by the workflow. Install from the publisher's distribution; no Pixaroma code is bundled here.

ComfyUI core loaders and public node APIs are used through the installed ComfyUI runtime. No model weights, checkpoints, LoRAs, or VAE files are included.
