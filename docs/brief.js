(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (iso, o) => new Date(iso).toLocaleDateString("en-GB", o || { day: "numeric", month: "short", year: "numeric" });
  const fmtItem = (i, o) => (i.date_approx ? "≈ " + fmt(i.published, { month: "short", year: "numeric" }) : fmt(i.published, o));
  const GROUPS = [
    { id: "difc", name: "DIFC", color: "var(--s-difc)" },
    { id: "adgm", name: "ADGM (incl. Hub71)", short: "ADGM", color: "var(--s-adgm)" },
    { id: "dmcc", name: "DMCC", color: "var(--s-dmcc)" },
    { id: "other", name: "Other free zones", short: "Others", color: "var(--s-other)" },
  ];
  const EMIRATES = ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"];
  const ZONES = {};

  const rootZone = (z) => (ZONES[z] && ZONES[z].parent) || z;
  const groupOf = (it) => { const r = it.zones.map(rootZone); return r.includes("difc") ? "difc" : r.includes("adgm") ? "adgm" : r.includes("dmcc") ? "dmcc" : "other"; };
  const zoneName = (z) => (ZONES[z] ? ZONES[z].name : z);
  const newest = (a, b) => (a.published < b.published ? 1 : -1);
  const tag = (z) => `<span class="tag ${z === "difc" || z === "adgm" ? "leader" : ""}">${esc(zoneName(z))}</span>`;
  const freeZoneCount = (d) => d.zones.filter((z) => !z.parent).length;

  function renderHero(d) {
    const ins = d.insights || {};
    const dates = d.items.map((i) => i.published).sort();
    const active = new Set(d.items.flatMap((i) => i.zones.map(rootZone)));
    const emirates = new Set([...active].map((z) => ZONES[z] && ZONES[z].emirate).filter(Boolean));
    const span = (iso) => fmt(iso, { month: "short", year: "numeric" });
    $("eyebrow").textContent = `AI briefing · as of ${fmt(ins.as_of || d.generated_at)}`;
    $("headline").textContent = ins.headline || "AI announcements by UAE free zones";
    $("lede").textContent = `${d.items.length} AI announcements by ${active.size} of the UAE's ${freeZoneCount(d)} free zones, ${span(dates[0])} to ${span(dates[dates.length - 1])}. Every item links to its source.`;
    $("updated").textContent = "Data updated " + fmt(d.generated_at);
    const k = [
      [d.items.length, "AI announcements tracked"],
      [active.size, "free zones with AI announcements"],
      [emirates.size, "emirates represented"],
      [d.items.filter((i) => (i.importance || 0) >= 4).length, "major announcements (zone-wide or large-scale)"],
    ];
    $("kpis").innerHTML = k.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  }

  function renderFindings(d) {
    const ins = d.insights || {};
    $("f-sub").textContent = ins.author ? `${ins.author}, ${fmt(ins.as_of || d.generated_at)}.` : "";
    $("findings").innerHTML = (ins.findings || []).map((f) => `<div class="finding"><div class="tags">${(f.zones || []).map(tag).join("")}</div><h3>${esc(f.title)}</h3><p>${esc(f.text)}</p></div>`).join("");
  }

  function renderLatest(items) {
    $("scorecard").innerHTML = GROUPS.map((g) => {
      const its = items.filter((i) => groupOf(i) === g.id).sort(newest);
      const pick = its.find((i) => (i.importance || 0) >= 3) || its[0];
      return `<div class="score" style="--zc:${g.color}">
        <h3>${esc(g.name)}</h3>
        <div class="hint">${its.length} AI announcement${its.length === 1 ? "" : "s"} tracked</div>
        ${pick ? `<div class="flag"><a href="${esc(pick.url)}" target="_blank" rel="noopener">${esc(pick.title)}</a></div>
        <div class="hint">${fmtItem(pick)} · ${esc(pick.source)}${g.id === "other" ? " · " + esc(zoneName(pick.zones[0])) : ""}</div>
        ${pick.ai_summary ? `<div class="angle">${esc(pick.ai_summary)}</div>` : ""}` : `<div class="hint">No AI announcements tracked yet.</div>`}
      </div>`;
    }).join("");
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
    const cw = (W - L - R) / rows.length, bw = Math.min(36, cw * 0.62);
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
        const h = Math.max(0, y0 - y1 - (si ? 2 : 0)); // 2px surface gap between stacked segments
        svg += top
          ? `<path d="M${x},${y1 + h} V${y1 + 4} Q${x},${y1} ${x + 4},${y1} H${x + bw - 4} Q${x + bw},${y1} ${x + bw},${y1 + 4} V${y1 + h} Z" fill="${g.color}"/>`
          : `<rect x="${x}" y="${y1}" width="${bw}" height="${h}" fill="${g.color}"/>`;
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
      const show = () => {
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

  function renderMix(items) {
    const counts = {};
    items.forEach((i) => { counts[i.category] = (counts[i.category] || 0) + 1; });
    const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const max = rows.length ? rows[0][1] : 1;
    $("mix").innerHTML = rows.map(([c, n]) => `<div class="hbar"><span>${esc(c)}</span><span class="track"><span class="fill" style="width:${(n / max) * 100}%"></span></span><span class="n">${n}</span></div>`).join("") +
      `<p class="hint" style="margin-top:12px">Each announcement is counted once, under its main type.</p>`;
  }

  function renderMajor(items) {
    $("moves").innerHTML = items.filter((i) => (i.importance || 0) >= 4).sort(newest).slice(0, 10).map((i) => `<li class="it">
      <div class="date">${fmtItem(i, { day: "numeric", month: "short" })}</div>
      <div><div class="tags">${i.zones.map(tag).join("")}<span class="tag cat">${esc(i.category)}</span></div>
        <h3><a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.title)}</a></h3>
        <div class="src">${esc(i.source)}${(i.counterparties || []).length ? " · with " + esc(i.counterparties.join(", ")) : ""}</div>
        ${i.ai_summary ? `<p>${esc(i.ai_summary)}</p>` : ""}</div></li>`).join("");
  }

  function renderZones(d) {
    const counts = {};
    d.items.forEach((i) => new Set(i.zones).forEach((z) => { counts[z] = (counts[z] || 0) + 1; }));
    const active = d.zones.filter((z) => !z.parent && (counts[z.id] || d.zones.some((c) => c.parent === z.id && counts[c.id]))).length;
    $("z-sub").textContent = `All ${freeZoneCount(d)} UAE free zones across 7 emirates are monitored (plus the Hub71 ecosystem in ADGM); ${active} have AI announcements since January 2026. Numbers are AI announcements tracked per zone.`;
    $("zones").innerHTML = EMIRATES.map((em) => {
      const zs = d.zones.filter((z) => z.emirate === em).sort((a, b) => (counts[b.id] || 0) - (counts[a.id] || 0) || a.name.localeCompare(b.name));
      return `<div class="finding"><h3>${esc(em)} <span class="hint">· ${zs.filter((z) => !z.parent).length} free zones</span></h3>
        <ul class="zlist">${zs.map((z) => `<li class="${counts[z.id] ? "" : "zero"}"><span>${esc(z.name)}${z.parent ? ` <span class="hint">(part of ${esc(zoneName(z.parent))})</span>` : ""}</span><b>${counts[z.id] || "–"}</b></li>`).join("")}</ul></div>`;
    }).join("");
  }

  (window.FZ_DATA ? Promise.resolve(window.FZ_DATA) : fetch("data/items.json", { cache: "no-store" }).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); }))
    .then((d) => {
      d.zones.forEach((z) => { ZONES[z.id] = z; });
      renderHero(d);
      renderFindings(d);
      renderChart(d.items, (d.insights && d.insights.as_of) || d.generated_at);
      renderMix(d.items);
      renderLatest(d.items);
      renderMajor(d.items);
      renderZones(d);
      const cov = d.coverage || [];
      const newsrooms = cov.filter((c) => c.kind === "Official newsroom").length;
      const verified = d.items.filter((i) => i.verified).length;
      $("method").innerHTML = `Method: announcements are collected from ${newsrooms} free zone newsrooms, government news agencies, regional outlets and news search covering all ${freeZoneCount(d)} free zones, then filtered for AI relevance and classified by type. ${verified} of ${d.items.length} items were checked by hand against the source page (headline, date, key facts); "≈" marks a date confirmed only to the month. <a href="how-it-works.html">How it works</a>.`;
    })
    .catch((e) => { console.error(e); $("headline").textContent = "Briefing data is not available yet."; });
})();
