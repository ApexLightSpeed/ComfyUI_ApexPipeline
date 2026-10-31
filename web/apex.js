// Apex Pipeline V2 · custom node frame and whole-node control surface.
// ComfyUI widgets remain the serialized/execution backing; LiteGraph draws each Apex shell.
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// V2 uses a dedicated generation node. The loader and archive classes are also
// present in V1, so only activate this surface when the complete V2 graph is
// loaded. This keeps the V1 workflow's names, frame and output behavior intact.
const TYPES = new Set(["ApexModelOptimizer", "ApexLoraGenerationCore", "ApexOutput", "ApexPreview"]);
const HEADER_ART_URL = new URL("./apex-infernal-header.png", import.meta.url).href;
const PORT_TEXTURE_URL = new URL("./apex-infernal-port-texture.png", import.meta.url).href;
const PORT_TEXTURE = new Image();
PORT_TEXTURE.onload = () => app.canvas?.setDirty?.(true, true);
PORT_TEXTURE.src = PORT_TEXTURE_URL;
const THEME = `
.apx-shell{box-sizing:border-box;width:calc(100% + 20px);margin-left:-10px;padding:0;background:transparent;color:#eeeef2;font:12px Inter,Arial,sans-serif;overflow:visible}
.apx-head{height:104px;position:relative;overflow:hidden;background-color:#050506;border:0;border-bottom:1px solid #641014;border-radius:0;margin:0 0 10px;padding:14px 18px;box-sizing:border-box}
.apx-preview-only{position:relative;box-sizing:border-box;width:100%;height:100%;min-height:180px;overflow:hidden;background:#060506;border:1px solid #54151a;border-radius:5px}.apx-preview-only img{display:block;width:100%;height:100%;object-fit:contain;background:#060506}.apx-preview-empty{position:absolute;inset:0;display:grid;place-items:center;color:#7e7075;font:10px ui-monospace,Consolas,monospace;letter-spacing:.4px;pointer-events:none}.apx-preview-grip{position:absolute;right:2px;bottom:2px;width:20px;height:20px;border:0;border-radius:3px;background:linear-gradient(135deg,transparent 42%,#9e252c 43%,#9e252c 49%,transparent 50%,transparent 59%,#c13a40 60%,#c13a40 66%,transparent 67%);cursor:nwse-resize;touch-action:none;z-index:2}.apx-preview-grip:hover{filter:brightness(1.5)}
.apx-preview-only img[hidden],.apx-preview-empty[hidden],.apx-preview[hidden]{display:none!important}
.apx-head:before{content:"";position:absolute;inset:0;background-image:linear-gradient(90deg,#050506 0%,#050506f8 34%,#080607e8 58%,#080607a8 100%),url("${HEADER_ART_URL}"),url("${PORT_TEXTURE_URL}");background-position:center,25% 58%,center;background-size:100% 100%,auto 245%,cover;background-repeat:no-repeat;opacity:.98;pointer-events:none}
.apx-mark{position:relative;z-index:1;display:flex;align-items:center;gap:7px;color:#f0e8e8;font:700 10px Arial,sans-serif;letter-spacing:1.2px}.apx-led{width:7px;height:7px;border-radius:50%;background:#d9232b;box-shadow:0 0 9px #c31820}
.apx-title{position:relative;z-index:1;margin-top:17px;font:900 22px/1 Impact,Haettenschweiler,"Arial Narrow Bold",sans-serif;letter-spacing:1.2px;color:#eee8e8;text-transform:uppercase;filter:url(#apx-title-grit);text-shadow:1px 1px 0 #21090b}.apx-sub{position:relative;z-index:1;margin-top:6px;color:#b9383c;font:9px monospace;letter-spacing:1px}
.apx-section{border:1px solid #353238;border-radius:7px;margin:8px 10px;padding:8px;background:linear-gradient(145deg,#121012,#0d0c0e)}.apx-section[data-accent="red"]{border-color:#641a1e}.apx-section[data-accent="cyan"]{border-color:#493034}.apx-label{display:flex;justify-content:space-between;align-items:center;margin:0 0 7px;color:#e25459;font:700 9px Arial,sans-serif;letter-spacing:.8px;text-transform:uppercase}.apx-section[data-accent="cyan"] .apx-label{color:#bb777a}
.apx-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.apx-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.apx-field{min-width:0;display:flex;flex-direction:column;gap:4px}.apx-field.wide{grid-column:1/-1}.apx-field label{color:#aaa0a4;font:9px Arial,sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.apx-input{box-sizing:border-box;width:100%;height:29px;border:1px solid #383238;border-radius:5px;background:#1a171b;color:#f0e9eb;padding:5px 8px;font:11px Arial,sans-serif;outline:none}.apx-input:focus{border-color:#c31820;box-shadow:0 0 0 1px #c3182055}.apx-input[type=number]{font-variant-numeric:tabular-nums}.select.apx-input,select.apx-input{appearance:none;padding-right:26px;background-image:linear-gradient(45deg,transparent 50%,#d35a60 50%),linear-gradient(135deg,#d35a60 50%,transparent 50%);background-position:calc(100% - 12px) 12px,calc(100% - 8px) 12px;background-size:4px 4px,4px 4px;background-repeat:no-repeat}select.apx-input option{background:#171317;color:#f4ecee}.apx-text{height:92px;resize:vertical;line-height:1.35}.apx-toggle{height:29px;display:flex;align-items:center;gap:8px;color:#ddd;font-size:10px}.apx-toggle input{accent-color:#c31820;width:15px;height:15px}.apx-foot{display:flex;justify-content:space-between;border-top:1px solid #2d2528;padding-top:7px;margin-top:8px;color:#7c7378;font:8px monospace;letter-spacing:.3px}.apx-status{color:#aaa;font:10px monospace;white-space:pre-wrap;overflow-wrap:anywhere}.apx-preview{display:block;width:100%;max-height:340px;object-fit:contain;border:1px solid #493034;border-radius:5px;background:#080809;margin-top:7px}.apx-hint{color:#898086;font:9px Arial,sans-serif;line-height:1.35;margin-top:5px}
.apx-clock-row{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:38px}.apx-clock{color:#e25459;font:700 25px/1 ui-monospace,Consolas,monospace;letter-spacing:1px;font-variant-numeric:tabular-nums}.apx-clock[data-state="running"]{color:#df565b;text-shadow:0 0 12px #c3182055}.apx-clock-state{color:#9a9095;font:9px monospace;letter-spacing:.5px;text-align:right}
.apx-lora-list{display:grid;gap:6px;max-height:390px;overflow:auto;padding-right:3px}.apx-lora-row{border:1px solid #332a2e;border-radius:6px;background:#151216;padding:6px}.apx-lora-top{display:grid;grid-template-columns:44px minmax(0,1fr) 24px 24px 24px 24px;gap:5px;align-items:center}.apx-lora-top .apx-input{height:27px}.apx-lora-fields{display:grid;grid-template-columns:minmax(0,1fr) minmax(90px,.72fr) minmax(90px,.72fr);gap:7px;margin-top:6px}.apx-lora-fields .apx-input{height:27px}.apx-lora-fields .apx-field label{font-size:8px}.apx-lora-row[data-off="true"]{opacity:.68}.apx-lora-switch{position:relative;width:42px;height:23px;padding:0 5px 0 22px;border:1px solid #5a3a3e;border-radius:999px;background:#282226;color:#aaa0a4;font:700 8px/1 Arial,sans-serif;letter-spacing:.04em;cursor:pointer;transition:background .14s,border-color .14s,color .14s}.apx-lora-switch:before{content:"";position:absolute;left:3px;top:3px;width:15px;height:15px;border-radius:50%;background:#87777b;box-shadow:0 1px 3px #0009;transition:transform .14s,background .14s}.apx-lora-switch[aria-checked="true"]{padding:0 21px 0 5px;border-color:#b52b32;background:#521419;color:#ffe5e6}.apx-lora-switch[aria-checked="true"]:before{transform:translateX(19px);background:#ff5961;box-shadow:0 0 8px #d3212a66}.apx-lora-switch:focus-visible{outline:2px solid #ee565d;outline-offset:2px}.apx-lora-helper{margin:-2px 0 6px;color:#988b90;font:9px Arial,sans-serif}.apx-mini-button,.apx-add-button{height:27px;border:1px solid #463338;border-radius:5px;background:#21191e;color:#eee4e6;font:10px Arial,sans-serif;cursor:pointer;transition:border-color .12s ease,background .12s ease,color .12s ease}.apx-mini-button:hover,.apx-add-button:hover{border-color:#c31820;background:#2c171b;color:#ff9a9e}.apx-mini-button:disabled,.apx-add-button:disabled{opacity:.36;cursor:default}.apx-lora-addbar{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:5px;margin-top:7px}.apx-lora-empty{padding:12px 8px;border:1px dashed #393036;border-radius:5px;color:#999096;text-align:center;font:10px Arial,sans-serif}
.apx-lora-heading{display:flex;justify-content:space-between;align-items:center}.apx-lora-heading-tools{display:flex;gap:7px;align-items:center}.apx-trigger-scan{height:23px;padding:0 8px;border:1px solid #8f1c23;border-radius:4px;background:linear-gradient(180deg,#8e171d,#4e0b10);color:#ffe6e7;font:700 8px/1 Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;cursor:pointer;box-shadow:inset 0 1px #ffffff20,0 0 10px #c3182022}.apx-trigger-scan:hover{border-color:#e25459;background:linear-gradient(180deg,#aa2027,#641016)}.apx-trigger-scan:disabled{opacity:.42;cursor:wait}.apx-trigger-results{display:flex;flex-wrap:wrap;gap:4px;margin-top:5px}.apx-trigger-chip{max-width:100%;padding:3px 7px;border:1px solid #7b232a;border-radius:999px;background:#351317;color:#ffdfe0;font:9px Arial,sans-serif;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.apx-trigger-chip:hover{background:#58151b;border-color:#d9444b}.apx-trigger-source{color:#97898e;font:8px monospace}.apx-trigger-status{min-height:11px;margin-top:5px;color:#bc8c90;font:9px Arial,sans-serif}
.apx-strength{display:grid;grid-template-columns:24px minmax(0,1fr) 24px 64px;align-items:center;gap:4px;height:27px}.apx-strength input[type=range]{width:100%;height:15px;accent-color:#c31820;margin:0;cursor:pointer}.apx-strength .apx-strength-step{height:23px;padding:0;border:1px solid #463338;border-radius:4px;background:#21191e;color:#f0dfe1;font:13px Arial,sans-serif;line-height:1;cursor:pointer}.apx-strength .apx-strength-step:hover{border-color:#c31820;background:#2c171b}.apx-strength .apx-strength-value{height:25px;padding:3px 5px;text-align:right;font:10px ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}.apx-preview-size-row{display:grid;grid-template-columns:auto minmax(0,1fr) 42px;align-items:center;gap:8px;color:#b5a9ad;font:9px Arial,sans-serif;margin-top:7px}.apx-preview-size-row input{width:100%;accent-color:#c31820}.apx-preview-size-row output{color:#e4d5d7;text-align:right;font:9px ui-monospace,Consolas,monospace}
.apx-resolution-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}.apx-resolution-grid .wide{grid-column:1/-1}.apx-resolution-summary{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:7px;padding:7px 9px;border:1px solid #363238;border-radius:5px;background:#111012}.apx-resolution-dims{font:700 15px ui-monospace,Consolas,monospace;color:#f2eded;font-variant-numeric:tabular-nums}.apx-resolution-aspect{width:52px;height:42px;min-width:26px;max-width:52px;border:1px solid #d24b50;border-radius:4px;background:linear-gradient(135deg,#c3182022,#621a1e11);box-shadow:inset 0 0 14px #c3182012}
`;

const META = {
  ApexModelOptimizer: { title: "APEX MODEL MATRIX", code: "01 / MODEL LOAD + OPTIMIZATION" },
  ApexLoraGenerationCore: { title: "APEX GENERATION NEXUS", code: "02 / IMAGE SYNTHESIS" },
  ApexOutput: { title: "APEX ARCHIVE", code: "03 / OUTPUT + PROVENANCE" },
};

function esc(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function slug(v) { return String(v).toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,""); }
function injectStyle() {
  if (document.getElementById("apx-v2-style")) return;
  const style = document.createElement("style"); style.id = "apx-v2-style"; style.textContent = THEME; document.head.append(style);
  const defs=document.createElementNS("http://www.w3.org/2000/svg","svg");defs.id="apx-title-filters";defs.setAttribute("aria-hidden","true");defs.style.cssText="position:absolute;width:0;height:0;overflow:hidden";
  defs.innerHTML='<filter id="apx-title-grit" x="-3%" y="-18%" width="106%" height="140%"><feTurbulence type="fractalNoise" baseFrequency="0.82" numOctaves="1" seed="23" result="grain"/><feDisplacementMap in="SourceGraphic" in2="grain" scale="0.72" xChannelSelector="R" yChannelSelector="G" result="worn"/><feComposite in="worn" in2="grain" operator="arithmetic" k1="0" k2="1" k3="-.12" k4=".05"/></filter>';
  document.body.append(defs);
}
function setValue(node, widget, value) {
  widget.value = value;
  widget.callback?.(value, app.canvas, node, [0, 0]);
  node.setDirtyCanvas?.(true, true);
}
function isV2Graph(graph=app.graph){
  const nodes=graph?._nodes||[];
  const types=new Set(nodes.map(n=>n?.comfyClass||n?.constructor?.ComfyClass||n?.type));
  return types.has("ApexModelOptimizer")&&types.has("ApexLoraGenerationCore")&&types.has("ApexOutput");
}
const ORIGINAL_TITLE_MODES=new Map();
function applyGraphTitleMode(graph=app.graph){
  const nodes=graph?._nodes||[];
  const noTitle=globalThis.LiteGraph?.NO_TITLE??1;
  const titleMode=isV2Graph(graph)?noTitle:null;
  for(const node of nodes){
    const type=node?.constructor;
    if(!type||!ORIGINAL_TITLE_MODES.has(type))continue;
    type.title_mode=titleMode===null?ORIGINAL_TITLE_MODES.get(type):titleMode;
  }
}
const MAX_LORA_ROWS=64;
function loraWidget(node,name){return (node.widgets||[]).find(w=>w.name===name);}
function readLoraRows(node){
  try{const data=JSON.parse(loraWidget(node,"lora_stack")?.value||"[]");return Array.isArray(data)?data.filter(r=>r&&typeof r==="object").slice(0,MAX_LORA_ROWS):[];}catch{return [];}
}
function loraTagText(rows){
  return rows.filter(r=>r.on&&r.name&&r.name!=="(none)").map(r=>{
    const name=String(r.name).replace(/\.(safetensors|sft|pt|ckpt|bin)$/i,"").replace(/[<>:]/g,"_");
    const model=Number(r.sm??1),clip=Number(r.sc??1);
    return `<lora:${name}:${Number.isFinite(model)?model:1}:${Number.isFinite(clip)?clip:1}>`;
  }).join(" ");
}
function writeLoraRows(node,rows){
  const stack=loraWidget(node,"lora_stack"),tags=loraWidget(node,"lora_tags");
  if(stack)setValue(node,stack,JSON.stringify(rows));
  if(tags)setValue(node,tags,loraTagText(rows));
  const count=node._apxLoraCount;if(count){const active=rows.filter(r=>r.on!==false&&r.name&&r.name!=="(none)").length;count.textContent=`${active} active · ${rows.length} / ${MAX_LORA_ROWS}`;}
  if(node._apxLoraAdd)node._apxLoraAdd.disabled=rows.length>=MAX_LORA_ROWS||node._apxLoraPicker?.value==="(none)";
}
const FOLDER_OPTION_PREFIX="__APX_FOLDER__:";
function cleanRelativePath(value){return String(value||"").replaceAll("\\","/").replace(/^\/+|\/+$/g,"");}
function folderOption(path){return FOLDER_OPTION_PREFIX+encodeURIComponent(path);}
function folderOptionPath(value){return value.startsWith(FOLDER_OPTION_PREFIX)?decodeURIComponent(value.slice(FOLDER_OPTION_PREFIX.length)):null;}
function fillFolderCombo(select,values,current,query="",browsePath="",emptyLabel="No matching files"){
  const all=[...new Set((Array.isArray(values)?values:[]).map(String))].sort((a,b)=>a.localeCompare(b,undefined,{sensitivity:"base"}));
  const q=String(query||"").trim().toLocaleLowerCase();
  const sentinels=all.filter(name=>["(none)","none","from checkpoint"].includes(name.toLocaleLowerCase()));
  const noneValue=sentinels.find(v=>v.toLocaleLowerCase()==="(none)")||sentinels.find(v=>v.toLocaleLowerCase()==="none")||"(none)";
  const files=all.filter(name=>!sentinels.includes(name)&&!name.startsWith("(no compatible files"));
  const currentPath=cleanRelativePath(current);
  const path=cleanRelativePath(browsePath);
  const prefix=path?path+"/":"";
  const currentIsSentinel=sentinels.includes(String(current));
  const currentInView=files.some(name=>{const clean=cleanRelativePath(name);return clean===currentPath&&(!q?(clean.startsWith(prefix)&&!clean.slice(prefix.length).includes("/")):clean.toLocaleLowerCase().includes(q));});
  select.replaceChildren();
  const none=document.createElement("option");none.value=noneValue;none.textContent="None";select.append(none);
  if(q){
    const crumb=document.createElement("option");crumb.disabled=true;crumb.textContent=`🔎 Matches in all folders · ${q}`;select.append(crumb);
    const matches=files.filter(name=>cleanRelativePath(name).toLocaleLowerCase().includes(q));
    if(current&&!currentIsSentinel&&!currentInView&&!matches.includes(String(current))){const selected=document.createElement("option");selected.value=String(current);selected.textContent=`Current · ${cleanRelativePath(current)}`;select.append(selected);}
    for(const name of matches){const option=document.createElement("option");option.value=name;option.textContent=cleanRelativePath(name);option.title=cleanRelativePath(name);select.append(option);}
    if(!matches.length){const empty=document.createElement("option");empty.disabled=true;empty.textContent=emptyLabel;select.append(empty);}
  }else{
    const crumb=document.createElement("option");crumb.disabled=true;crumb.textContent=path?`📂 ${path}`:"📂 All folders";select.append(crumb);
    if(path){const parent=path.includes("/")?path.slice(0,path.lastIndexOf("/")):"";const up=document.createElement("option");up.value=folderOption(parent);up.textContent="📁 ..  Parent folder";select.append(up);}
    const childFolders=new Set(),directFiles=[];
    for(const name of files){const relative=cleanRelativePath(name);if(!relative.startsWith(prefix))continue;const rest=relative.slice(prefix.length);if(!rest)continue;const slash=rest.indexOf("/");if(slash<0)directFiles.push(name);else childFolders.add(rest.slice(0,slash));}
    if(current&&!currentIsSentinel&&!currentInView){const selected=document.createElement("option");selected.value=String(current);selected.textContent=`Current · ${currentPath}`;selected.title=currentPath;select.append(selected);}
    for(const folder of [...childFolders].sort((a,b)=>a.localeCompare(b,undefined,{sensitivity:"base"}))){const target=path?`${path}/${folder}`:folder;const option=document.createElement("option");option.value=folderOption(target);option.textContent=`📁 ${folder}`;option.title=`Open ${target}`;select.append(option);}
    for(const name of directFiles.sort((a,b)=>cleanRelativePath(a).localeCompare(cleanRelativePath(b),undefined,{sensitivity:"base"}))){const clean=cleanRelativePath(name);const option=document.createElement("option");option.value=name;option.textContent=clean.slice(clean.lastIndexOf("/")+1);option.title=clean;select.append(option);}
    if(!childFolders.size&&!directFiles.length){const placeholder=all.find(name=>name.startsWith("(no compatible files"));const empty=document.createElement("option");empty.disabled=true;empty.textContent=placeholder||emptyLabel;select.append(empty);}
  }
  select.value=current&&[...select.options].some(option=>option.value===String(current))?String(current):noneValue;
  return select;
}
function fillLoraCombo(select,values,current,query="",browsePath=""){
  return fillFolderCombo(select,Array.isArray(values)?values:["(none)"],current,query,browsePath,"No matching LoRAs");
}
function loraCombo(values,current,query="",browsePath=""){
  const select=document.createElement("select");select.className="apx-input";
  return fillLoraCombo(select,values,current,query,browsePath);
}
function loraField(labelText,input){
  const field=document.createElement("div");field.className="apx-field";
  const label=document.createElement("label");label.textContent=labelText;field.append(label,input);return field;
}
function syncLoraBrowseHint(node){
  const hint=node._apxLoraBrowseHint;if(!hint)return;
  hint.textContent=node._apxLoraFilter?"🔎 Search results include every LoRA subfolder.":`📂 ${node._apxLoraBrowsePath||"All folders"}`;
}
function strengthControl(node,rows,row,key,labelText){
  const field=document.createElement("div");field.className="apx-field";
  const label=document.createElement("label");label.textContent=labelText;field.append(label);
  const wrap=document.createElement("div");wrap.className="apx-strength";
  const slider=document.createElement("input");slider.type="range";slider.min="-5";slider.max="5";slider.step="0.05";slider.title="Slider range: -5 to 5; type any finite strength in the value field";
  const initial=Number(row[key]??1),value=Number.isFinite(initial)?initial:1;
  const minus=document.createElement("button");minus.type="button";minus.className="apx-strength-step";minus.textContent="−";minus.title="Decrease strength by 0.05";
  const plus=document.createElement("button");plus.type="button";plus.className="apx-strength-step";plus.textContent="+";plus.title="Increase strength by 0.05";
  const input=document.createElement("input");input.type="number";input.step="any";input.className="apx-input apx-strength-value";input.setAttribute("aria-label",`${labelText} (any finite value)`);input.value=String(value);
  const syncSlider=()=>{slider.value=String(Math.max(-5,Math.min(5,Number(row[key]))));};
  const commit=()=>{if(input.value.trim()==="")return;const next=Number(input.value);if(!Number.isFinite(next))return;row[key]=next;input.value=String(next);syncSlider();writeLoraRows(node,rows);};
  slider.value=String(Math.max(-5,Math.min(5,value)));
  slider.addEventListener("input",()=>{row[key]=Number(slider.value);input.value=String(row[key]);writeLoraRows(node,rows)});
  input.addEventListener("change",commit);input.addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();commit();input.blur();}});
  const nudge=delta=>{const current=Number(input.value);const base=Number.isFinite(current)?current:value;row[key]=Math.round((base+delta)*100)/100;input.value=String(row[key]);syncSlider();writeLoraRows(node,rows);};
  minus.addEventListener("click",()=>nudge(-0.05));plus.addEventListener("click",()=>nudge(0.05));
  wrap.append(minus,slider,plus,input);field.append(wrap);return field;
}
async function copyTriggerWord(node,word){
  try{await navigator.clipboard.writeText(word);if(node._apxTriggerStatus)node._apxTriggerStatus.textContent=`Copied: ${word}`;}
  catch{if(node._apxTriggerStatus)node._apxTriggerStatus.textContent="Clipboard access was unavailable; select the trigger text manually.";}
}
async function scanLoraTriggerWords(node){
  const rows=readLoraRows(node),names=[...new Set(rows.filter(r=>r.name&&r.name!=="(none)").map(r=>r.name))];
  const button=node._apxLoraScanButton,status=node._apxTriggerStatus;
  if(!names.length){if(status)status.textContent="Add a LoRA before scanning.";return;}
  if(button)button.disabled=true;if(status)status.textContent=`Checking ${names.length} selected LoRA${names.length===1?"":"s"}…`;
  node._apxTriggerSuggestions??=new Map();
  let next=0,completed=0,found=0,local=0,remote=0;
  const worker=async()=>{while(next<names.length){const name=names[next++];try{
    const response=await fetch(`/apex/v2/lora-trigger-words?name=${encodeURIComponent(name)}`);
    const result=await response.json();if(!response.ok)throw new Error(result.error||`HTTP ${response.status}`);
    if(result.words?.length){node._apxTriggerSuggestions.set(name,{words:result.words,source:result.source});found++;if(result.source==="local metadata")local++;else if(result.source==="Civitai SHA-256")remote++;}
    else node._apxTriggerSuggestions.set(name,{words:[],source:result.source||"none"});
  }catch(error){node._apxTriggerSuggestions.set(name,{words:[],source:"error",error:String(error?.message||error)});}
    completed++;if(status)status.textContent=`Checked ${completed}/${names.length} selected LoRAs…`;
  }
  };
  await Promise.all(Array.from({length:Math.min(3,names.length)},worker));
  renderLoraRows(node,rows);
  const unavailable=names.filter(name=>{const result=node._apxTriggerSuggestions.get(name);return result?.source==="Civitai lookup unavailable"||result?.source==="error";}).length;
  if(status)status.textContent=found?`${found} LoRA${found===1?"":"s"} matched · ${local} local metadata · ${remote} Civitai lookup.${unavailable?` ${unavailable} lookup${unavailable===1?"":"s"} unavailable.`:" Click a red chip to copy."}`:unavailable?`Local metadata had no words; Civitai could not be reached for ${unavailable} lookup${unavailable===1?"":"s"}.`:"No trigger words found. Local metadata may be empty and Civitai's older-file index is incomplete.";
  if(button)button.disabled=false;
}
function renderLoraRows(node,rows=readLoraRows(node)){
  const list=node._apxLoraList;if(!list)return;
  list.replaceChildren();
  if(node._apxLoraCount){const active=rows.filter(r=>r.on!==false&&r.name&&r.name!=="(none)").length;node._apxLoraCount.textContent=`${active} active · ${rows.length} / ${MAX_LORA_ROWS}`;}
  const catalog=loraWidget(node,"lora_catalog"),values=catalog?.options?.values||["(none)"];
  if(!rows.length){const empty=document.createElement("div");empty.className="apx-lora-empty";empty.textContent="No LoRAs selected. Add one when you need it.";list.append(empty);}
  rows.forEach((row,index)=>{
    const item=document.createElement("div");item.className="apx-lora-row";item.dataset.off=String(!row.on);
    const top=document.createElement("div");top.className="apx-lora-top";
    const enabled=document.createElement("button");enabled.type="button";enabled.className="apx-lora-switch";enabled.setAttribute("role","switch");
    const syncEnabled=()=>{const active=row.on!==false;enabled.setAttribute("aria-checked",String(active));enabled.textContent=active?"ON":"OFF";enabled.title=active?"LoRA is active for the next queued run":"LoRA is bypassed";enabled.setAttribute("aria-label",(active?"Bypass ":"Apply ")+(row.name||"selected LoRA"));item.dataset.off=String(!active)};
    syncEnabled();enabled.addEventListener("click",()=>{row.on=row.on===false;syncEnabled();writeLoraRows(node,rows)});
    const select=loraCombo(values,row.name||"(none)",node._apxLoraFilter||"",node._apxLoraBrowsePath||"");select.setAttribute("aria-label","Select LoRA file");select.title="Browse LoRA folders or search every local LoRA";select.addEventListener("change",()=>{const folder=folderOptionPath(select.value);if(folder!==null){node._apxLoraBrowsePath=folder;syncLoraBrowseHint(node);if(node._apxLoraPicker)fillLoraCombo(node._apxLoraPicker,values,"(none)",node._apxLoraFilter||"",folder);renderLoraRows(node,rows);return;}row.name=select.value==="(none)"?"":select.value;syncEnabled();writeLoraRows(node,rows)});
    const button=(label,title,fn,disabled=false)=>{const b=document.createElement("button");b.type="button";b.className="apx-mini-button";b.textContent=label;b.title=title;b.disabled=disabled;b.addEventListener("click",fn);return b;};
    top.append(enabled,select,
      button("↑","Move up",()=>{if(index>0){[rows[index-1],rows[index]]=[rows[index],rows[index-1]];writeLoraRows(node,rows);renderLoraRows(node,rows)}},index===0),
      button("↓","Move down",()=>{if(index<rows.length-1){[rows[index+1],rows[index]]=[rows[index],rows[index+1]];writeLoraRows(node,rows);renderLoraRows(node,rows)}},index===rows.length-1),
      button("+","Duplicate",()=>{if(rows.length<MAX_LORA_ROWS){rows.splice(index+1,0,{...row});writeLoraRows(node,rows);renderLoraRows(node,rows)}},rows.length>=MAX_LORA_ROWS),
      button("×","Remove",()=>{rows.splice(index,1);writeLoraRows(node,rows);renderLoraRows(node,rows)}));
    const fields=document.createElement("div");fields.className="apx-lora-fields";
    const trigger=document.createElement("input");trigger.type="text";trigger.className="apx-input";trigger.placeholder="Optional trigger words";trigger.value=String(row.trigger||"");trigger.addEventListener("input",()=>{row.trigger=trigger.value;writeLoraRows(node,rows)});
    const suggestions=node._apxTriggerSuggestions?.get(row.name);
    const triggerField=loraField("TRIGGER WORDS",trigger);
    if(suggestions?.words?.length){const chips=document.createElement("div");chips.className="apx-trigger-results";for(const word of suggestions.words){const chip=document.createElement("button");chip.type="button";chip.className="apx-trigger-chip";chip.textContent=word;chip.title=`Copy trigger word · ${suggestions.source}`;chip.addEventListener("click",()=>copyTriggerWord(node,word));chips.append(chip);}const source=document.createElement("span");source.className="apx-trigger-source";source.textContent=suggestions.source;triggerField.append(chips,source);}
    fields.append(triggerField,strengthControl(node,rows,row,"sm","MODEL STRENGTH"),strengthControl(node,rows,row,"sc","CLIP STRENGTH"));
    item.append(top,fields);list.append(item);
  });
  if(node._apxLoraAdd)node._apxLoraAdd.disabled=rows.length>=MAX_LORA_ROWS||node._apxLoraPicker?.value==="(none)";
  if(node._apxLoraToggleAll){node._apxLoraToggleAll.textContent=rows.length&&rows.every(r=>r.on)?"Disable all":"Enable all";node._apxLoraToggleAll.disabled=!rows.length;}
}
const RESOLUTION_DEFAULT={mode:"preset",ratio:"2:3",w:896,h:1344,custom_w:1024,custom_h:1024,custom_ratio_w:4,custom_ratio_h:3,snap:16};
const RESOLUTION_SIZES={
  "1:1":[[512,512],[768,768],[1024,1024],[1280,1280],[1328,1328],[1408,1408],[1536,1536],[2048,2048]],
  "16:9":[[832,480],[1280,720],[1344,768],[1536,864],[1600,896],[1664,928],[1792,1008],[1920,1088]],
  "9:16":[[480,832],[720,1280],[768,1344],[864,1536],[896,1600],[928,1664],[1008,1792],[1088,1920]],
  "2:1":[[512,256],[1024,512],[1280,640],[1536,768],[1600,800],[1792,896],[1920,960],[2048,1024]],
  "3:2":[[768,512],[1024,680],[1152,768],[1344,896],[1536,1024],[1632,1088],[1728,1152],[1920,1280]],
  "2:3":[[512,768],[680,1024],[768,1152],[896,1344],[1024,1536],[1088,1632],[1152,1728],[1280,1920]],
  "4:3":[[512,384],[640,480],[768,576],[1024,768],[1280,960],[1408,1056],[1600,1200],[1920,1440]],
  "3:4":[[384,512],[480,640],[576,768],[768,1024],[960,1280],[1056,1408],[1200,1600],[1440,1920]],
  "4:5":[[512,640],[640,800],[768,960],[832,1040],[1024,1280],[1152,1440],[1280,1600],[1536,1920]],
};
const RESOLUTION_DEFAULTS={"1:1":[1024,1024],"16:9":[1280,720],"9:16":[720,1280],"2:1":[1280,640],"3:2":[1152,768],"2:3":[896,1344],"4:3":[1024,768],"3:4":[768,1024],"4:5":[1024,1280]};
const RESOLUTION_RATIOS=Object.keys(RESOLUTION_SIZES);
function readResolutionState(node){
  try{return {...RESOLUTION_DEFAULT,...JSON.parse(loraWidget(node,"resolution_ui")?.value||"{}")};}catch{return {...RESOLUTION_DEFAULT};}
}
function resolutionClamp(value,snap){
  const s=[8,16,32,64].includes(Number(snap))?Number(snap):16;
  const n=Math.round(Number(value)/s)*s;
  return Math.max(64,Math.min(16384,Number.isFinite(n)?n:s*64));
}
function safeResolutionMath(text){
  const source=String(text).trim();if(!source||source.length>96||!/^[0-9+\-*/().\s]+$/.test(source))return NaN;
  let i=0,depth=0;const ws=()=>{while(/\s/.test(source[i]||""))i++;},eat=c=>{ws();if(source[i]===c){i++;return true;}return false;};
  function factor(){if(++depth>32)return NaN;ws();let v;if(eat("+"))v=factor();else if(eat("-"))v=-factor();else if(eat("(")){v=expr();if(!eat(")"))v=NaN;}else{const start=i;while(/[0-9.]/.test(source[i]||""))i++;const raw=source.slice(start,i);v=(raw&&!((raw.match(/\./g)||[]).length>1))?Number(raw):NaN;}depth--;return v;}
  function term(){let v=factor();for(;;){if(eat("*"))v*=factor();else if(eat("/")){const d=factor();v=d===0?NaN:v/d;}else return v;}}
  function expr(){let v=term();for(;;){if(eat("+"))v+=term();else if(eat("-"))v-=term();else return v;}}
  const value=expr();ws();return i===source.length&&Number.isFinite(value)?value:NaN;
}
function writeResolutionState(node,state,w,h){
  const width=Math.max(64,Math.min(16384,Math.round(Number(w)||64)));
  const height=Math.max(64,Math.min(16384,Math.round(Number(h)||64)));
  state={...RESOLUTION_DEFAULT,...state,w:width,h:height};
  const widget=loraWidget(node,"resolution_ui");if(widget)setValue(node,widget,JSON.stringify(state));
  const widthWidget=loraWidget(node,"width"),heightWidget=loraWidget(node,"height");
  if(widthWidget)setValue(node,widthWidget,width);if(heightWidget)setValue(node,heightWidget,height);
  if(node._apxResolutionDims)node._apxResolutionDims.textContent=`${width} × ${height}`;
  if(node._apxResolutionAspect){const ratio=width/height;node._apxResolutionAspect.style.aspectRatio=`${width} / ${height}`;node._apxResolutionAspect.style.width=`${Math.max(26,Math.min(52,52*Math.min(1,ratio)))}px`;node._apxResolutionAspect.style.height=`${Math.max(26,Math.min(42,42/Math.max(1,ratio)))}px`;}
}
function resolutionField(label,input,wide=false){const field=loraField(label,input);if(wide)field.classList.add("wide");return field;}
function buildResolutionPanel(node,batchWidget){
  const box=document.createElement("section");box.className="apx-section";box.dataset.accent="red";
  const title=document.createElement("div");title.className="apx-label";title.textContent="02 / CANVAS + RESOLUTION";box.append(title);
  const grid=document.createElement("div");grid.className="apx-resolution-grid";
  const mode=document.createElement("select");mode.className="apx-input";
  [["preset","Ratio presets"],["custom_ratio","Custom ratio"],["custom","Exact dimensions"]].forEach(([v,label])=>{const o=document.createElement("option");o.value=v;o.textContent=label;mode.append(o)});
  let state=readResolutionState(node);mode.value=state.mode;grid.append(resolutionField("MODE",mode,true));
  const selector=document.createElement("select");selector.className="apx-input";
  let baseWidth=document.createElement("select");baseWidth.className="apx-input";
  [512,768,1024,1536].forEach(v=>{const o=document.createElement("option");o.value=String(v);o.textContent=`${v} px`;baseWidth.append(o)});
  const ratioW=document.createElement("input"),ratioH=document.createElement("input");
  for(const input of [ratioW,ratioH]){input.type="number";input.className="apx-input";input.min="1";input.max="1000";input.step="1";}
  ratioW.value=String(state.custom_ratio_w);ratioH.value=String(state.custom_ratio_h);
  const exactW=document.createElement("input"),exactH=document.createElement("input");
  for(const input of [exactW,exactH]){input.type="text";input.className="apx-input";input.inputMode="decimal";input.maxLength=96;}
  exactW.value=String(state.custom_w);exactH.value=String(state.custom_h);
  const snap=document.createElement("select");snap.className="apx-input";
  [8,16,32,64].forEach(v=>{const o=document.createElement("option");o.value=String(v);o.textContent=`Snap ${v}px`;snap.append(o)});snap.value=String(state.snap);
  const updateSizeOptions=()=>{
    const sizes=RESOLUTION_SIZES[state.ratio]||RESOLUTION_SIZES["2:3"];
    selector.replaceChildren();sizes.forEach(([w,h])=>{const o=document.createElement("option");o.value=`${w}x${h}`;o.textContent=`${w} × ${h}`;selector.append(o)});
    const current=`${state.w}x${state.h}`;selector.value=sizes.some(([w,h])=>`${w}x${h}`===current)?current:`${(RESOLUTION_DEFAULTS[state.ratio]||[896,1344]).join("x")}`;
  };
  const paintMode=()=>{
    grid.querySelectorAll("[data-resolution-control]").forEach(el=>el.remove());
    const add=(label,input)=>{const f=resolutionField(label,input);f.dataset.resolutionControl="1";grid.append(f);};
    if(state.mode==="preset"){
      const ratios=document.createElement("select");ratios.className="apx-input";RESOLUTION_RATIOS.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;ratios.append(o)});ratios.value=state.ratio;
      ratios.onchange=()=>{state.ratio=ratios.value;const [w,h]=RESOLUTION_DEFAULTS[state.ratio];state.w=w;state.h=h;updateSizeOptions();writeResolutionState(node,state,w,h)};
      selector.onchange=()=>{const [w,h]=selector.value.split("x").map(Number);state.w=w;state.h=h;writeResolutionState(node,state,w,h)};
      add("ASPECT RATIO",ratios);add("SIZE PRESET",selector);
    }else if(state.mode==="custom_ratio"){
      const update=()=>{const rw=Math.max(1,Number(ratioW.value)||4),rh=Math.max(1,Number(ratioH.value)||3),s=Number(snap.value),w=resolutionClamp(Number(baseWidth.value),s),h=resolutionClamp(w*rh/rw,s);state={...state,custom_ratio_w:rw,custom_ratio_h:rh,snap:s};writeResolutionState(node,state,w,h)};
      ratioW.onchange=update;ratioH.onchange=update;baseWidth.onchange=update;snap.onchange=update;
      add("RATIO WIDTH",ratioW);add("RATIO HEIGHT",ratioH);add("BASE WIDTH",baseWidth);add("SNAP",snap);
      ratioW.value=String(state.custom_ratio_w);ratioH.value=String(state.custom_ratio_h);baseWidth.value=String([512,768,1024,1536].reduce((best,v)=>Math.abs(v-state.w)<Math.abs(best-state.w)?v:best,1024));
    }else{
      const update=()=>{const s=Number(snap.value),parsedW=safeResolutionMath(exactW.value),parsedH=safeResolutionMath(exactH.value);if(!Number.isFinite(parsedW)||!Number.isFinite(parsedH))return;state={...state,custom_w:resolutionClamp(parsedW,s),custom_h:resolutionClamp(parsedH,s),snap:s};writeResolutionState(node,state,state.custom_w,state.custom_h)};
      exactW.onchange=update;exactH.onchange=update;snap.onchange=update;exactW.value=String(state.custom_w);exactH.value=String(state.custom_h);
      add("WIDTH (PX OR MATH)",exactW);add("HEIGHT (PX OR MATH)",exactH);add("SNAP",snap,true);
    }
    if(batchWidget){const batch=makeControl(node,batchWidget);batch.dataset.resolutionControl="1";grid.append(batch);}
    const summary=document.createElement("div");summary.className="apx-resolution-summary";summary.dataset.resolutionControl="1";
    const dims=document.createElement("strong");dims.className="apx-resolution-dims";dims.textContent=`${state.w} × ${state.h}`;
    const aspect=document.createElement("div");aspect.className="apx-resolution-aspect";summary.append(dims,aspect);box._apxDims=dims;box._apxAspect=aspect;node._apxResolutionDims=dims;node._apxResolutionAspect=aspect;grid.append(summary);
  };
  mode.addEventListener("change",()=>{
    state={...state,mode:mode.value};
    if(mode.value==="preset"){
      if(!RESOLUTION_SIZES[state.ratio])state.ratio="2:3";
      const sizes=RESOLUTION_SIZES[state.ratio]||[];
      if(!sizes.some(([w,h])=>w===state.w&&h===state.h))[state.w,state.h]=RESOLUTION_DEFAULTS[state.ratio];
    }else if(mode.value==="custom"){
      state.w=resolutionClamp(state.custom_w,state.snap);state.h=resolutionClamp(state.custom_h,state.snap);
      state.custom_w=state.w;state.custom_h=state.h;
    }else{
      const s=Number(state.snap)||16;
      state.w=resolutionClamp(state.w,s);
      state.h=resolutionClamp(state.w*Number(state.custom_ratio_h||3)/Number(state.custom_ratio_w||4),s);
    }
    paintMode();writeResolutionState(node,state,state.w,state.h);
  });
  box.append(grid);node._apxResolutionDims=null;node._apxResolutionAspect=null;
  const widget=loraWidget(node,"resolution_ui");if(widget){
    try{state={...RESOLUTION_DEFAULT,...JSON.parse(widget.value||"{}")};mode.value=state.mode;}catch{}
  }
  updateSizeOptions();paintMode();
  node._apxResolutionDims=box._apxDims;node._apxResolutionAspect=box._apxAspect;
  node._apxResolutionRefresh=()=>{
    const current=loraWidget(node,"resolution_ui");
    try{state={...RESOLUTION_DEFAULT,...JSON.parse(current?.value||"{}")};}catch{state={...RESOLUTION_DEFAULT};}
    mode.value=state.mode;updateSizeOptions();paintMode();writeResolutionState(node,state,state.w,state.h);
  };
  writeResolutionState(node,state,state.w,state.h);
  return box;
}
function makeControl(node, widget, wide=false, filter="", folderAware=false) {
  const field = document.createElement("div"); field.className = `apx-field${wide ? " wide" : ""}`;
  const label = document.createElement("label"); label.textContent = widget.name.replaceAll("_", " ");
  const id = `apx-${node.id}-${slug(widget.name)}`; label.htmlFor=id; field.append(label);
  let input;
  let folderHint=null;
  const values = widget.options?.values;
  if (Array.isArray(values) && values.length) {
    input=document.createElement("select"); input.className="apx-input";
    const browse=node._apxModelBrowse||(node._apxModelBrowse={});
    const fill=()=>{fillFolderCombo(input,values,String(widget.value ?? values[0]),filter,browse[widget.name]||"");if(folderHint)folderHint.textContent=`📂 ${browse[widget.name]||"All folders"}${filter?" · search covers all folders":""}`;};
    if(folderAware)fill();
    else values.forEach(v=>{const o=document.createElement("option");o.value=String(v);o.textContent=String(v);input.append(o)});
    input.value=String(widget.value ?? values[0]);
    if(folderAware){folderHint=document.createElement("div");folderHint.className="apx-hint";folderHint.textContent=`📂 ${browse[widget.name]||"All folders"}${filter?" · search covers all folders":""}`;input.title="Choose a folder to browse into, or search across all installed files.";input.addEventListener("focus",fill);}
    input.addEventListener("change",()=>{if(folderAware){const folder=folderOptionPath(input.value);if(folder!==null){browse[widget.name]=folder;fill();return;}}setValue(node,widget,input.value)});
  } else if (typeof widget.value === "boolean" || widget.type === "toggle") {
    input=document.createElement("input"); input.type="checkbox"; input.checked=!!widget.value;
    const wrap=document.createElement("div");wrap.className="apx-toggle";wrap.append(input,document.createTextNode("enabled"));
    input._apxWidget=widget;widget._apxInput=input;
    input.addEventListener("change",()=>setValue(node,widget,input.checked)); field.append(wrap); return field;
  } else if (typeof widget.value === "number" || ["number","slider"].includes(widget.type)) {
    input=document.createElement("input"); input.type="number"; input.className="apx-input"; input.value=String(widget.value ?? 0);
    const opts=widget.options||{}; if(Number.isFinite(opts.min))input.min=opts.min;if(Number.isFinite(opts.max))input.max=opts.max;if(Number.isFinite(opts.step))input.step=opts.step;
    input.addEventListener("change",()=>{const n=Number(input.value);if(Number.isFinite(n))setValue(node,widget,n)});
  } else {
    const multiline=widget.options?.multiline || widget.type === "customtext";
    input=document.createElement(multiline?"textarea":"input"); input.className=`apx-input${multiline?" apx-text":""}`;
    if(!multiline)input.type="text"; input.value=String(widget.value??"");
    input.addEventListener("input",()=>setValue(node,widget,input.value));
  }
  input.id=id;input._apxWidget=widget;widget._apxInput=input;field.append(input);if(folderHint)field.append(folderHint);return field;
}
function section(title, widgets, node, opts={}) {
  const box=document.createElement("section");box.className="apx-section";box.dataset.accent=opts.accent||"red";
  const heading=document.createElement("div");heading.className="apx-label";heading.textContent=title;
  if(opts.meta){const m=document.createElement("span");m.textContent=opts.meta;heading.append(m)}
  box.append(heading);
  let filter="";
  if(opts.folderSearch){const search=document.createElement("input");search.type="search";search.className="apx-input";search.placeholder="Search installed files and subfolders…";search.setAttribute("aria-label","Search installed model files and subfolders");search.value=String(node._apxModelFilter||"");search.addEventListener("input",()=>{node._apxModelFilter=search.value;grid.replaceChildren();widgets.forEach(w=>grid.append(makeControl(node,w,opts.wide?.includes(w.name),search.value,["model_file","text_encoder","vae"].includes(w.name))))});box.append(search);filter=search.value;}
  const grid=document.createElement("div");grid.className=`apx-grid${opts.three?" three":""}`;
  widgets.forEach(w=>grid.append(makeControl(node,w,opts.wide?.includes(w.name),filter,opts.folderSearch&&["model_file","text_encoder","vae"].includes(w.name))));box.append(grid);return box;
}
function head(info) {
  const d=document.createElement("header");d.className="apx-head";
  d.innerHTML=`<div class="apx-mark"><i class="apx-led"></i> APEXLIGHTSPEED <span style="color:#857679">/ PIPELINE</span></div><div class="apx-title">${info.title}</div><div class="apx-sub">${info.code}　·　APEX ORIGINAL SYSTEM</div>`;return d;
}
function buildBody(node, type) {
  const root=document.createElement("div");root.className="apx-shell";
  const info=META[type];root.append(head(info));
  const ws=(node.widgets||[]).filter(w=>!w._apxSurface && !["lora_tags","lora_stack","lora_catalog","resolution_ui"].includes(w.name));
  if(type==="ApexGenerationCore"||type==="ApexLoraGenerationCore"){
    const by=n=>ws.find(w=>w.name===n);
    const get=names=>names.map(by).filter(Boolean);
    root.append(section("01 / Prompt",get(["prompt"]),node,{wide:["prompt"],accent:"cyan"}));
    root.append(buildResolutionPanel(node,by("batch_size")));
    const loraBox=document.createElement("section");loraBox.className="apx-section";loraBox.dataset.accent="cyan";
    const loraHeading=document.createElement("div");loraHeading.className="apx-label apx-lora-heading";
    loraHeading.append(document.createTextNode("03 / LoRA stack"));
    const headingTools=document.createElement("div");headingTools.className="apx-lora-heading-tools";
    const scan=document.createElement("button");scan.type="button";scan.className="apx-trigger-scan";scan.textContent="Find triggers";scan.title="Reads local metadata first. If needed, only the selected file's SHA-256 is sent to Civitai for a public model-version lookup; no model data is uploaded.";scan.addEventListener("click",()=>scanLoraTriggerWords(node));
    const count=document.createElement("span");count.textContent=`0 active · 0 / ${MAX_LORA_ROWS}`;
    headingTools.append(scan,count);loraHeading.append(headingTools);
    const helper=document.createElement("div");helper.className="apx-lora-helper";helper.textContent="Search local LoRA filenames, then choose from the dropdown. The list filters for adding and changing entries; enabled LoRAs apply on the next queued run.";
    const search=document.createElement("input");search.type="search";search.className="apx-input";search.placeholder="Search local LoRA files…";search.setAttribute("aria-label","Search local LoRA files");search.value=String(node._apxLoraFilter||"");
    const searchField=loraField("SEARCH LOCAL LORAS",search);
    const browseHint=document.createElement("div");browseHint.className="apx-hint";node._apxLoraBrowseHint=browseHint;syncLoraBrowseHint(node);
    const list=document.createElement("div");list.className="apx-lora-list";
    const catalog=loraWidget(node,"lora_catalog");const values=catalog?.options?.values||["(none)"];
    const addbar=document.createElement("div");addbar.className="apx-lora-addbar";
    const picker=loraCombo(values,"(none)",search.value,node._apxLoraBrowsePath||"");
    const add=document.createElement("button");add.type="button";add.className="apx-add-button";add.textContent="Add LoRA";add.disabled=true;add.title="Search for and choose a LoRA first.";
    const syncAdd=()=>{add.disabled=picker.value==="(none)"||readLoraRows(node).length>=MAX_LORA_ROWS;add.title=add.disabled?"Search for and choose a LoRA first.":"Add the selected LoRA to the stack."};
    picker.addEventListener("change",()=>{const folder=folderOptionPath(picker.value);if(folder!==null){node._apxLoraBrowsePath=folder;syncLoraBrowseHint(node);fillLoraCombo(picker,values,"(none)",search.value,folder);syncAdd();renderLoraRows(node);return;}syncAdd()});
    search.addEventListener("input",()=>{node._apxLoraFilter=search.value;syncLoraBrowseHint(node);fillLoraCombo(picker,values,"(none)",search.value,node._apxLoraBrowsePath||"");syncAdd();renderLoraRows(node)});
    add.addEventListener("click",()=>{const rows=readLoraRows(node);if(rows.length>=MAX_LORA_ROWS||picker.value==="(none)")return;rows.push({name:picker.value,on:true,sm:1,sc:1,trigger:""});writeLoraRows(node,rows);renderLoraRows(node,rows)});
    const toggleAll=document.createElement("button");toggleAll.type="button";toggleAll.className="apx-add-button";toggleAll.textContent="Enable all";toggleAll.disabled=true;toggleAll.title="Enable or disable every LoRA in the stack.";
    toggleAll.addEventListener("click",()=>{const rows=readLoraRows(node);const turnOn=rows.some(r=>!r.on);rows.forEach(r=>r.on=turnOn);writeLoraRows(node,rows);renderLoraRows(node,rows)});
    const scanStatus=document.createElement("div");scanStatus.className="apx-trigger-status";scanStatus.setAttribute("aria-live","polite");
    addbar.append(picker,add,toggleAll);loraBox.append(loraHeading,helper,searchField,browseHint,list,addbar,scanStatus);root.append(loraBox);
    node._apxLoraList=list;node._apxLoraCount=count;node._apxLoraAdd=add;node._apxLoraPicker=picker;node._apxLoraSearch=search;node._apxLoraToggleAll=toggleAll;node._apxLoraScanButton=scan;node._apxTriggerStatus=scanStatus;
    renderLoraRows(node);
    root.append(section("04 / Sampling",get(["seed_mode","seed","speed_boost","steps","cfg","sampler_name","scheduler"]),node,{three:true,accent:"red"}));
    const run=document.createElement("section");run.className="apx-section";run.dataset.accent="red";run.innerHTML='<div class="apx-label">05 / Run telemetry</div><div class="apx-status">Ready for generation.</div>';root.append(run);node._apxStatus=run.querySelector(".apx-status");
  } else if(type==="ApexOutput"){
    root.append(section("01 / Destination",ws.filter(w=>["folder","filename","format","quality"].includes(w.name)),node,{accent:"cyan",three:true}));
    root.append(section("02 / Metadata",ws.filter(w=>["negative","denoise"].includes(w.name)),node,{accent:"red",wide:["negative"]}));
    root.append(section("03 / PNG + resource data",ws.filter(w=>["embed_workflow","embed_civitai","hash_resources"].includes(w.name)),node,{three:true,accent:"cyan"}));
    const timer=document.createElement("section");timer.className="apx-section";timer.dataset.accent="cyan";
    timer.innerHTML='<div class="apx-label">04 / Run time <span>WHOLE WORKFLOW</span></div><div class="apx-clock-row"><strong class="apx-clock" data-state="idle">--:--</strong><span class="apx-clock-state">NO COMPLETED RUN</span></div>';
    root.append(timer);node._apxClock=timer.querySelector(".apx-clock");node._apxClockState=timer.querySelector(".apx-clock-state");
    const prior=Number(node.properties?.runTimerLastMs);if(Number.isFinite(prior)&&prior>0){node._apxClock.textContent=formatRunTime(prior);node._apxClockState.textContent="LAST COMPLETED RUN";}
    const status=document.createElement("div");status.className="apx-section";status.dataset.accent="red";
    status.innerHTML='<div class="apx-label">05 / Last save</div><div class="apx-status">Ready for image output.</div>';
    const previewSize=document.createElement("div");previewSize.className="apx-preview-size-row";
    const previewLabel=document.createElement("label");previewLabel.textContent="Preview size";
    const previewSlider=document.createElement("input");previewSlider.type="range";previewSlider.min="120";previewSlider.max="420";previewSlider.step="20";
    const previewHeight=Math.max(120,Math.min(420,Number(node.properties?.apxPreviewHeight)||220));previewSlider.value=String(previewHeight);
    const previewValue=document.createElement("output");previewValue.textContent=`${previewHeight}px`;
    const image=document.createElement("img");image.className="apx-preview";image.hidden=true;image.style.maxHeight=`${previewHeight}px`;
    const updatePreviewSize=()=>{const h=Number(previewSlider.value);image.style.maxHeight=`${h}px`;previewValue.textContent=`${h}px`;node._apxFitSurface?.();node.graph?.setDirtyCanvas?.(true,true)};
    previewSlider.addEventListener("input",updatePreviewSize);
    previewSlider.addEventListener("change",()=>node.setProperty?.("apxPreviewHeight",Number(previewSlider.value)));
    image.addEventListener("load",()=>{node._apxFitSurface?.();node.graph?.setDirtyCanvas?.(true,true)});
    previewSize.append(previewLabel,previewSlider,previewValue);status.append(previewSize,image);root.append(status);
    node._apxStatus=status.querySelector(".apx-status");node._apxPreview=image;
  } else {
    const groups=[
      ["01 / Model profile",["base_model","goal"],"cyan"],
      ["02 / Model components",["model_file","text_encoder","vae","clip_type"],"red"],
      ["03 / Runtime optimization",["speed_ups","attention","fp16_accumulation","step_cache","torch_compile","qwen21_cache","spectrum","veda"],"cyan"],
    ];
    const used=new Set();
    for(const [title,names,accent] of groups){
      const fields=names.map(n=>ws.find(w=>w.name===n)).filter(Boolean);
      fields.forEach(w=>used.add(w.name));
      if(fields.length)root.append(section(title,fields,node,{three:fields.length>=3,accent,folderSearch:title==="02 / Model components"}));
    }
    const remainder=ws.filter(w=>!used.has(w.name));
    if(remainder.length)root.append(section("04 / Additional controls",remainder,node,{three:remainder.length>=3,accent:"red"}));
    const run=document.createElement("section");run.className="apx-section";run.dataset.accent="red";run.innerHTML='<div class="apx-label">Engine status</div><div class="apx-status">Ready.</div>';root.append(run);node._apxStatus=run.querySelector(".apx-status");
  }
  const foot=document.createElement("footer");foot.className="apx-foot";foot.innerHTML="<span>APEXLIGHTSPEED</span><span>V2 / NODE SYSTEM</span>";root.append(foot);
  return root;
}
function buildPreviewBody(node){
  const frame=document.createElement("div");frame.className="apx-preview-only";
  const img=document.createElement("img");img.alt="Generated image preview";img.hidden=true;
  const empty=document.createElement("div");empty.className="apx-preview-empty";empty.textContent="IMAGE PREVIEW · RUN TO DISPLAY";
  img.addEventListener("load",()=>{img.hidden=false;empty.hidden=true;});
  img.addEventListener("error",()=>{img.hidden=true;empty.hidden=false;});
  const grip=document.createElement("button");grip.type="button";grip.className="apx-preview-grip";grip.title="Drag to resize preview";grip.setAttribute("aria-label","Resize image preview");
  grip.addEventListener("pointerdown",event=>{
    if(event.button!==0)return;
    event.preventDefault();event.stopPropagation();
    if(node._apxPreviewResizeAbort)node._apxPreviewResizeAbort.abort();
    const startX=event.clientX,startY=event.clientY,startW=node.size?.[0]||480,startH=node.size?.[1]||640;
    const pointerId=event.pointerId,controller=new AbortController();node._apxPreviewResizeAbort=controller;
    const opts={capture:true,signal:controller.signal};
    const finish=e=>{
      if(node._apxPreviewResizeAbort!==controller)return;
      node._apxPreviewResizeAbort=null;node._apxPreviewResizeFinish=null;controller.abort();grip.classList.remove("is-resizing");
      try{if(grip.hasPointerCapture(pointerId))grip.releasePointerCapture(pointerId);}catch{}
      e?.preventDefault?.();e?.stopPropagation?.();
    };
    const move=e=>{
      if(e.pointerId!==pointerId)return;
      e.preventDefault();e.stopPropagation();
      const w=Math.max(280,Math.min(1600,startW+e.clientX-startX));
      const h=Math.max(240,Math.min(1600,startH+e.clientY-startY));
      node.setSize?.([w,h]);frame.style.height=`${Math.max(180,h-42)}px`;node.graph?.setDirtyCanvas?.(true,true);
    };
    node._apxPreviewResizeFinish=finish;grip.classList.add("is-resizing");
    try{grip.setPointerCapture(pointerId);}catch{}
    document.addEventListener("pointermove",move,opts);document.addEventListener("pointerup",finish,opts);
    document.addEventListener("pointercancel",finish,opts);grip.addEventListener("lostpointercapture",finish,opts);
    window.addEventListener("blur",finish,{once:true,signal:controller.signal});
    document.addEventListener("visibilitychange",()=>{if(document.hidden)finish();},{once:true,signal:controller.signal});
  });
  frame.append(img,empty,grip);frame.style.height=`${Math.max(180,(node.size?.[1]||640)-42)}px`;
  node._apxPreviewOnlyImage=img;node._apxPreviewOnlyEmpty=empty;node._apxPreviewOnlyFrame=frame;
  return frame;
}
function addPreviewSurface(node){
  if(node._apxSurfaceAdded||!node.addDOMWidget)return;
  injectStyle();node.color="#54151a";node.bgcolor="#080809";node.boxcolor="#9f1018";node.shape="round";styleVueNodeShell(node);
  const body=buildPreviewBody(node);
  const surface=node.addDOMWidget("apex_preview_surface","custom",body,{serialize:false,hideOnZoom:false,getHeight:()=>Math.max(180,(node.size?.[1]||640)-42),getMinHeight:()=>180});
  surface.serialize=false;surface._apxSurface=true;hideNativeWidgets(node,surface);
  node._apxSurfaceAdded=true;node._apxPreviewWidget=surface;
}
function hideNativeWidgets(node, surface) {
  for(const w of node.widgets||[]){ if(w===surface)continue; w.hidden=true; w.options={...(w.options||{}),hidden:true,serialize:true}; }
}

// Replace the canvas card itself as well as its HTML controls. The custom node
// callbacks run inside LiteGraph's node draw pass, behind the DOM control layer.
function drawApexNodeSurface(ctx,node){
  const b=node.boundingRect;
  if(!b)return;
  const x=b[0]-node.pos[0],y=b[1]-node.pos[1],w=b[2],h=b[3];
  if(!(w>0&&h>0))return;
  ctx.save();
  ctx.beginPath();ctx.roundRect(x,y,w,h,10);
  const fill=ctx.createLinearGradient(x,y,x+w,y+h);
  fill.addColorStop(0,"#111319");fill.addColorStop(.58,"#0b0d11");fill.addColorStop(1,"#090a0d");
  ctx.fillStyle=fill;ctx.fill();
  // Blend LiteGraph's required socket rows into the Apex shell. Keep the I/O
  // field dark and quiet so native connector labels stay readable and the
  // area flows into the branded header below instead of reading as empty space.
  const slots=Math.max(node.inputs?.length||0,node.outputs?.length||0);
  const band=Math.min(360,Math.max(72,slots*20+22));
  ctx.save();ctx.beginPath();ctx.rect(x+1,y+1,Math.max(0,w-2),Math.min(band,Math.max(0,h-2)));ctx.clip();
  if(PORT_TEXTURE.complete&&PORT_TEXTURE.naturalWidth){ctx.save();ctx.globalAlpha=.08;ctx.drawImage(PORT_TEXTURE,0,155,1200,365,x+1,y+1,w-2,Math.min(band,h-2));ctx.restore();}
  // Keep the socket field at the title header's near-black base luminance.
  // Only a trace of the texture remains; colored art belongs in the title band.
  ctx.fillStyle="#050506e8";ctx.fillRect(x+1,y+1,w-2,Math.min(band,h-2));
  const glow=ctx.createRadialGradient(x+w*.53,y+band*.54,0,x+w*.53,y+band*.54,w*.72);
  glow.addColorStop(0,"#7a10141c");glow.addColorStop(.62,"#3010140c");glow.addColorStop(1,"#090a0d00");
  ctx.fillStyle=glow;ctx.fillRect(x+1,y+1,w-2,Math.min(band,h-2));
  // A restrained central wordmark gives the connector rows a quiet center;
  // no decoration crosses the native socket labels or wire hit areas.
  const midX=x+w*.5,midY=y+band*.52;
  ctx.textAlign="center";ctx.textBaseline="middle";
  ctx.globalAlpha=.13;ctx.fillStyle="#f2eff1";ctx.font="800 23px Arial,sans-serif";
  ctx.fillText("APEX",midX,midY-2);
  ctx.globalAlpha=.32;ctx.fillStyle="#b9383c";ctx.font="600 7px ui-monospace,Consolas,monospace";
  ctx.fillText("APEX  /  LIGHTSPEED",midX,midY+15);
  const edge=ctx.createLinearGradient(x,y+band-8,x+w,y+band-8);
  edge.addColorStop(0,"#54151a00");edge.addColorStop(.5,"#8f22282c");edge.addColorStop(1,"#54151a00");
  ctx.globalAlpha=1;ctx.fillStyle=edge;ctx.fillRect(x+12,y+band-8,w-24,1);
  ctx.restore();
  // Subtle signal rail gives the whole node a branded edge without affecting
  // links, socket hit areas, or model execution.
  ctx.fillStyle="#9f1018";ctx.globalAlpha=.82;ctx.fillRect(x+1,y+14,2,Math.max(24,h-28));
  ctx.globalAlpha=.28;ctx.fillStyle="#bd2930";ctx.fillRect(x+4,y+14,1,Math.max(24,h-28));
  ctx.globalAlpha=1;ctx.lineWidth=1;ctx.strokeStyle=node.selected?"#c52a32":"#54151a";ctx.stroke();
  ctx.restore();
}

function styleVueNodeShell(node){
  if(node.id===undefined||node.id===null||String(node.id)==="-1")return;
  const id=String(node.id).replace(/[^a-zA-Z0-9_-]/g,"_");
  const slots=Math.max(node.inputs?.length||0,node.outputs?.length||0);
  node._apxPortBand=Math.min(360,Math.max(72,slots*20+22));
  const styleId=`apx-v2-vue-shell-${id}`;
  let style=document.getElementById(styleId);
  if(!style){style=document.createElement("style");style.id=styleId;document.head.append(style);}
  style.textContent=`
    [data-node-id="${id}"] [data-testid="node-inner-wrapper"]{
      position:relative!important;isolation:isolate!important;
      --apx-port-band:${node._apxPortBand}px;
      background:linear-gradient(155deg,#111319 0%,#0b0d11 58%,#090a0d 100%)!important;
      border:1px solid #54151a!important;border-radius:10px!important;
      box-shadow:inset 0 0 0 1px #9f101812,0 7px 24px #0008!important;
      overflow:hidden!important;
    }
    [data-node-id="${id}"] [data-testid="node-inner-wrapper"]::before{
      content:"";position:absolute;z-index:0;pointer-events:none;inset:0 0 auto;height:var(--apx-port-band);
      background:
        linear-gradient(90deg,#050506f5,#050506e8),
        radial-gradient(ellipse at 82% 26%,#76101422,transparent 48%),
        url("${PORT_TEXTURE_URL}") center 42%/cover no-repeat;
    }
    [data-node-id="${id}"] [data-testid="node-body-${id}"]{
      position:relative;z-index:1;background:transparent!important;row-gap:0!important;padding:0 0 8px!important;
    }
    [data-node-id="${id}"] .apx-shell{width:100%!important;margin-left:0!important;}
  `;
}

function syncWidgetControls(node){
  for(const w of node.widgets||[]){const input=w._apxInput;if(!input)continue;
    if(input.type==="checkbox")input.checked=!!w.value;else input.value=String(w.value??"");
  }
  if((node.widgets||[]).some(w=>w.name==="lora_stack"))renderLoraRows(node);
  node._apxResolutionRefresh?.();
}
function addSurface(node,type){
  if(node._apxSurfaceAdded || !node.addDOMWidget)return;
  if(!(node.widgets||[]).length)return;
  injectStyle();node.color="#54151a";node.bgcolor="#090a0d";node.boxcolor="#9f1018";node.shape="round";
  styleVueNodeShell(node);
  const body=buildBody(node,type);
  const surface=node.addDOMWidget("apex_ui_surface","custom",body,{
    serialize:false,hideOnZoom:false,getHeight:()=>Math.max(120,body.scrollHeight+8),getMinHeight:()=>Math.max(120,body.scrollHeight+8),
  });
  surface.serialize=false;
  surface._apxSurface=true;hideNativeWidgets(node,surface);
  // Keep the UI-only surface after backing controls. ComfyUI configures widgets
  // before nodeCreated adds this DOM widget; if it is prepended, its saved value
  // is restored into the first real control and shifts every later value. Native
  // controls are hidden, so leaving the surface last does not add a layout gap.
  node._apxSurfaceAdded=true;
  const minWidth=type==="ApexLoraGenerationCore"?540:500;
  let resizePending=false;
  const fitSurface=()=>{
    if(resizePending||!node._apxSurfaceAdded)return;resizePending=true;
    requestAnimationFrame(()=>{
      resizePending=false;if(!node._apxSurfaceAdded)return;
      const width=Math.max(node.size?.[0]||0,minWidth),height=Math.ceil(body.scrollHeight+42);
      // A real content-height change (LoRA rows, expanded controls, or preview
      // size) needs a layout commit. Identical measurements during canvas zoom
      // must not cause repeated node geometry writes or Vue remounts.
      if(Math.abs((node.size?.[1]||0)-height)>1)node.setSize?.([width,height]);
    });
  };
  fitSurface();node._apxFitSurface=fitSurface;
  const observer=new ResizeObserver(fitSurface);
  observer.observe(body);node._apxSurfaceObserver=observer;
  const onRemoved=node.onRemoved;
  node.onRemoved=function(){
    onRemoved?.apply(this,arguments);
    this._apxSurfaceObserver?.disconnect();
    this._apxFitSurface=null;
    document.getElementById(`apx-v2-vue-shell-${String(this.id).replace(/[^a-zA-Z0-9_-]/g,"_")}`)?.remove();
  };
}

function formatRunTime(ms){
  const total=Math.max(0,Math.floor(ms/1000));
  const sec=String(total%60).padStart(2,"0");
  const min=String(Math.floor(total/60)%60).padStart(2,"0");
  const hours=Math.floor(total/3600);
  return hours>0?`${String(hours).padStart(2,"0")}:${min}:${sec}`:`${min}:${sec}`;
}
let activeRunTimer=null;
let activeRunTimerTick=null;
function timerNodes(){
  if(!isV2Graph())return [];
  return (app.graph?._nodes||[]).filter(n=>(n?.comfyClass||n?.type)==="ApexOutput"&&n._apxClock);
}
function finishRunTimer(state){
  if(!activeRunTimer)return;
  const {nodes,started}=activeRunTimer;
  const elapsed=performance.now()-started;
  clearInterval(activeRunTimerTick);activeRunTimerTick=null;activeRunTimer=null;
  for(const node of nodes){
    if(node._apxClock)node._apxClock.textContent=formatRunTime(elapsed);
    if(node._apxClock)node._apxClock.dataset.state=state;
    if(node._apxClockState)node._apxClockState.textContent=state==="complete"?"RUN COMPLETE":state==="failed"?"RUN FAILED":"RUN INTERRUPTED";
    if(state==="complete")node.setProperty?.("runTimerLastMs",elapsed);
    node.setDirtyCanvas?.(true,true);
  }
}

app.registerExtension({
  name:"Apex.Pipeline.V2.WholeNodeSurface",
  setup(){
    api.addEventListener("execution_start",()=>{
      const nodes=timerNodes();if(!nodes.length)return;
      clearInterval(activeRunTimerTick);
      activeRunTimer={nodes,started:performance.now()};
      for(const node of nodes){if(node._apxClock){node._apxClock.dataset.state="running";node._apxClockState.textContent="RUNNING";}}
      const tick=()=>{if(!activeRunTimer)return;const elapsed=performance.now()-activeRunTimer.started;for(const node of activeRunTimer.nodes){if(node._apxClock)node._apxClock.textContent=formatRunTime(elapsed);}};
      tick();activeRunTimerTick=setInterval(tick,250);
    });
    api.addEventListener("execution_success",()=>finishRunTimer("complete"));
    api.addEventListener("execution_error",()=>finishRunTimer("failed"));
    api.addEventListener("execution_interrupted",()=>finishRunTimer("interrupted"));
  },
  async nodeCreated(node){
    const type=node?.comfyClass||node?.constructor?.ComfyClass||node?.type;
    if(!TYPES.has(type))return;
    // nodeCreated runs after ComfyNode has built the native widgets; defer once
    // so the DOM surface receives the complete widget set on every frontend version.
    requestAnimationFrame(()=>{
      if(!isV2Graph(node.graph))return;
      applyGraphTitleMode(node.graph);
      if(type==="ApexPreview")addPreviewSurface(node);else addSurface(node,type);syncWidgetControls(node);
    });
  },
  async afterConfigureGraph(){
    const nodes=app.graph?._nodes||[];
    applyGraphTitleMode(app.graph);
    if(!isV2Graph())return;
    for(const node of nodes){
      const type=node?.comfyClass||node?.constructor?.ComfyClass||node?.type;
      if(!TYPES.has(type))continue;
      if(type==="ApexPreview")addPreviewSurface(node);else addSurface(node,type);syncWidgetControls(node);
    }
  },
  async beforeRegisterNodeDef(nodeType,nodeData){
    const type=nodeType.ComfyClass||nodeData.name;if(!TYPES.has(type))return;
    if(!ORIGINAL_TITLE_MODES.has(nodeType))ORIGINAL_TITLE_MODES.set(nodeType,nodeType.title_mode);
    const drawBackground=nodeType.prototype.onDrawBackground;
    nodeType.prototype.onDrawBackground=function(ctx){
      drawBackground?.apply(this,arguments);
      if(isV2Graph(this.graph))drawApexNodeSurface(ctx,this);
    };
    if(type==="ApexOutput"){
      const executed=nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted=function(message){
        if(!isV2Graph(this.graph)){executed?.apply(this,arguments);return;}
        // Keep output handling, but route image metadata only to Apex's Last
        // save panel so ComfyUI cannot render a second native canvas thumbnail.
        const item=(message?.apex_saved_images||message?.images||[])[0];
        const cleanMessage={...(message||{}),images:[]};
        executed?.call(this,cleanMessage);
        this.imgs=[];this.imageIndex=0;this.images=[];
        if(!this._apxStatus)return;
        if(item){
          const q=new URLSearchParams({filename:item.filename,subfolder:item.subfolder||"",type:item.type||"output"});
          this._apxPreview.src=`/view?${q}`;this._apxPreview.hidden=false;
          this._apxStatus.textContent=`Saved: ${item.subfolder?item.subfolder+"/":""}${item.filename}`;
        } else if(message?.apex_saved_as){this._apxStatus.textContent=String(message.apex_saved_as)}
        this.setDirtyCanvas?.(true,true);
      };
    } else if(type==="ApexPreview"){
      const executed=nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted=function(message){
        if(!isV2Graph(this.graph)){executed?.apply(this,arguments);return;}
        const item=(message?.apex_preview_images||message?.images||[])[0];
        executed?.call(this,{...(message||{}),images:[]});
        this.imgs=[];this.imageIndex=0;this.images=[];
        if(item&&this._apxPreviewOnlyImage){
          const q=new URLSearchParams({filename:item.filename,subfolder:item.subfolder||"",type:item.type||"temp"});
          this._apxPreviewOnlyImage.hidden=true;this._apxPreviewOnlyImage.src=`/view?${q}`;
          if(this._apxPreviewOnlyEmpty)this._apxPreviewOnlyEmpty.hidden=false;
        }
        this.setDirtyCanvas?.(true,true);
      };
    } else {
      const executed=nodeType.prototype.onExecuted;
      nodeType.prototype.onExecuted=function(message){
        executed?.apply(this,arguments);
        if(isV2Graph(this.graph)&&message?.apex_status && this._apxStatus){this._apxStatus.textContent=message.apex_status.join("\n");this.setDirtyCanvas?.(true,true);}
      };
    }
  },
});
