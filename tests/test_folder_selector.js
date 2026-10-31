const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Option {
  constructor() { this.value = ""; this.textContent = ""; this.title = ""; this.disabled = false; }
}
class Select {
  constructor() { this.children = []; this._value = ""; }
  append(option) { this.children.push(option); }
  replaceChildren(...children) { this.children = children; }
  get options() { return this.children; }
  set value(value) { this._value = this.children.some(option => option.value === value) ? value : ""; }
  get value() { return this._value; }
}

const source = fs.readFileSync(path.join(__dirname, "../web/apex.js"), "utf8");
const start = source.indexOf("const FOLDER_OPTION_PREFIX=");
const end = source.indexOf("function loraField(", start);
assert(start >= 0 && end > start, "folder selector helpers must be present");
const context = { document: { createElement: tag => tag === "select" ? new Select() : new Option() } };
vm.runInNewContext(source.slice(start, end), context);

const files = [
  "None",
  "root.safetensors",
  "placeholder/model.safetensors",
  "placeholder/nested/vae.safetensors",
  String.raw`windows\organized\model.safetensors`,
];
const select = new Select();
context.fillFolderCombo(select, files, "None");
const folderEntry = select.options.find(option => option.textContent === "📁 placeholder");
assert(folderEntry, "root dropdown should expose a selectable folder entry");
assert(!select.options.some(option => option.value === "placeholder/model.safetensors"), "nested files should stay inside their folder");

context.fillFolderCombo(select, files, "None", "", "placeholder");
assert(select.options.some(option => option.value === "placeholder/model.safetensors"), "opening a folder should show its files");
assert(select.options.some(option => option.value === context.folderOption("placeholder/nested")), "nested folders should be navigable");

context.fillFolderCombo(select, files, "None", "vae");
assert(select.options.some(option => option.value === "placeholder/nested/vae.safetensors"), "search should find files in nested folders");

context.fillFolderCombo(select, files, "None", "windows");
assert(select.options.some(option => option.value === String.raw`windows\organized\model.safetensors`), "search must preserve Windows file tokens");

console.log("folder navigation and search checks passed");
