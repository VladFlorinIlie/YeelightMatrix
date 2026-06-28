/**
 * Yeelight Matrix painter card.
 *
 * Renders the cube matrix as a grid of dots. Pick a colour (full colour picker
 * or a quick swatch), then tap/drag to paint. Edits are batched into one
 * `yeelight_matrix.set_pixels` call so the device draws a single frame. The card
 * also mirrors the real device state (published by the light entity), so Clear,
 * uploads and changes made elsewhere are reflected here.
 *
 * Configuration:
 *   type: custom:yeelight-matrix-card
 *   entity: light.yeelight_matrix     # the whole-device light entity
 *   reverse: false                    # flip module order to match the cubes
 *   max_dot_size: 30                  # optional px upper bound per dot
 *   min_dot_size: 12                  # optional px; below this it scrolls
 */

const GAP = 2;
const MODULE_PAD = 4;
const MODULE_GAP = 10;
const WRAP_PAD = 12;

class YeelightMatrixCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("You must define an 'entity' (the Yeelight Matrix light).");
    }
    this._config = config;
    this._color = "#ff0000";
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
  }

  getCardSize() {
    return 6;
  }

  disconnectedCallback() {
    if (this._resizeObserver) this._resizeObserver.disconnect();
  }

  _stateObj() {
    return this._hass && this._hass.states[this._config.entity];
  }

  _moduleSize(type) {
    return type && type.startsWith("5x5") ? 5 : 1;
  }

  _build() {
    const stateObj = this._stateObj();
    if (!stateObj) return;
    this._modules = stateObj.attributes.modules || [];
    this._orientation = stateObj.attributes.orientation || "vertical";

    const root = document.createElement("ha-card");
    root.header = this._config.title || "Yeelight Matrix";
    const style = document.createElement("style");
    style.textContent = `
      ha-card { overflow: hidden; }
      .wrap { padding: ${WRAP_PAD}px; box-sizing: border-box; max-width: 100%; }
      .toolbar { display:flex; align-items:center; gap:10px; margin-bottom:12px; flex-wrap:wrap; }
      .picker { display:flex; align-items:center; gap:6px; }
      .picker label { font-size:12px; color: var(--secondary-text-color); }
      .toolbar input[type=color] { width:46px; height:34px; border:1px solid var(--divider-color);
               border-radius:6px; background:none; padding:0; cursor:pointer; }
      .swatches { display:flex; gap:6px; flex-wrap:wrap; }
      .swatch { width:24px; height:24px; border-radius:5px; cursor:pointer; border:2px solid var(--divider-color); }
      .swatch.active { outline:2px solid var(--primary-color); outline-offset:1px; }
      button { cursor:pointer; border:none; border-radius:6px; padding:6px 12px;
               background: var(--primary-color); color: var(--text-primary-color); font-size:13px; }
      button.secondary { background: var(--secondary-background-color); color: var(--primary-text-color); }
      .scroll { max-width:100%; overflow-x:auto; overflow-y:hidden; }
      .stack { display:flex; gap:${MODULE_GAP}px; align-items:center; width:max-content;
               flex-direction:${this._orientation === "vertical" ? "column" : "row"}; }
      .module { display:grid; gap:${GAP}px; padding:${MODULE_PAD}px; border-radius:6px;
                background: var(--secondary-background-color); touch-action:none; }
      .cell { width:var(--cell,22px); height:var(--cell,22px); border-radius:3px; cursor:pointer;
              box-shadow: inset 0 0 0 1px rgba(0,0,0,0.25); }
      .label { font-size:11px; color: var(--secondary-text-color); text-align:center; margin-top:2px; }
      .col { display:flex; flex-direction:column; align-items:center; }
    `;
    root.appendChild(style);

    const wrap = document.createElement("div");
    wrap.className = "wrap";
    wrap.appendChild(this._buildToolbar());

    const scroll = document.createElement("div");
    scroll.className = "scroll";
    this._stack = document.createElement("div");
    this._stack.className = "stack";
    this._cells = {};

    // Display order can be reversed to match the physical cubes; cell module
    // indices always stay logical so the right module is controlled.
    const order = this._modules.map((type, index) => ({ type, index }));
    if (this._config.reverse) order.reverse();

    order.forEach(({ type, index }) => {
      const size = this._moduleSize(type);
      const grid = document.createElement("div");
      grid.className = "module";
      grid.style.gridTemplateColumns = `repeat(${size}, var(--cell,22px))`;

      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          const cell = document.createElement("div");
          cell.className = "cell";
          cell.style.background = "#000000";
          cell.dataset.key = `${index},${x},${y}`;
          this._cells[cell.dataset.key] = cell;
          cell.addEventListener("click", () => this._setPixel(cell));
          grid.appendChild(cell);
        }
      }

      const col = document.createElement("div");
      col.className = "col";
      const label = document.createElement("div");
      label.className = "label";
      label.textContent = `#${index} ${type}`;
      col.appendChild(grid);
      col.appendChild(label);
      this._stack.appendChild(col);
    });

    scroll.appendChild(this._stack);
    wrap.appendChild(scroll);
    root.appendChild(wrap);

    this.innerHTML = "";
    this.appendChild(root);
    this._built = true;

    this._resizeObserver = new ResizeObserver(() => this._resizeCells());
    this._resizeObserver.observe(this);
    requestAnimationFrame(() => this._resizeCells());
    this._pullState(); // restore the current device frame on (re)load
  }

  _pullState() {
    if (!this._cells) return;
    const stateObj = this._stateObj();
    if (!stateObj) return;
    const colors = stateObj.attributes.module_colors;
    if (!colors) return;
    this._modules.forEach((type, m) => {
      const size = this._moduleSize(type);
      const grid = colors[m] || [];
      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          const cell = this._cells[`${m},${x},${y}`];
          if (cell) cell.style.background = grid[y * size + x] || "#000000";
        }
      }
    });
  }

  _buildToolbar() {
    const toolbar = document.createElement("div");
    toolbar.className = "toolbar";

    const picker = document.createElement("div");
    picker.className = "picker";
    const pickerLabel = document.createElement("label");
    pickerLabel.textContent = "Colour";
    const input = document.createElement("input");
    input.type = "color";
    input.value = this._color;
    input.addEventListener("input", (e) => {
      this._color = e.target.value;
      this._markActiveSwatch();
    });
    this._colorInput = input;
    picker.appendChild(pickerLabel);
    picker.appendChild(input);
    toolbar.appendChild(picker);

    const swatches = document.createElement("div");
    swatches.className = "swatches";
    this._swatchEls = [];
    ["#ff0000", "#ff9900", "#ffee00", "#33cc33", "#0099ff", "#9933ff", "#ffffff", "#000000"].forEach(
      (c) => {
        const s = document.createElement("div");
        s.className = "swatch";
        s.style.background = c;
        s.dataset.color = c;
        s.addEventListener("click", () => {
          this._color = c;
          this._colorInput.value = c;
          this._markActiveSwatch();
        });
        swatches.appendChild(s);
        this._swatchEls.push(s);
      }
    );
    toolbar.appendChild(swatches);
    this._markActiveSwatch();

    const uploadBtn = document.createElement("button");
    uploadBtn.className = "secondary";
    uploadBtn.textContent = "Upload art";
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";
    fileInput.style.display = "none";
    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files[0]) this._uploadImage(fileInput.files[0]);
      fileInput.value = "";
    });
    uploadBtn.addEventListener("click", () => fileInput.click());
    toolbar.appendChild(uploadBtn);
    toolbar.appendChild(fileInput);

    const clearBtn = document.createElement("button");
    clearBtn.className = "secondary";
    clearBtn.textContent = "Clear";
    clearBtn.addEventListener("click", () => {
      Object.values(this._cells).forEach((c) => (c.style.background = "#000000"));
      this._hass.callService("yeelight_matrix", "clear", {}, { entity_id: this._config.entity });
    });
    toolbar.appendChild(clearBtn);

    return toolbar;
  }

  _markActiveSwatch() {
    if (!this._swatchEls) return;
    const current = this._color.toLowerCase();
    this._swatchEls.forEach((s) =>
      s.classList.toggle("active", s.dataset.color.toLowerCase() === current)
    );
  }

  _resizeCells() {
    if (!this._stack) return;
    const maxDot = this._config.max_dot_size || 30;
    const minDot = this._config.min_dot_size || 12;

    let cols = 0;
    let modules = 0;
    if (this._orientation === "vertical") {
      cols = Math.max(...this._modules.map((t) => this._moduleSize(t)));
      modules = 1;
    } else {
      cols = this._modules.reduce((n, t) => n + this._moduleSize(t), 0);
      modules = this._modules.length;
    }

    const available = this.clientWidth - WRAP_PAD * 2;
    const fixed =
      modules * MODULE_PAD * 2 +
      (modules - 1) * MODULE_GAP +
      (this._orientation === "vertical"
        ? (cols - 1) * GAP
        : this._modules.reduce((n, t) => n + (this._moduleSize(t) - 1) * GAP, 0));

    let cell = Math.floor((available - fixed) / cols);
    cell = Math.max(minDot, Math.min(maxDot, cell));
    this._stack.style.setProperty("--cell", `${cell}px`);
  }

  _setPixel(cell) {
    cell.style.background = this._color;
    const [m, x, y] = cell.dataset.key.split(",").map(Number);
    this._hass.callService(
      "yeelight_matrix",
      "set_pixel",
      { module_index: m, x, y, color: this._color },
      { entity_id: this._config.entity }
    );
  }

  async _uploadImage(file) {
    const dataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
    const base64 = String(dataUrl).split(",")[1];
    const clearModules =
      this._modules.filter((t) => t === "5x5_clear").length || this._modules.length;
    // Clear first so the image can fill the (now free) clear modules.
    await this._hass.callService(
      "yeelight_matrix",
      "clear",
      {},
      { entity_id: this._config.entity }
    );
    await this._hass.callService(
      "yeelight_matrix",
      "set_image",
      { image_data: base64, start_module: 0, max_modules: clearModules },
      { entity_id: this._config.entity }
    );
    // Pull the resulting frame once it has propagated to the entity state.
    setTimeout(() => this._pullState(), 500);
  }
}

customElements.define("yeelight-matrix-card", YeelightMatrixCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "yeelight-matrix-card",
  name: "Yeelight Matrix Painter",
  description: "Tap or drag to paint individual dots on a Yeelight Cube Matrix.",
});
