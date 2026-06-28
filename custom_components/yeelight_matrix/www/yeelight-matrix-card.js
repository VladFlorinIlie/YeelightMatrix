/**
 * Yeelight Matrix painter card.
 *
 * A simple, dependency-free Lovelace card that renders the cube matrix as a
 * grid of dots. Pick a colour, then tap (or drag across) the dots to paint
 * them — just like the Yeelight app. Editing is batched into a single
 * `yeelight_matrix.set_pixels` service call so the device draws one frame.
 *
 * Configuration:
 *   type: custom:yeelight-matrix-card
 *   entity: light.yeelight_matrix      # the whole-device light entity
 *   dot_size: 26                       # optional, px
 */

class YeelightMatrixCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("You must define an 'entity' (the Yeelight Matrix light).");
    }
    this._config = config;
    this._color = "#ff0000";
    this._painting = false;
    this._pending = new Map(); // key "m,x,y" -> {module_index,x,y,color}
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
  }

  getCardSize() {
    return 6;
  }

  _stateObj() {
    return this._hass && this._hass.states[this._config.entity];
  }

  _build() {
    const stateObj = this._stateObj();
    if (!stateObj) return;
    const modules = stateObj.attributes.modules || [];
    const orientation = stateObj.attributes.orientation || "vertical";
    const dot = this._config.dot_size || 26;

    const root = document.createElement("ha-card");
    root.header = this._config.title || "Yeelight Matrix";
    const style = document.createElement("style");
    style.textContent = `
      .wrap { padding: 12px; }
      .toolbar { display:flex; align-items:center; gap:12px; margin-bottom:12px; flex-wrap:wrap; }
      .toolbar input[type=color] { width:42px; height:32px; border:none; background:none; padding:0; cursor:pointer; }
      .swatches { display:flex; gap:6px; }
      .swatch { width:22px; height:22px; border-radius:4px; cursor:pointer; border:2px solid var(--divider-color); }
      button { cursor:pointer; border:none; border-radius:6px; padding:6px 10px;
               background: var(--primary-color); color: var(--text-primary-color); }
      .stack { display:flex; gap:10px; align-items:center;
               flex-direction:${orientation === "vertical" ? "column" : "row"}; }
      .module { display:grid; gap:2px; padding:4px; border-radius:6px;
                background: var(--secondary-background-color); }
      .cell { width:${dot}px; height:${dot}px; border-radius:3px; cursor:pointer;
              box-shadow: inset 0 0 0 1px rgba(0,0,0,0.25); }
      .label { font-size:11px; color: var(--secondary-text-color); text-align:center; }
    `;
    root.appendChild(style);

    const wrap = document.createElement("div");
    wrap.className = "wrap";

    // Toolbar: colour picker + swatches + clear.
    const toolbar = document.createElement("div");
    toolbar.className = "toolbar";
    const picker = document.createElement("input");
    picker.type = "color";
    picker.value = this._color;
    picker.addEventListener("input", (e) => (this._color = e.target.value));
    toolbar.appendChild(picker);

    const swatches = document.createElement("div");
    swatches.className = "swatches";
    ["#ff0000", "#ff9900", "#ffee00", "#33cc33", "#0099ff", "#9933ff", "#ffffff", "#000000"].forEach(
      (c) => {
        const s = document.createElement("div");
        s.className = "swatch";
        s.style.background = c;
        s.addEventListener("click", () => {
          this._color = c;
          picker.value = c;
        });
        swatches.appendChild(s);
      }
    );
    toolbar.appendChild(swatches);

    const clearBtn = document.createElement("button");
    clearBtn.textContent = "Clear";
    clearBtn.addEventListener("click", () =>
      this._hass.callService("yeelight_matrix", "clear", {}, { entity_id: this._config.entity })
    );
    toolbar.appendChild(clearBtn);
    wrap.appendChild(toolbar);

    // The stack of modules.
    const stack = document.createElement("div");
    stack.className = "stack";
    this._cells = {};

    modules.forEach((type, moduleIndex) => {
      const isMatrix = type.startsWith("5x5");
      const size = isMatrix ? 5 : 1;
      const grid = document.createElement("div");
      grid.className = "module";
      grid.style.gridTemplateColumns = `repeat(${size}, ${dot}px)`;

      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          const cell = document.createElement("div");
          cell.className = "cell";
          cell.style.background = "#000000";
          const key = `${moduleIndex},${x},${y}`;
          this._cells[key] = cell;
          const paint = () => this._paint(moduleIndex, x, y, cell);
          cell.addEventListener("mousedown", (e) => {
            e.preventDefault();
            this._painting = true;
            paint();
          });
          cell.addEventListener("mouseenter", () => {
            if (this._painting) paint();
          });
          grid.appendChild(cell);
        }
      }
      const container = document.createElement("div");
      const label = document.createElement("div");
      label.className = "label";
      label.textContent = `#${moduleIndex} ${type}`;
      container.appendChild(grid);
      container.appendChild(label);
      stack.appendChild(container);
    });

    document.addEventListener("mouseup", () => this._flush());
    wrap.appendChild(stack);
    root.appendChild(wrap);

    this.innerHTML = "";
    this.appendChild(root);
    this._built = true;
  }

  _paint(moduleIndex, x, y, cell) {
    cell.style.background = this._color;
    this._pending.set(`${moduleIndex},${x},${y}`, {
      module_index: moduleIndex,
      x,
      y,
      color: this._color,
    });
  }

  _flush() {
    if (!this._painting) return;
    this._painting = false;
    if (this._pending.size === 0) return;
    const pixels = Array.from(this._pending.values());
    this._pending.clear();
    this._hass.callService(
      "yeelight_matrix",
      "set_pixels",
      { pixels },
      { entity_id: this._config.entity }
    );
  }
}

customElements.define("yeelight-matrix-card", YeelightMatrixCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "yeelight-matrix-card",
  name: "Yeelight Matrix Painter",
  description: "Tap or drag to paint individual dots on a Yeelight Cube Matrix.",
});
