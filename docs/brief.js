(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (iso, o) => new Date(iso).toLocaleDateString("en-GB", o || { day: "numeric", month: "short", year: "numeric" });
  const GROUPS = [
    { id: "difc", name: "DIFC", color: "var(--s-difc)" },
    { id: "adgm", name: "ADGM (incl. Hub71)", short: "ADGM", color: "var(--s-adgm)" },
    { id: "dmcc", name: "DMCC (own)", short: "DMCC", color: "var(--s-dmcc)" },
    { id: "other", name: "Other free zones", short: "Others", color: "var(--s-other)" },
  ];
  let ZONES = {};

  const groupOf = (it) => it.zones.includes("difc") ? "difc" : it.zones.includes("adgm") ? "adgm" : it.zones.includes("dmcc") ? "dmcc" : "other";
  const isOwn = (it) => it.zones.every((z) => ZONES[z] && ZONES[z].self);
  const rank = (a, b) => (b.importance || 0) - (a.importance || 0) || b.score - a.score || (a.published < b.published ? 1 : -1);
  const zoneName = (z) => (ZONES[z] ? ZONES[z].name : z);

  function zoneTags(it) {
    return it.zones.map((z) => `<span class="tag ${z === "difc" || z === "adgm" ? "leader" : ""} ${ZONES[z] && ZONES[z].self ? "self" : ""}">${esc(zoneName(z))}</span>`).join("");
  }

  function renderHero(d, comp) {
    const ins = d.insights || {};
    const dates = d.items.map((i) => i.published).sort();
    // Ecosystem brands (e.g. Hub71) count under their parent zone (ADGM).
    const zonesActive = new Set(comp.map((i) => (ZONES[i.zones[0]] && ZONES[i.zones[0]].parent) || i.zones[0]));
    $("eyebrow").textContent = `AI competitor briefing · as of ${fmt(ins.as_of || d.generated_at)}`;
    $("headline").textContent = ins.headline || "AI moves by UAE free zones";
    $("lede").textContent = `Based on ${d.items.length} AI announcements (${comp.length} by competitors) across ${zonesActive.size} competitor free zones and DMCC, ${fmt(dates[0], { month: "short", year: "numeric" })}–${fmt(dates[dates.length - 1], { month: "short", year: "numeric" })}. Every item links to its source.`;
    $("updated").textContent = "Data updated " + fmt(d.generated_at);
    const leaders = comp.filter((i) => i.zones.includes("difc") || i.zones.includes("adgm")).length;
    const k = [
      [comp.length, "competitor AI moves tracked"],
      [zonesActive.size, "competitor zones active on AI"],
      [Math.round((leaders / Math.max(comp.length, 1)) * 100) + "%", "of moves made by DIFC & ADGM"],
      [comp.filter((i) => (i.importance || 0) >= 4).length, "strategic-grade moves (rated 4–5 of 5)"],
    ];
    $("kpis").innerHTML = k.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  }

  function renderScorecard(items) {
    const cards = GROUPS.map((g) => {
      const its = items.filter((i) => groupOf(i) === g.id).sort(rank);
      const top = its[0];
      const cats = [...new Set(its.map((i) => i.category))].slice(0, 4);
      return `<div class="score" style="--zc:${g.color}">
        <h3>${esc(g.name)} <span class="count">${its.length} move${its.length === 1 ? "" : "s"}</span></h3>
        ${top ? `<div class="flag"><a href="${esc(top.url)}" target="_blank" rel="noopener">${esc(top.title)}</a></div>
        <div class="hint">${fmt(top.published)} · ${esc(top.source)}</div>
        ${top.dmcc_angle && g.id !== "dmcc" ? `<div class="angle">${esc(top.dmcc_angle)}</div>` : ""}` : `<div class="hint">No AI moves tracked yet.</div>`}
        <div class="cats">${cats.map((c) => `<span class="tag cat">${esc(c)}</span>`).join("")}</div>
      </div>`;
    });
    $("scorecard").innerHTML = cards.join("");
  }

  function months(items, asOf) {
    const first = new Date(items.map((i) => i.published).sort()[0]);
    const last = new Date(asOf);
    const out = [];
    for (let d = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth(), 1)); d <= last; d.setUTCMonth(d.getUTCMonth() + 1)) {
      out.push(d.toISOString().slice(0, 7));
    }
    return out;
  }

  function renderChart(items, asOf) {
    const ms = months(items, asOf);
    const rows = ms.map((m) => {
      const r = { m };
      GROUPS.forEach((g) => { r[g.id] = items.filter((i) => i.published.slice(0, 7) === m && groupOf(i) === g.id).length; });
      r.total = GROUPS.reduce((s, g) => s + r[g.id], 0);
      return r;
    });
    const max = Math.max(1, ...rows.map((r) => r.total));
    const W = 520, H = 250, L = 28, R = 8, T = 18, B = 26;
    const cw = (W - L - R) / rows.length, bw = Math.min(46, cw * 0.62);
    const y = (v) => T + (H - T - B) * (1 - v / max);
    const step = max <= 5 ? 1 : Math.ceil(max / 4);
    let svg = "";
    for (let v = 0; v <= max; v += step) svg += `<line class="grid-line" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
    rows.forEach((r, i) => {
      const x = L + i * cw + (cw - bw) / 2;
      let acc = 0;
      const segs = GROUPS.filter((g) => r[g.id]);
      segs.forEach((g, si) => {
        const y0 = y(acc), y1 = y(acc + r[g.id]);
        const top = si === segs.length - 1;
        const h = Math.max(0, y0 - y1 - (top ? 0 : 2)); // 2px surface gap between stacked segments
        const yy = y1 + (top ? 0 : 0);
        svg += top
          ? `<path d="M${x},${yy + h} V${yy + 4} Q${x},${yy} ${x + 4},${yy} H${x + bw - 4} Q${x + bw},${yy} ${x + bw},${yy + 4} V${yy + h} Z" fill="${g.color}"/>`
          : `<rect x="${x}" y="${yy + 2}" width="${bw}" height="${Math.max(0, h)}" fill="${g.color}"/>`;
        acc += r[g.id];
      });
      if (r.total) svg += `<text class="total" x="${x + bw / 2}" y="${y(r.total) - 5}" text-anchor="middle">${r.total}</text>`;
      svg += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle">${new Date(r.m + "-01T00:00:00Z").toLocaleDateString("en-GB", { month: "short", timeZone: "UTC" })}</text>`;
      svg += `<rect class="hit" data-i="${i}" x="${L + i * cw}" y="${T}" width="${cw}" height="${H - T - B}" fill="transparent"/>`;
    });
    svg += `<line class="axis" x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}"/>`;
    const el = $("chart");
    el.setAttribute("viewBox", `0 0 ${W} ${H}`);
    el.innerHTML = svg;
    $("legend").innerHTML = GROUPS.map((g) => `<span><i style="background:${g.color}"></i>${esc(g.name)}</span>`).join("");

    const tip = $("tip");
    el.querySelectorAll(".hit").forEach((h) => {
      const show = (ev) => {
        const r = rows[+h.dataset.i];
        tip.innerHTML = `<b>${new Date(r.m + "-01T00:00:00Z").toLocaleDateString("en-GB", { month: "long", year: "numeric", timeZone: "UTC" })}</b>` +
          GROUPS.map((g) => `<div class="row"><span><i style="background:${g.color}"></i>${esc(g.short || g.name)}</span><span>${r[g.id]}</span></div>`).join("") +
          `<div class="row" style="border-top:1px solid var(--line);margin-top:4px;padding-top:4px"><span>Total</span><span>${r.total}</span></div>`;
        tip.style.display = "block";
        const box = $("chartwrap").getBoundingClientRect(), hb = h.getBoundingClientRect();
        let left = hb.left - box.left + hb.width / 2 + 10;
        if (left + 170 > box.width) left = hb.left - box.left - 170;
        tip.style.left = Math.max(0, left) + "px";
        tip.style.top = "10px";
        h.setAttribute("fill", "rgba(127,127,127,.08)");
      };
      const hide = () => { tip.style.display = "none"; h.setAttribute("fill", "transparent"); };
      h.addEventListener("mouseenter", show); h.addEventListener("mousemove", show); h.addEventListener("mouseleave", hide);
      h.addEventListener("touchstart", show, { passive: true });
    });

    $("charttable").innerHTML = `<table class="data"><thead><tr><th>Month</th>${GROUPS.map((g) => `<th class="n">${esc(g.short || g.name)}</th>`).join("")}<th class="n">Total</th></tr></thead><tbody>` +
      rows.map((r) => `<tr><td>${r.m}</td>${GROUPS.map((g) => `<td class="n">${r[g.id]}</td>`).join("")}<td class="n">${r.total}</td></tr>`).join("") + "</tbody></table>";
    $("tblbtn").onclick = () => {
      const t = $("charttable"), open = t.hidden;
      t.hidden = !open; $("chartwrap").hidden = open;
      $("tblbtn").textContent = open ? "Show chart" : "Show table";
      $("tblbtn").setAttribute("aria-expanded", String(open));
    };
  }

  function renderMix(comp) {
    const counts = {};
    comp.forEach((i) => { counts[i.category] = (counts[i.category] || 0) + 1; });
    const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const max = rows.length ? rows[0][1] : 1;
    $("mix").innerHTML = rows.map(([c, n]) => `<div class="hbar"><span>${esc(c)}</span><span class="track"><span class="fill" style="width:${(n / max) * 100}%"></span></span><span class="n">${n}</span></div>`).join("") +
      `<p class="hint" style="margin-top:12px">Competitor moves only (DMCC excluded). Each announcement is counted once under its main type.</p>`;
  }

  function renderInsights(d) {
    const ins = d.insights || { findings: [], recommendations: [] };
    $("f-sub").textContent = ins.author ? `${ins.author}, ${fmt(ins.as_of)}.` : "";
    $("findings").innerHTML = ins.findings.map((f) => `<div class="finding"><div class="tags">${f.zones.map((z) => `<span class="tag ${z === "difc" || z === "adgm" ? "leader" : ""}">${esc(zoneName(z))}</span>`).join("")}</div><h3>${esc(f.title)}</h3><p>${esc(f.text)}</p></div>`).join("");
    $("recs").innerHTML = ins.recommendations.map((r, i) => `<div class="rec"><div class="num">${i + 1}</div><div><h3>${esc(r.title)}</h3><p>${esc(r.text)}</p></div></div>`).join("");
  }

  function renderMoves(comp) {
    $("moves").innerHTML = comp.slice().sort(rank).slice(0, 6).map((i) => `<li class="it">
      <div class="date">${fmt(i.published, { day: "numeric", month: "short" })}<br><span class="sig ${i.score >= 7 ? "hi" : ""}" title="Signal score 0-10">signal ${i.score}</span></div>
      <div><div class="tags">${zoneTags(i)}<span class="tag cat">${esc(i.category)}</span></div>
        <h3><a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.title)}</a></h3>
        <div class="src">${esc(i.source)}${(i.counterparties || []).length ? " · with " + esc(i.counterparties.join(", ")) : ""}</div>
        ${i.ai_summary ? `<p>${esc(i.ai_summary)}</p>` : ""}
        ${i.dmcc_angle ? `<p class="angle">DMCC angle: ${esc(i.dmcc_angle)}</p>` : ""}</div></li>`).join("");
  }

  fetch("data/items.json", { cache: "no-store" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((d) => {
      d.zones.forEach((z) => { ZONES[z.id] = z; });
      const comp = d.items.filter((i) => !isOwn(i));
      renderHero(d, comp);
      renderScorecard(d.items);
      renderChart(d.items, (d.insights && d.insights.as_of) || d.generated_at);
      renderMix(comp);
      renderInsights(d);
      renderMoves(comp);
      const verified = d.items.filter((i) => i.verified).length;
      $("method").innerHTML = `Method: announcements are collected from 24 competitor newsrooms, government news agencies, 11 regional outlets and news search, filtered for AI relevance and classified by type. ${verified} of ${d.items.length} items were checked by hand against the source page (headline, date, key facts). Findings and recommendations are analyst judgement based on these items. <a href="how-it-works.html">How it works</a>.`;
    })
    .catch(() => { $("headline").textContent = "Briefing data is not available yet."; });
})();
