// Apex Pipeline Generator UI — status display for the three released Apex nodes.
import { app } from "../../scripts/app.js";

const LINES = { ApexRecipe: 9, ApexGenerate: 5, ApexModelOptimizer: 8 };
const LINE_H = 14;

function statusWidget(maxLines) {
  const h = maxLines * LINE_H + 12;
  return {
    name: "apex_status",
    type: "apex_status",
    value: "",
    serialize: false,
    options: { serialize: false },
    computeSize: (width) => [width, h],
    draw(ctx, node, width, y) {
      const lines = node._apexLines || ["Run to see status."];
      ctx.save();
      ctx.fillStyle = "#15181b";
      ctx.strokeStyle = "#30353c";
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(8, y, width - 16, h - 4, 6);
      else ctx.rect(8, y, width - 16, h - 4);
      ctx.fill();
      ctx.stroke();
      ctx.font = "11px sans-serif";
      const maxW = width - 32;
      lines.slice(0, maxLines).forEach((line, index) => {
        let s = String(line);
        if (ctx.measureText(s).width > maxW) {
          while (s.length > 3 && ctx.measureText(s + "…").width > maxW) s = s.slice(0, -1);
          s += "…";
        }
        ctx.fillStyle = s.startsWith("!") ? "#e0b060" : s.startsWith(" ") ? "#9fd8bb" : "#b8c0c8";
        ctx.fillText(s, 16, y + 14 + index * LINE_H);
      });
      ctx.restore();
    },
  };
}

app.registerExtension({
  name: "Apex.Pipeline.Generator",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    const maxLines = LINES[nodeData.name];
    if (!maxLines) return;
    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = created ? created.apply(this, arguments) : undefined;
      this.color = "#244d43";
      this.bgcolor = "#111715";
      this.addCustomWidget(statusWidget(maxLines));
      const size = this.computeSize();
      this.setSize([Math.max(size[0], 380), size[1]]);
      return result;
    };
    const executed = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      if (executed) executed.apply(this, arguments);
      if (message && message.apex_status) {
        this._apexLines = message.apex_status;
        this.setDirtyCanvas(true, true);
      }
    };
  },
});
