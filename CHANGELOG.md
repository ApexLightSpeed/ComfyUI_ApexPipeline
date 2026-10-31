# Changelog

## 2.0.4 — Automatic Civitai workflow attribution

- Adds the Apex Generator workflow AIR to saved PNG Civitai resource metadata automatically.
- Hides the manual AIR field in Apex Archive. The separate Embed workflow checkbox remains visible and enabled by default so the ComfyUI graph is still embedded.
- Keeps files in ComfyUI's normal `output/Apex` folder. Firefox uploaded from the shared folder; Opera GX produced a browser file-access warning.
- No model loading, LoRA, sampling, decode, image, or save-path behavior changed beyond adding the workflow resource reference.

## 2.0.3 — Registry identity in the starter workflow

- Adds Comfy Registry package identity and package version metadata to each Apex node in the clean V2 starter. ComfyUI can now associate missing Apex node types with the `apex-pipeline` pack instead of grouping them as “Unknown pack.”
- Updates the workflow builder so regenerated templates retain the same identity.
- Adds a release assertion covering the pack identity on all four Apex nodes.
- No node execution or sampling behavior changes.

# Changelog

## 2.0.2 — LoRA stack reliability and control polish

- Fixes fixed-seed cache identity so adding, enabling, disabling, reordering, or changing LoRA strengths invalidates stale generation output; enabled file size and modification changes also refresh the LoRA patch.
- Replaces each LoRA checkbox with an accessible, keyboard-focusable ON/OFF switch and clearer active/bypassed state.
- Shows the number of active LoRAs and explains that changes apply on the next queued generation.
- Keeps the existing ordered stack, independent model/CLIP strengths, trigger lookup, sampler, and model patch implementation.

## 2.0.1 — V2 release correction

- Reissues the current V2 package as a fresh Registry version so ComfyUI users can update to the intended frontend and starter workflow.
- States explicitly that the starter saves no model filenames or LoRA selections; users choose files from their own model folders.
- Keeps the LoRA model and CLIP controls at −5…+5, with ±0.05 buttons and direct numeric entry for any finite value.
- Preserves the four-node layout, image preview, model loading, sampling, decode, and save behavior.

## 2.0.0 — Apex Generator V2

- Ships the four-node Apex Model Matrix → Apex Generation Nexus → Apex Archive → Apex Image Preview workflow.
- Aligns all four nodes in a compact row in the starter workflow, following Apex's supplied layout reference.
- Adds per-LoRA model and CLIP strength controls with a −5 to +5 slider, 0.05 step buttons, and direct numeric entry for any finite strength.
- Rewrites installation and first-run instructions in plain language; documents model files, LC123 dependency, trigger lookup and previews.
- Keeps the blank prompt and empty LoRA stack in the starter. No model or image output behavior was changed in this UI/layout pass.

## Earlier V2 development notes — Infernal artwork and dedicated preview

- Replaces the skull header treatment with image crops adapted from Apex's supplied infernal banner and metal-frame artwork. The text-free frame texture continues through the connector band to blend the header into the socket area.
- Adds **Apex Image Preview**, a minimal image-only node with a corner drag handle; it receives the Generation Nexus image directly while Apex Archive saves the same image independently.
- Suppresses ComfyUI's native image thumbnail on Apex Archive, leaving its integrated Last save image as the single small preview in that node.
- Leaves model loading, sampling, decoding, metadata, and archive save behavior unchanged; the preview uses ComfyUI's built-in preview image writer.

## V2 development note — Apex surface refinement

- Renames the readable node headers to Apex Model Matrix, Apex Generation Nexus, and Apex Archive while preserving the underlying node class IDs and graph sockets.
- Replaces the abstract signal header with original, angled crimson skull artwork and a distressed condensed title; shifts the header and controls toward black with restrained deep-red accents.
- Removes the port-band grid, routing label, and diagonal header overlay so the socket area blends into the darker header without the previous tech-line motif.
- Makes LoRA strengths explicit model/clip sliders and sorts the picker for faster scanning. Adds a single on-demand trigger lookup: local safetensors metadata first, then Civitai trained words from a public SHA-256 match, shown as copyable chips.
- Guards unchanged ResizeObserver measurements from repeatedly committing node geometry during zoom. Intended to address intermittent zoom flicker; verify in the live ComfyUI frontend before release.
- Keeps the Apex Archive's Last save preview as the single canvas preview and adds a workflow-persisted size slider.
- Leaves sampler, conditioning, model load, VAE decode, and LC123 metadata/saver implementations unchanged.
- Tunes remaining canvas accent strokes to the deeper crimson palette in Apex's latest art direction.

## V2 development candidate — three-node layout (superseded)

- Replaces the multi-node Generator canvas with three Apex nodes: Model Engine, Generation Core, and Output / Provenance.
- Replaces ComfyUI's standard title bar, node frame and widget stack with full-bleed ApexLightSpeed surfaces; the whole node body and outline use the near-black and red signal system.
- Moves prompt, canvas size, batch, seed, and sampling controls into Apex Generation Core; retains Pixaroma's ordered 64-row LoRA capacity with per-row enable, trigger, strength, reorder, duplicate and remove controls.
- Adds LC Save Metadata and LC Save Image controls to Apex Output, backed by LC123's installed metadata builder and image saver; no LC123 source is bundled.
- Folds the whole-workflow run timer into Apex Output and preserves the last completed duration in the workflow.
- Keeps the existing sampler and VAE decode path and adds an identity-keyed LoRA cache for conditioning reuse.
- Adds a clean three-node V2 workflow without a separate recipe, preview, metadata, or image-saver node. This candidate still needs live frontend and generation validation.

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
