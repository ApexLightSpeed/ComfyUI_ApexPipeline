# Third-party notices

Apex Pipeline is a separate custom-node package. The Generator workflow depends on the following separately installed projects; no implementation source from their node packs is bundled or redistributed by Apex.

- **ComfyUI LC123 Nodes** by lonecatone23: https://github.com/lonecatone23/ComfyUI_LC123_nodes. LC123 supplies the LCOptimizer engine (when installed), LCSpeedBoostKSampler, and LC Save Image / metadata nodes used by the workflow. Apex dynamically discovers and calls the installed LCOptimizer node through ComfyUI's node registry and uses a temporary, scoped adapter for model-list enumeration; Apex does not include LC123's optimizer implementation. The upstream project identifies its license as MIT; consult its repository and `LICENSE` file for the current terms.
- **Pixaroma ComfyUI nodes**: separately installed dependency providing the LoRA stack, prompt, seed, resolution, and runtime helper nodes. No Pixaroma code is bundled or redistributed by Apex. Refer to the publisher's distribution for its current license and terms.
- **ComfyUI**: Apex uses public runtime node mappings and APIs supplied by the installed ComfyUI distribution.

Apex's own source is distributed under the MIT License in `LICENSE`. These notices describe runtime dependencies and do not grant rights to redistribute their code or model weights. No checkpoints, text encoders, VAEs, or LoRAs are included.

### LC123 upstream license attribution

The LC123 upstream repository's current `LICENSE` identifies the project as MIT, with this copyright notice:

> Copyright (c) 2026 lonecatone23

The MIT license text is available at: https://github.com/lonecatone23/ComfyUI_LC123_nodes/blob/main/LICENSE

This attribution is informational for the separately installed LC123 dependency. Apex does not redistribute LC123 source files.
