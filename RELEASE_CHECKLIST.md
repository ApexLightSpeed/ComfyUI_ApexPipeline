# Apex Generator V2 release checklist

Current package: `apex-pipeline` v2.0.2. The Registry release source is GitHub commit `a0ed570de3aa30210cd05fbf1db4c19def55516f`. Documentation-only follow-up commits do not alter the package.

## Package and workflow

- [x] Four Apex nodes: Model Matrix, Generation Nexus, Archive, Image Preview; 17 valid links.
- [x] Public starter has a blank prompt and empty LoRA stack, with no serialized personal model or LoRA values.
- [x] Fixed-seed cache fingerprint includes the LoRA stack and enabled file revisions/strengths; random-seed runs still re-execute.
- [x] Per-LoRA checkbox replaced by an accessible ON/OFF switch. Active count and next-queued-run guidance are visible.
- [x] Independent model/CLIP strength sliders, ±0.05 controls and manual numeric entry remain available.
- [x] README, changelog, dependency notes and simple installation steps are included.
- [x] Registry archive v2.0.2 inspected (18 entries); starter workflow and updated Python/JS sources present.

## Verification

- [x] `node --check web/apex.js` passed.
- [x] Workflow JSON parsed; four Apex node types, 17 links and no serialized widget values confirmed.
- [x] Comfy Desktop restarted after preserving the active local workflow separately.
- [x] Live ComfyUI showed the new switches and all four Apex node types registered.
- [x] Post-restart generation with the saved LoRA stack completed successfully; queue is idle.
- [ ] Python pytest suite was not run: Python and pytest are unavailable in the shell used for this release work. The backend loaded and executed the workflow, but this does not replace the test suite.

## Publication status

- [x] GitHub source commit `a0ed570de3aa30210cd05fbf1db4c19def55516f` pushed.
- [x] GitHub Actions run [41185990694](https://github.com/ApexLightSpeed/ComfyUI_ApexPipeline/actions/runs/41185990694) succeeded.
- [x] Comfy Registry v2.0.2 uploaded (version ID `6e8cd189-2b26-4ab6-901b-ccc68b7c9168`).
- [ ] Registry review is pending. Do not republish v2.0.2; published versions are immutable.
- [ ] Civitai remains outside this assistance scope; Apex will handle that listing.

The personal test workflow is saved locally as `Apex Generator V2 - Recovery 2026-10-31`. Never distribute it; use only `workflows/Apex Generator V2.json` for the clean public starter.
