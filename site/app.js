(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const DAY = 864e5;
  const LEADERS = new Set(["difc", "adgm"]);
  const state = { q: "", zone: "", period: 30, sort: "date", leaders: false, self: false, cats: new Set() };
  let DATA = null, ZONES = {};

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const age = (iso) => Date.now() - new Date(iso).getTime();
  const isSelfOnly = (it) => it.zones.every((z) => ZONES[z] && ZONES[z].self);
  const fmtDate = (iso) => new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });

  // Filters persist per viewer; storage can be unavailable, so never depend on it.
  function loadPrefs() {
    try { Object.assign(state, JSON.parse(localStorage.getItem("fzaw-prefs") || "{}"), { cats: new Set() }); } catch (e) {}
  }
  function savePrefs() {
    try { const { cats, q, ...rest } = state; localStorage.setItem("fzaw-prefs", JSON.stringify(rest)); } catch (e) {}
  }

  function baseFilter(it, ignoreCats) {
    if (!state.self && isSelfOnly(it)) return false;
    if (state.period && age(it.published) > state.period * DAY) return false;
    if (state.zone && !it.zones.includes(state.zone)) return false;
    if (state.leaders && !it.zones.some((z) => LEADERS.has(z))) return false;
    if (!ignoreCats && state.cats.size && !state.cats.has(it.category)) return false;
    if (state.q) {
      const hay = [it.title, it.source, it.summary, it.ai_summary, it.dmcc_angle, (it.players || []).join(" "),
        (it.counterparties || []).join(" "), it.zones.map((z) => ZONES[z] ? ZONES[z].name : z).join(" ")].join(" ").toLowerCase();
      if (!state.q.toLowerCase().split(/\s+/).every((t) => hay.includes(t))) return false;
    }
    return true;
  }

  function renderKpis() {
    const comp = DATA.items.filter((i) => !isSelfOnly(i));
    const within = (d) => comp.filter((i) => age(i.published) <= d * DAY);
    const m30 = within(30);
    const k = [
      [within(1).length, "new in last 24h"],
      [within(7).length, "competitor items, 7 days"],
      [m30.filter((i) => i.zones.includes("difc")).length, "DIFC items, 30 days"],
      [m30.filter((i) => i.zones.includes("adgm")).length, "ADGM items, 30 days"],
    ];
    $("kpis").innerHTML = k.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  }

  function renderZoneBars() {
    const counts = {};
    DATA.items.forEach((i) => {
      if (isSelfOnly(i) || age(i.published) > 30 * DAY) return;
      i.zones.forEach((z) => { if (ZONES[z] && !ZONES[z].self) counts[z] = (counts[z] || 0) + 1; });
    });
    const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const max = rows.length ? rows[0][1] : 1;
    $("zonebars").innerHTML = rows.length ? rows.map(([z, n]) => `
      <button class="zb ${LEADERS.has(z) ? "leader" : ""} ${state.zone === z ? "on" : ""}" data-z="${z}" title="Filter to ${esc(ZONES[z].name)}">
        <span class="zn">${esc(ZONES[z].name)}</span>
        <span class="track"><span class="fill" style="width:${Math.max(3, (n / max) * 100)}%"></span></span>
        <span class="n">${n}</span>
      </button>`).join("") : `<p class="hint">No competitor items in the last 30 days yet.</p>`;
  }

  function renderCats() {
    const counts = {};
    DATA.items.filter((i) => baseFilter(i, true)).forEach((i) => { counts[i.category] = (counts[i.category] || 0) + 1; });
    $("cats").innerHTML = DATA.categories.filter((c) => counts[c] || state.cats.has(c)).map((c) =>
      `<button class="chip ${state.cats.has(c) ? "on" : ""}" data-c="${esc(c)}" aria-pressed="${state.cats.has(c)}">${esc(c)}<span class="c">${counts[c] || 0}</span></button>`
    ).join("");
  }

  function renderList() {
    let items = DATA.items.filter((i) => baseFilter(i, false));
    if (state.sort === "score") items = items.slice().sort((a, b) => b.score - a.score || (a.published < b.published ? 1 : -1));
    $("count").textContent = `${items.length} item${items.length === 1 ? "" : "s"}`;
    $("empty").hidden = items.length > 0;
    $("list").innerHTML = items.slice(0, 300).map((i) => {
      const zoneTags = i.zones.map((z) => {
        const zo = ZONES[z] || { name: z };
        return `<span class="tag ${LEADERS.has(z) ? "leader" : ""} ${zo.self ? "self" : ""}">${esc(zo.name)}</span>`;
      }).join("");
      const partners = (i.counterparties && i.counterparties.length ? i.counterparties : i.players || []).slice(0, 4);
      const also = i.also_in && i.also_in.length ? ` · also in ${esc(i.also_in.slice(0, 3).join(", "))}` : "";
      return `<li class="it">
        <div class="date">${fmtDate(i.published)}<br><span class="sig ${i.score >= 7 ? "hi" : ""}" title="Signal score">signal ${i.score}</span></div>
        <div>
          <div class="tags">${zoneTags}<span class="tag cat">${esc(i.category)}</span></div>
          <h3><a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.title)}</a></h3>
          <div class="src">${esc(i.source)}${also}${partners.length ? " · with " + esc(partners.join(", ")) : ""}</div>
          ${i.ai_summary ? `<p>${esc(i.ai_summary)}</p>` : ""}
          ${i.dmcc_angle ? `<p class="angle">DMCC angle: ${esc(i.dmcc_angle)}</p>` : ""}
        </div>
      </li>`;
    }).join("");
  }

  function render() { renderZoneBars(); renderCats(); renderList(); savePrefs(); }

  function syncControls() {
    $("q").value = state.q; $("zone").value = state.zone; $("period").value = String(state.period);
    $("sort").value = state.sort; $("leaders").checked = state.leaders; $("self").checked = state.self;
  }

  function bind() {
    $("q").addEventListener("input", (e) => { state.q = e.target.value.trim(); renderCats(); renderList(); });
    $("zone").addEventListener("change", (e) => { state.zone = e.target.value; render(); });
    $("period").addEventListener("change", (e) => { state.period = +e.target.value; render(); });
    $("sort").addEventListener("change", (e) => { state.sort = e.target.value; render(); });
    $("leaders").addEventListener("change", (e) => { state.leaders = e.target.checked; render(); });
    $("self").addEventListener("change", (e) => { state.self = e.target.checked; render(); });
    $("zonebars").addEventListener("click", (e) => {
      const b = e.target.closest(".zb"); if (!b) return;
      state.zone = state.zone === b.dataset.z ? "" : b.dataset.z; $("zone").value = state.zone; render();
    });
    $("cats").addEventListener("click", (e) => {
      const b = e.target.closest(".chip"); if (!b) return;
      const c = b.dataset.c; state.cats.has(c) ? state.cats.delete(c) : state.cats.add(c); render();
    });
  }

  fetch("data/items.json", { cache: "no-store" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((data) => {
      DATA = data;
      data.zones.forEach((z) => { ZONES[z.id] = z; });
      $("zone").insertAdjacentHTML("beforeend", data.zones.map((z) => `<option value="${z.id}">${esc(z.name)}${z.self ? " (own)" : ""}</option>`).join(""));
      $("updated").textContent = "Updated " + new Date(data.generated_at).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
      loadPrefs(); syncControls(); renderKpis(); bind(); render();
    })
    .catch(() => { $("updated").textContent = "No data yet - the first daily run hasn't happened."; $("empty").hidden = false; });
})();
