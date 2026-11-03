// Replace Device – sidebar panel. Plain web component, no build step; follows the Home Assistant theme.

const TEXT = {
  en: {
    title: "Replace device",
    heroTitle: "A device died?",
    heroText: "Pair the new one first. It then takes over the old one's name, entity IDs and history – your automations and dashboards keep working.",
    start: "Replace a device",
    dead: "Dead devices",
    noDead: "No dead devices. Everything is reporting.",
    deadFor: "No contact for {t}",
    twin: "Possible replacement",
    replaceWith: "Replace with {name}",
    pickReplacement: "Pick replacement",
    history: "Replaced",
    undo: "Undo",
    undone: "Undone",
    moved: "{n} entities moved",
    pickTitle: "Which device is replaced?",
    old: "Old device",
    new: "New device",
    choose: "Choose…",
    deadGroup: "Dead",
    allGroup: "All devices",
    newestGroup: "Newest first",
    next: "Next",
    back: "Back",
    tookOver: "takes over",
    deadTag: "dead",
    matchTitle: "What goes where",
    matchText: "Each old entity has its match picked. Change it if it's wrong.",
    removed: "— removed",
    keepsOwn: "New, keep their own entity ID",
    usesDevice: "Automations and scripts that use the old device itself",
    usesDeviceHint: "They are updated. If the new device uses another integration, check their device triggers.",
    removeOld: "Remove the old device",
    removeOldHint: "Needed for the names to be free. If it's still in your Zigbee network, remove it there too.",
    replace: "Replace now",
    working: "Replacing…",
    doneTitle: "{name} is replaced",
    doneText: "{n} entities moved over with their history. Automations and dashboards keep working.",
    keptOld: "The old device's integration didn't allow removing it here – remove it there, so it doesn't come back.",
    undoHint: "Undo gives the new device its own names back. The old one only returns if its integration finds it again.",
    home: "Done",
    duplicate: "Two old entities point at the same new one.",
    sameDevice: "Pick two different devices.",
    error: "Something went wrong: {e}",
    minutes: "{n} min",
    hours: "{n} h",
    days: "{n} days",
    pickOld: "Which device is replaced?",
    pickNew: "Which device takes over?",
    search: "Search name, area or model…",
    allIntegrations: "All integrations",
    sameHardware: "same device",
    sameModel: "same model",
    newTag: "new",
    noResults: "Nothing found.",
    change: "Change",
    migrateTitle: "Move many devices",
    migrateStart: "Move many devices",
    migrateText: "Moving to another integration, e.g. ZHA → Zigbee2MQTT? Pair the devices there first. They are matched by their Zigbee address, serial number or MAC address – names don't matter.",
    from: "From",
    to: "To",
    findPairs: "Find pairs",
    pairsFound: "{n} devices found in both",
    noPairs: "No device was found in both. Pair them in {target} first.",
    by_ieee: "Zigbee address",
    by_serial: "serial number",
    by_mac: "MAC address",
    entitiesMatched: "{m}/{t} entities",
    missing: "{n} devices in {source} have no partner in {target} yet.",
    renameZ2m: "Same name in Zigbee2MQTT",
    renameZ2mHint: "The device gets its Home Assistant name in Zigbee2MQTT too. Entity IDs are not changed.",
    moveN: "Move {n} devices",
    migrateDone: "{d} devices moved",
    migrateDoneText: "{n} entities moved over with their history. Each device can be undone under Replaced.",
    all: "All",
    none: "None",
  },
  da: {
    title: "Udskift enhed",
    heroTitle: "Er en enhed død?",
    heroText: "Par den nye først. Så overtager den den gamles navn, entity-id'er og historik – dine automatiseringer og dashboards virker videre.",
    start: "Udskift en enhed",
    dead: "Døde enheder",
    noDead: "Ingen døde enheder. Alt melder sig.",
    deadFor: "Ingen kontakt i {t}",
    twin: "Mulig afløser",
    replaceWith: "Udskift med {name}",
    pickReplacement: "Vælg afløser",
    history: "Udskiftet",
    undo: "Fortryd",
    undone: "Fortrudt",
    moved: "{n} entiteter flyttet",
    pickTitle: "Hvilken enhed skal udskiftes?",
    old: "Gammel enhed",
    new: "Ny enhed",
    choose: "Vælg…",
    deadGroup: "Døde",
    allGroup: "Alle enheder",
    newestGroup: "Nyeste først",
    next: "Næste",
    back: "Tilbage",
    tookOver: "overtager",
    deadTag: "død",
    matchTitle: "Hvad hører sammen",
    matchText: "For hver gammel entitet er den matchende valgt. Ret den, hvis den er forkert.",
    removed: "— fjernes",
    keepsOwn: "Nye, beholder deres eget entity-id",
    usesDevice: "Automatiseringer og scripts, der bruger selve den gamle enhed",
    usesDeviceHint: "De bliver opdateret. Bruger den nye enhed en anden integration, så tjek deres enhedstriggere.",
    removeOld: "Fjern den gamle enhed",
    removeOldHint: "Nødvendigt, for at navnene bliver ledige. Er den stadig i dit Zigbee-netværk, så fjern den også der.",
    replace: "Udskift nu",
    working: "Udskifter…",
    doneTitle: "{name} er udskiftet",
    doneText: "{n} entiteter er flyttet med deres historik. Automatiseringer og dashboards virker videre.",
    keptOld: "Den gamle enheds integration tillod ikke at fjerne den her – fjern den dér, så den ikke kommer igen.",
    undoHint: "Fortryd giver den nye enhed dens egne navne tilbage. Den gamle kommer kun igen, hvis dens integration finder den.",
    home: "Færdig",
    duplicate: "To gamle entiteter peger på den samme nye.",
    sameDevice: "Vælg to forskellige enheder.",
    error: "Noget gik galt: {e}",
    minutes: "{n} min",
    hours: "{n} t",
    days: "{n} dage",
    pickOld: "Hvilken enhed skal udskiftes?",
    pickNew: "Hvilken enhed overtager?",
    search: "Søg på navn, område eller model…",
    allIntegrations: "Alle integrationer",
    sameHardware: "samme enhed",
    sameModel: "samme model",
    newTag: "ny",
    noResults: "Intet fundet.",
    change: "Skift",
    migrateTitle: "Flyt mange enheder",
    migrateStart: "Flyt mange enheder",
    migrateText: "Skal du flytte til en anden integration, fx ZHA → Zigbee2MQTT? Par enhederne dér først. De matches på deres Zigbee-adresse, serienummer eller MAC-adresse – navnene er ligegyldige.",
    from: "Fra",
    to: "Til",
    findPairs: "Find par",
    pairsFound: "{n} enheder fundet begge steder",
    noPairs: "Ingen enheder blev fundet begge steder. Par dem i {target} først.",
    by_ieee: "Zigbee-adresse",
    by_serial: "serienummer",
    by_mac: "MAC-adresse",
    entitiesMatched: "{m}/{t} entiteter",
    missing: "{n} enheder i {source} har ingen partner i {target} endnu.",
    renameZ2m: "Samme navn i Zigbee2MQTT",
    renameZ2mHint: "Enheden får også sit Home Assistant-navn i Zigbee2MQTT. Entity-id'erne ændres ikke.",
    moveN: "Flyt {n} enheder",
    migrateDone: "{d} enheder er flyttet",
    migrateDoneText: "{n} entiteter er flyttet med deres historik. Hver enhed kan fortrydes under Udskiftet.",
    all: "Alle",
    none: "Ingen",
  },
};

const DOMAIN_ICON = {
  sensor: "mdi:eye", binary_sensor: "mdi:radiobox-marked", light: "mdi:lightbulb", switch: "mdi:toggle-switch",
  button: "mdi:gesture-tap-button", event: "mdi:bell-ring", climate: "mdi:thermostat", cover: "mdi:window-shutter",
  fan: "mdi:fan", lock: "mdi:lock", number: "mdi:ray-vertex", select: "mdi:format-list-bulleted", update: "mdi:package-up",
};
const CLASS_ICON = {
  temperature: "mdi:thermometer", humidity: "mdi:water-percent", battery: "mdi:battery", pressure: "mdi:gauge",
  illuminance: "mdi:brightness-5", motion: "mdi:motion-sensor", occupancy: "mdi:home-account", door: "mdi:door",
  window: "mdi:window-open", power: "mdi:flash", energy: "mdi:lightning-bolt", voltage: "mdi:sine-wave",
  signal_strength: "mdi:wifi", moisture: "mdi:water", carbon_dioxide: "mdi:molecule-co2",
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class ReplaceDevicePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.view = "home";
    this.devices = [];
    this.historyItems = [];
    this.plan = null;
    this.mapping = {};
    this.removeOld = true;
    this.result = null;
    this.error = "";
    this.oldId = "";
    this.newId = "";
    this.query = "";
    this.srcFilter = "";
    this.renameZ2m = true;
    this.migrateSource = "";
    this.migrateTarget = "";
    this.migratePlan = null;
    this.migrateSelected = new Set();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this.load();
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.hass = hass;
  }

  set narrow(narrow) {
    this._narrow = narrow;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) menu.narrow = narrow;
  }

  t(key, vars = {}) {
    const lang = (this._hass?.language || "en").startsWith("da") ? "da" : "en";
    return (TEXT[lang][key] || TEXT.en[key]).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
  }

  ago(ts) {
    const s = Math.max(0, (Date.now() / 1000) - ts);
    if (s < 3600) return this.t("minutes", { n: Math.round(s / 60) });
    if (s < 172800) return this.t("hours", { n: Math.round(s / 3600) });
    return this.t("days", { n: Math.round(s / 86400) });
  }

  async ws(type, data = {}) {
    return this._hass.callWS({ type: `replace_device/${type}`, ...data });
  }

  async load() {
    try {
      const [devices, history] = await Promise.all([this.ws("devices"), this.ws("history")]);
      this.devices = devices.devices;
      this.historyItems = history.history;
      this.error = "";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code || e });
    }
    this.render();
  }

  device(id) {
    return this.devices.find((d) => d.id === id);
  }

  async openPlan(oldId, newId, mapping) {
    if (!oldId || !newId || oldId === newId) {
      this.error = this.t("sameDevice");
      return this.render();
    }
    this.oldId = oldId;
    this.newId = newId;
    try {
      this.plan = await this.ws("plan", { old: oldId, new: newId, ...(mapping ? { mapping } : {}) });
      this.mapping = { ...this.plan.mapping };
      this.view = "match";
      this.error = "";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
  }

  async doReplace() {
    const picked = Object.values(this.mapping).filter(Boolean);
    if (picked.length !== new Set(picked).size) {
      this.error = this.t("duplicate");
      return this.render();
    }
    this.view = "working";
    this.render();
    try {
      this.result = await this.ws("replace", { old: this.oldId, new: this.newId, mapping: this.mapping, remove_old: this.removeOld, rename_z2m: Boolean(this.plan.new.z2m && this.renameZ2m) });
      this.result.name = this.plan.old.name;
      this.view = "done";
      this.error = "";
    } catch (e) {
      this.view = "match";
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
    this.load();
  }

  async undo(id) {
    try {
      await this.ws("undo", { record: id });
      this.view = "home";
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.load();
  }

  icon(e) {
    return e.icon || CLASS_ICON[e.device_class] || DOMAIN_ICON[e.domain] || "mdi:shape";
  }

  // ---------- views ----------

  homeView() {
    const dead = this.devices.filter((d) => d.dead).sort((a, b) => (b.twins?.length || 0) - (a.twins?.length || 0));
    const deadCards = dead.length
      ? dead.map((d) => {
          const twin = d.twins?.length ? this.device(d.twins[0]) : null;
          return `
          <div class="card dead-card">
            <div class="dev-head">
              <div class="dot red"></div>
              <div class="grow">
                <div class="dev-name">${esc(d.name)}</div>
                <div class="muted">${esc([d.area, d.model, d.integration_title].filter(Boolean).join(" · "))}</div>
                <div class="muted small">${esc(this.t("deadFor", { t: d.dead_since ? this.ago(d.dead_since) : "?" }))}</div>
              </div>
            </div>
            ${twin ? `
              <div class="twin"><ha-icon icon="mdi:auto-fix"></ha-icon><div class="grow"><div class="small muted">${this.t("twin")}</div><b>${esc(twin.name)}</b></div></div>
              <button class="primary full" data-act="plan" data-old="${d.id}" data-new="${twin.id}">${esc(this.t("replaceWith", { name: twin.name }))}</button>`
            : `<button class="ghost full" data-act="pick" data-old="${d.id}">${this.t("pickReplacement")}</button>`}
          </div>`;
        }).join("")
      : `<div class="card empty"><ha-icon icon="mdi:check-circle"></ha-icon>${this.t("noDead")}</div>`;
    const history = this.historyItems.map((h) => `
      <div class="hist">
        <ha-icon icon="mdi:swap-horizontal"></ha-icon>
        <div class="grow"><b>${esc(h.old_device.name)}</b> → ${esc(h.new_device.model || h.new_device.name)}
          <div class="muted small">${new Date(h.at * 1000).toLocaleString(this._hass.language)} · ${this.t("moved", { n: h.moved })}</div></div>
        ${h.undone ? `<span class="tag">${this.t("undone")}</span>` : `<button class="ghost small-btn" data-act="undo" data-id="${h.id}">${this.t("undo")}</button>`}
      </div>`).join("");
    return `
      <div class="hero card">
        <div class="hero-icon"><ha-icon icon="mdi:swap-horizontal-circle"></ha-icon></div>
        <div class="grow"><h2>${this.t("heroTitle")}</h2><p class="muted">${this.t("heroText")}</p>
        <div class="btns"><button class="primary" data-act="pick">${this.t("start")}</button>
        <button class="ghost" data-act="migrate"><ha-icon icon="mdi:transfer"></ha-icon>${this.t("migrateStart")}</button></div></div>
      </div>
      <h3>${this.t("dead")} ${dead.length ? `<span class="count">${dead.length}</span>` : ""}</h3>
      <div class="grid">${deadCards}</div>
      ${history ? `<h3>${this.t("history")}</h3><div class="card list">${history}</div>` : ""}`;
  }

  pickView() {
    const old = this.oldId && this.device(this.oldId);
    const sources = [...new Map(this.devices.filter((d) => d.integration).map((d) => [d.integration, d.integration_title])).entries()];
    return `
      ${old ? `<div class="card chosen"><div class="dev-head"><ha-icon icon="mdi:devices"></ha-icon><div class="grow"><div class="muted small">${this.t("old")}</div><div class="dev-name">${esc(old.name)}</div>
        <div class="muted small">${esc([old.area, old.model, old.integration_title].filter(Boolean).join(" · "))}</div></div>
        <button class="ghost small-btn" data-act="changeOld">${this.t("change")}</button></div></div>` : ""}
      <h3>${old ? this.t("pickNew") : this.t("pickOld")}</h3>
      <div class="filters">
        <div class="search"><ha-icon icon="mdi:magnify"></ha-icon><input id="q" type="search" placeholder="${this.t("search")}" value="${esc(this.query)}"></div>
        <select id="src"><option value="">${this.t("allIntegrations")}</option>${sources.map(([k, v]) => `<option value="${esc(k)}" ${k === this.srcFilter ? "selected" : ""}>${esc(v || k)}</option>`).join("")}</select>
      </div>
      <div class="pick-list" id="list">${this.pickList()}</div>
      <div class="actions"><button class="ghost" data-act="home">${this.t("back")}</button></div>`;
  }

  pickList() {
    const old = this.oldId && this.device(this.oldId);
    const q = this.query.trim().toLowerCase();
    let list = this.devices.filter((d) => (!this.srcFilter || d.integration === this.srcFilter)
      && (!q || [d.name, d.area, d.model, d.manufacturer, d.integration_title].join(" ").toLowerCase().includes(q)));
    const day = Date.now() / 1000 - 86400;
    const tags = (d) => {
      const out = [];
      if (old && d.hardware?.some((k) => old.hardware?.includes(k))) out.push(`<span class="tag green">${this.t("sameHardware")}</span>`);
      else if (old && d.model && d.model === old.model) out.push(`<span class="tag blue">${this.t("sameModel")}</span>`);
      if (d.dead) out.push(`<span class="tag red">${this.t("deadTag")}</span>`);
      else if (d.created > day) out.push(`<span class="tag blue">${this.t("newTag")}</span>`);
      return out.join("");
    };
    if (old) {
      const score = (d) => (d.hardware?.some((k) => old.hardware?.includes(k)) ? 1e12 : 0) + (d.model && d.model === old.model ? 1e11 : 0) + d.created;
      list = list.filter((d) => d.id !== old.id && !d.dead).sort((a, b) => score(b) - score(a));
    } else {
      list = list.sort((a, b) => (b.dead - a.dead) || a.name.localeCompare(b.name));
    }
    if (!list.length) return `<div class="card empty">${this.t("noResults")}</div>`;
    return list.slice(0, 60).map((d) => `
      <button class="devpick" data-act="choose" data-id="${d.id}">
        <span class="dot ${d.dead ? "red" : "green"}"></span>
        <span class="grow"><span class="dev-name">${esc(d.name)}</span>
          <span class="muted small">${esc([d.area, [d.manufacturer, d.model].filter(Boolean).join(" "), d.integration_title].filter(Boolean).join(" · "))}</span></span>
        <span class="tags">${tags(d)}</span><ha-icon icon="mdi:chevron-right"></ha-icon>
      </button>`).join("");
  }

  migrateView() {
    const sources = [...new Map(this.devices.filter((d) => d.integration).map((d) => [d.integration, d.integration_title])).entries()];
    const opts = (sel) => sources.map(([k, v]) => `<option value="${esc(k)}" ${k === sel ? "selected" : ""}>${esc(v || k)}</option>`).join("");
    const plan = this.migratePlan;
    const name = (k) => esc((sources.find(([x]) => x === k) || [k, k])[1] || k);
    let result = "";
    if (plan) {
      const rows = plan.pairs.map((p) => `
        <label class="mrow"><input type="checkbox" data-pair="${p.old.id}" ${this.migrateSelected.has(p.old.id) ? "checked" : ""}><span class="box"></span>
          <span class="grow"><span class="dev-name">${esc(p.old.name)}</span>
            <span class="muted small">→ ${esc(p.new.name)} · ${this.t("by_" + p.by)} · ${this.t("entitiesMatched", { m: p.matched, t: p.total })}</span></span>
          ${p.old.area ? `<span class="tag">${esc(p.old.area)}</span>` : ""}</label>`).join("");
      result = plan.pairs.length ? `
        <div class="card">
          <div class="mhead"><h3 class="in">${this.t("pairsFound", { n: plan.pairs.length })}</h3>
            <span><button class="ghost small-btn" data-act="selectAll">${this.t("all")}</button> <button class="ghost small-btn" data-act="selectNone">${this.t("none")}</button></span></div>
          <div class="mrows">${rows}</div>
          ${plan.missing.length ? `<p class="muted small">${this.t("missing", { n: plan.missing.length, source: name(this.migrateSource), target: name(this.migrateTarget) })}</p>` : ""}
        </div>
        <div class="card">
          <label class="switch-row"><input type="checkbox" id="removeOld" ${this.removeOld ? "checked" : ""}><span class="switch"></span>
            <div class="grow"><b>${this.t("removeOld")}</b><div class="muted small">${this.t("removeOldHint")}</div></div></label>
          ${this.migrateTarget === "zigbee2mqtt" ? `<label class="switch-row sep"><input type="checkbox" id="renameZ2m" ${this.renameZ2m ? "checked" : ""}><span class="switch"></span>
            <div class="grow"><b>${this.t("renameZ2m")}</b><div class="muted small">${this.t("renameZ2mHint")}</div></div></label>` : ""}
        </div>
        <div class="actions sticky"><button class="primary big" data-act="doMigrate" ${this.migrateSelected.size ? "" : "disabled"}><ha-icon icon="mdi:transfer"></ha-icon>${this.t("moveN", { n: this.migrateSelected.size })}</button></div>`
        : `<div class="card empty">${this.t("noPairs", { target: name(this.migrateTarget) })}</div>`;
    }
    return `
      <div class="card">
        <h2>${this.t("migrateTitle")}</h2><p class="muted">${this.t("migrateText")}</p>
        <div class="fromto">
          <div><label>${this.t("from")}</label><select id="msrc">${opts(this.migrateSource)}</select></div>
          <ha-icon icon="mdi:arrow-right"></ha-icon>
          <div><label>${this.t("to")}</label><select id="mdst">${opts(this.migrateTarget)}</select></div>
        </div>
        <div class="actions"><button class="ghost" data-act="home">${this.t("back")}</button><button class="primary" data-act="findPairs">${this.t("findPairs")}</button></div>
      </div>
      ${result}`;
  }

  migrateDoneView() {
    const r = this.result;
    return `
      <div class="card center done">
        <div class="check"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M15 27l7 7 15-16"/></svg></div>
        <h2>${this.t("migrateDone", { d: r.devices })}</h2>
        <p class="muted">${this.t("migrateDoneText", { n: r.moved })}</p>
        <div class="actions"><button class="primary" data-act="home">${this.t("home")}</button></div>
      </div>`;
  }

  async findPairs() {
    this.migrateSource = this.shadowRoot.getElementById("msrc").value;
    this.migrateTarget = this.shadowRoot.getElementById("mdst").value;
    if (!this.migrateSource || this.migrateSource === this.migrateTarget) {
      this.error = this.t("sameDevice");
      return this.render();
    }
    try {
      this.migratePlan = await this.ws("migrate_plan", { source: this.migrateSource, target: this.migrateTarget });
      this.migrateSelected = new Set(this.migratePlan.pairs.map((p) => p.old.id));
    } catch (e) {
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
  }

  async doMigrate() {
    const pairs = this.migratePlan.pairs.filter((p) => this.migrateSelected.has(p.old.id)).map((p) => ({ old: p.old.id, new: p.new.id }));
    this.view = "working";
    this.render();
    try {
      this.result = await this.ws("migrate", { pairs, remove_old: this.removeOld, rename_z2m: this.migrateTarget === "zigbee2mqtt" && this.renameZ2m });
      this.view = "migrated";
      this.migratePlan = null;
    } catch (e) {
      this.view = "migrate";
      this.error = this.t("error", { e: e.message || e.code });
    }
    this.render();
    this.load();
  }

  deviceCard(d, kind) {
    return `
      <div class="card devcard ${kind}">
        <div class="dev-head"><ha-icon icon="${kind === "old" ? "mdi:devices" : "mdi:new-box"}"></ha-icon>
          <div class="grow"><div class="dev-name">${esc(d.name)}</div><div class="muted small">${esc([d.manufacturer, d.model].filter(Boolean).join(" "))}</div>
          <div class="muted small">${esc(d.integration_title || d.integration || "")}</div></div>
          ${kind === "old" && d.dead ? `<span class="tag red">${this.t("deadTag")}</span>` : ""}
          ${kind === "new" ? `<span class="tag blue">${this.t("tookOver")}</span>` : ""}
        </div>
      </div>`;
  }

  matchView() {
    const p = this.plan;
    const taken = new Set(Object.values(this.mapping).filter(Boolean));
    const rows = p.old_entities.map((o) => {
      const choice = this.mapping[o.entity_id];
      const options = p.new_entities.filter((n) => n.domain === o.domain);
      return `
        <div class="row ${choice ? "ok" : "gone"}">
          <div class="side">
            <ha-icon icon="${this.icon(o)}"></ha-icon>
            <div class="grow"><div class="ename">${esc(o.name || o.entity_id)}</div><code>${esc(o.entity_id)}</code></div>
          </div>
          <div class="mid"><ha-icon icon="${choice ? "mdi:arrow-left-bold" : "mdi:close"}"></ha-icon></div>
          <div class="side">
            <select data-old="${o.entity_id}">
              <option value="">${this.t("removed")}</option>
              ${options.map((n) => `<option value="${n.entity_id}" ${n.entity_id === choice ? "selected" : ""}>${esc(n.name || n.entity_id)}${n.state && n.state !== "unavailable" ? ` · ${esc(n.state)}${n.unit ? ` ${esc(n.unit)}` : ""}` : ""}</option>`).join("")}
            </select>
          </div>
        </div>`;
    }).join("");
    const own = p.new_entities.filter((n) => !taken.has(n.entity_id));
    return `
      <div class="pair">
        ${this.deviceCard(p.old, "old")}
        <div class="pair-arrow"><ha-icon icon="mdi:arrow-right-thick"></ha-icon></div>
        ${this.deviceCard(p.new, "new")}
      </div>
      <div class="card">
        <h3 class="in">${this.t("matchTitle")}</h3>
        <p class="muted">${this.t("matchText")}</p>
        <div class="rows">${rows}</div>
      </div>
      ${own.length ? `<div class="card"><h3 class="in">${this.t("keepsOwn")}</h3><div class="chips">${own.map((n) => `<span class="chip"><ha-icon icon="${this.icon(n)}"></ha-icon>${esc(n.name || n.entity_id)}</span>`).join("")}</div></div>` : ""}
      ${p.uses_device.length ? `<div class="card warn"><h3 class="in"><ha-icon icon="mdi:robot"></ha-icon> ${this.t("usesDevice")}</h3><ul>${p.uses_device.map((n) => `<li>${esc(n)}</li>`).join("")}</ul><p class="muted small">${this.t("usesDeviceHint")}</p></div>` : ""}
      <div class="card">
        <label class="switch-row"><input type="checkbox" id="removeOld" ${this.removeOld ? "checked" : ""}><span class="switch"></span>
          <div class="grow"><b>${this.t("removeOld")}</b><div class="muted small">${this.t("removeOldHint")}</div></div></label>
        ${p.new.z2m ? `<label class="switch-row sep"><input type="checkbox" id="renameZ2m" ${this.renameZ2m ? "checked" : ""}><span class="switch"></span>
          <div class="grow"><b>${this.t("renameZ2m")}</b><div class="muted small">${this.t("renameZ2mHint")}</div></div></label>` : ""}
      </div>
      <div class="actions sticky"><button class="ghost" data-act="back">${this.t("back")}</button>
        <button class="primary big" data-act="replace"><ha-icon icon="mdi:swap-horizontal"></ha-icon>${esc(this.t("replace", { name: p.old.name }))}</button></div>`;
  }

  workingView() {
    return `<div class="card center"><div class="spinner"></div><h2>${this.t("working")}</h2></div>`;
  }

  doneView() {
    const r = this.result;
    return `
      <div class="card center done">
        <div class="check"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="24"/><path d="M15 27l7 7 15-16"/></svg></div>
        <h2>${esc(this.t("doneTitle", { name: r.name }))}</h2>
        <p class="muted">${this.t("doneText", { n: r.moved })}</p>
        ${this.removeOld && !r.removed ? `<p class="warn-text">${this.t("keptOld")}</p>` : ""}
        <div class="actions"><button class="ghost" data-act="undo" data-id="${r.id}">${this.t("undo")}</button><button class="primary" data-act="home">${this.t("home")}</button></div>
        <p class="muted small">${this.t("undoHint")}</p>
      </div>`;
  }

  render() {
    if (!this._hass) return;
    const body = {
      home: () => this.homeView(), pick: () => this.pickView(), match: () => this.matchView(), working: () => this.workingView(),
      done: () => this.doneView(), migrate: () => this.migrateView(), migrated: () => this.migrateDoneView(),
    }[this.view]();
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>
      <div class="toolbar">${customElements.get("ha-menu-button") ? "<ha-menu-button></ha-menu-button>" : ""}<div class="tb-title">${this.t("title")}</div></div>
      <div class="content">${this.error ? `<div class="card error"><ha-icon icon="mdi:alert-circle"></ha-icon>${esc(this.error)}</div>` : ""}${body}</div>`;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) {
      menu.hass = this._hass;
      menu.narrow = this._narrow;
    }
    this.shadowRoot.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset)));
    this.shadowRoot.querySelectorAll("select[data-old]").forEach((el) =>
      el.addEventListener("change", () => {
        this.mapping[el.dataset.old] = el.value || null;
        this.error = "";
        this.render();
      }));
    const remove = this.shadowRoot.getElementById("removeOld");
    if (remove) remove.addEventListener("change", () => (this.removeOld = remove.checked));
    const rename = this.shadowRoot.getElementById("renameZ2m");
    if (rename) rename.addEventListener("change", () => (this.renameZ2m = rename.checked));
    const q = this.shadowRoot.getElementById("q");
    if (q) {
      q.addEventListener("input", () => {
        this.query = q.value;
        this.renderList();
      });
    }
    const src = this.shadowRoot.getElementById("src");
    if (src) {
      src.addEventListener("change", () => {
        this.srcFilter = src.value;
        this.renderList();
      });
    }
    this.shadowRoot.querySelectorAll("input[data-pair]").forEach((el) =>
      el.addEventListener("change", () => {
        if (el.checked) this.migrateSelected.add(el.dataset.pair);
        else this.migrateSelected.delete(el.dataset.pair);
        this.render();
      }));
  }

  renderList() {
    const list = this.shadowRoot.getElementById("list");
    list.innerHTML = this.pickList();
    list.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this.act(el.dataset)));
  }

  act(data) {
    this.error = "";
    if (data.act === "home") {
      this.view = "home";
      this.oldId = this.newId = "";
      this.load();
    } else if (data.act === "pick") {
      this.oldId = data.old || "";
      this.newId = "";
      this.query = "";
      this.view = "pick";
      this.render();
    } else if (data.act === "choose") {
      if (!this.oldId) {
        this.oldId = data.id;
        this.query = "";
        this.render();
      } else {
        this.openPlan(this.oldId, data.id);
      }
    } else if (data.act === "changeOld") {
      this.oldId = "";
      this.render();
    } else if (data.act === "back") {
      this.view = "pick";
      this.render();
    } else if (data.act === "migrate") {
      const sources = [...new Set(this.devices.map((d) => d.integration).filter(Boolean))];
      this.migrateSource ||= sources.includes("zha") ? "zha" : sources[0] || "";
      this.migrateTarget ||= sources.includes("zigbee2mqtt") ? "zigbee2mqtt" : sources.find((x) => x !== this.migrateSource) || "";
      this.view = "migrate";
      this.render();
    } else if (data.act === "findPairs") {
      this.findPairs();
    } else if (data.act === "selectAll" || data.act === "selectNone") {
      this.migrateSelected = new Set(data.act === "selectAll" ? this.migratePlan.pairs.map((p) => p.old.id) : []);
      this.render();
    } else if (data.act === "doMigrate") {
      this.doMigrate();
    } else if (data.act === "plan") {
      this.openPlan(data.old, data.new);
    } else if (data.act === "replace") {
      this.doReplace();
    } else if (data.act === "undo") {
      this.undo(data.id);
    }
  }
}

const STYLE = `
:host{display:block;min-height:100vh;background:var(--primary-background-color,#f3f5f8);color:var(--primary-text-color,#1c2430);font-family:var(--paper-font-body1_-_font-family,Roboto,"Noto Sans",sans-serif);
  --rd-red:var(--error-color,#db4437);--rd-green:var(--success-color,#43a047);--rd-blue:var(--primary-color,#03a9f4);--rd-amber:var(--warning-color,#ffa600)}
*{box-sizing:border-box}
.toolbar{display:flex;align-items:center;height:56px;padding:0 12px;background:var(--app-header-background-color,var(--primary-color,#03a9f4));color:var(--app-header-text-color,#fff);position:sticky;top:0;z-index:2}
.tb-title{font-size:20px;margin-left:8px}
.content{max-width:960px;margin:0 auto;padding:16px 16px 96px}
.card{background:var(--card-background-color,#fff);border-radius:var(--ha-card-border-radius,12px);box-shadow:var(--ha-card-box-shadow,0 1px 4px rgba(0,0,0,.1));border:1px solid var(--divider-color,transparent);padding:16px;margin-bottom:16px}
h2{margin:0 0 6px;font-size:22px}h3{margin:24px 4px 10px;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}h3.in{margin:0 0 6px}
p{margin:4px 0 12px;line-height:1.45}.muted{color:var(--secondary-text-color,#6b7686)}.small{font-size:13px}.grow{flex:1;min-width:0}
code{font-family:var(--code-font-family,monospace);font-size:12px;color:var(--secondary-text-color);word-break:break-all}
button{font:inherit;font-weight:500;border-radius:10px;padding:10px 18px;cursor:pointer;border:1px solid transparent;display:inline-flex;align-items:center;justify-content:center;gap:8px}
button.primary{background:var(--rd-blue);color:var(--text-primary-color,#fff)}button.primary:hover{filter:brightness(1.08)}
button.ghost{background:transparent;color:var(--rd-blue);border-color:var(--divider-color,#d0d7e0)}
button.full{width:100%;margin-top:12px}button.big{padding:13px 22px;font-size:16px}button.small-btn{padding:6px 12px;font-size:13px}
.hero{display:flex;gap:16px;align-items:flex-start;background:linear-gradient(135deg,rgba(3,169,244,.10),transparent 60%),var(--card-background-color,#fff)}
.hero-icon ha-icon{--mdc-icon-size:48px;color:var(--rd-blue)}
.count{background:var(--rd-red);color:#fff;border-radius:99px;font-size:12px;padding:1px 8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}.grid .card{margin:0}
.dev-head{display:flex;gap:12px;align-items:flex-start}.dev-name{font-weight:600;font-size:16px}
.dot{width:12px;height:12px;border-radius:50%;margin-top:5px;flex:none}.dot.red{background:var(--rd-red);box-shadow:0 0 0 4px rgba(219,68,55,.15)}
.twin{display:flex;gap:10px;align-items:center;margin-top:12px;padding:10px 12px;border-radius:10px;background:rgba(67,160,71,.10)}.twin ha-icon{color:var(--rd-green)}
.empty{display:flex;gap:10px;align-items:center;color:var(--secondary-text-color)}.empty ha-icon{color:var(--rd-green)}
.list{padding:4px 16px}.hist{display:flex;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--divider-color,#e6e9ee)}.hist:last-child{border:0}
.tag{font-size:12px;padding:3px 10px;border-radius:99px;background:var(--secondary-background-color,#eef1f5);white-space:nowrap}
.tag.red{background:rgba(219,68,55,.14);color:var(--rd-red)}.tag.blue{background:rgba(3,169,244,.14);color:var(--rd-blue)}
.pick label{display:block;font-size:13px;color:var(--secondary-text-color);margin:16px 0 6px}
select{width:100%;font:inherit;padding:10px 12px;border-radius:10px;border:1px solid var(--divider-color,#d0d7e0);background:var(--card-background-color,#fff);color:var(--primary-text-color)}
.arrow-down{text-align:center;margin-top:12px;color:var(--secondary-text-color)}
.actions{display:flex;gap:12px;justify-content:flex-end;margin-top:20px;flex-wrap:wrap}
.actions.sticky{position:sticky;bottom:0;padding:12px 0;background:linear-gradient(transparent,var(--primary-background-color,#f3f5f8) 30%)}
.pair{display:flex;gap:12px;align-items:stretch}.pair .card{flex:1;margin-bottom:16px}
.pair-arrow{align-self:center;color:var(--rd-blue);margin-bottom:16px}.pair-arrow ha-icon{--mdc-icon-size:32px}
.devcard.old{opacity:.75}.devcard.new{border:2px solid var(--rd-blue)}
.rows{display:flex;flex-direction:column;gap:8px}
.row{display:grid;grid-template-columns:1fr 36px 1fr;align-items:center;gap:8px;padding:10px;border-radius:10px;border-left:4px solid var(--rd-green);background:var(--secondary-background-color,#f6f8fa)}
.row.gone{border-left-color:var(--rd-red)}.row.gone .side:first-child .ename{text-decoration:line-through;opacity:.7}
.side{display:flex;gap:10px;align-items:center;min-width:0}.side ha-icon{color:var(--secondary-text-color);flex:none}
.mid{text-align:center;color:var(--rd-green)}.row.gone .mid{color:var(--rd-red)}
.ename{font-weight:500;overflow:hidden;text-overflow:ellipsis}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}.chip{display:inline-flex;gap:6px;align-items:center;padding:6px 12px;border-radius:99px;background:var(--secondary-background-color,#eef1f5);font-size:13px}.chip ha-icon{--mdc-icon-size:16px}
.warn{border-left:4px solid var(--rd-amber)}.warn ul{margin:6px 0;padding-left:20px}
.error{display:flex;gap:10px;align-items:center;border-left:4px solid var(--rd-red);color:var(--rd-red)}
.switch-row{display:flex;gap:14px;align-items:center;cursor:pointer}.switch-row input{display:none}
.switch{width:44px;height:24px;border-radius:12px;background:var(--divider-color,#c4cbd4);position:relative;flex:none;transition:.2s}
.switch:after{content:"";position:absolute;left:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:.2s}
input:checked+.switch{background:var(--rd-blue)}input:checked+.switch:after{left:23px}
.center{text-align:center;padding:40px 20px}.center .actions{justify-content:center}
.spinner{width:48px;height:48px;margin:0 auto 16px;border-radius:50%;border:4px solid var(--divider-color,#e0e0e0);border-top-color:var(--rd-blue);animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.check svg{width:84px;height:84px;margin-bottom:12px;animation:pop .5s cubic-bezier(.3,1.6,.6,1)}
.check circle{fill:rgba(67,160,71,.12);stroke:var(--rd-green);stroke-width:3}
.check path{fill:none;stroke:var(--rd-green);stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
@keyframes pop{from{transform:scale(.5)}}
.warn-text{color:var(--rd-amber)}
.btns{display:flex;gap:10px;flex-wrap:wrap}
.chosen{border-left:4px solid var(--rd-red)}
.filters{display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap}.filters select{width:auto;flex:0 1 220px}
.search{flex:1 1 240px;display:flex;align-items:center;gap:8px;padding:0 12px;border-radius:10px;border:1px solid var(--divider-color,#d0d7e0);background:var(--card-background-color,#fff)}
.search ha-icon{color:var(--secondary-text-color)}.search input{flex:1;border:0;outline:0;background:transparent;font:inherit;color:var(--primary-text-color);padding:11px 0;min-width:0}
.pick-list{display:flex;flex-direction:column;gap:8px}
.devpick{width:100%;text-align:left;display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#e3e7ec);color:var(--primary-text-color);font-weight:400}
.devpick:hover{border-color:var(--rd-blue)}.devpick .grow{display:flex;flex-direction:column;gap:2px}.devpick>ha-icon{color:var(--secondary-text-color)}
.devpick .dot{margin-top:0}.dot.green{background:var(--rd-green)}
.tags{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}.tag.green{background:rgba(67,160,71,.14);color:var(--rd-green)}
.fromto{display:flex;align-items:flex-end;gap:12px}.fromto>div{flex:1}.fromto>ha-icon{margin-bottom:12px;color:var(--rd-blue)}
.fromto label{display:block;font-size:13px;color:var(--secondary-text-color);margin-bottom:6px}
.mhead{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px}.mhead>span{display:flex;gap:6px;flex:none}
.mrows{display:flex;flex-direction:column}
.mrow{display:flex;align-items:center;gap:12px;padding:10px 4px;border-bottom:1px solid var(--divider-color,#eceff3);cursor:pointer}.mrow:last-child{border:0}
.mrow input{display:none}.mrow .grow{display:flex;flex-direction:column;gap:2px}
.box{width:22px;height:22px;border-radius:6px;border:2px solid var(--divider-color,#b8c0ca);flex:none;position:relative}
input:checked+.box{background:var(--rd-blue);border-color:var(--rd-blue)}input:checked+.box:after{content:"";position:absolute;left:6px;top:2px;width:6px;height:11px;border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}
.switch-row.sep{margin-top:14px;padding-top:14px;border-top:1px solid var(--divider-color,#eceff3)}
button[disabled]{opacity:.45;cursor:default}
@media (max-width:600px){
  .content{padding:12px 12px 96px}.hero{flex-direction:column}.pair{flex-direction:column;gap:0}.pair-arrow{transform:rotate(90deg);margin:-8px auto 8px}
  .row{grid-template-columns:1fr;gap:6px}.mid{display:none}.actions.sticky button{flex:1}
  .filters select{flex:1 1 100%}.devpick .tags{display:none}.devpick .tags:has(.green){display:flex}
}
`;

customElements.define("replace-device-panel", ReplaceDevicePanel);
