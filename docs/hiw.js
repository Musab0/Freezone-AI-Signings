(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const yes = (b) => (b ? '<span class="yes" aria-label="yes">✓</span>' : '<span class="no" aria-label="no">–</span>');

  fetch("data/items.json", { cache: "no-store" })
    .then((r) => r.json())
    .then((d) => {
      const zones = {};
      d.zones.forEach((z) => { zones[z.id] = z; });
      $("updated").textContent = "Data updated " + new Date(d.generated_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
      const cov = d.coverage || [];
      const official = cov.filter((c) => c.kind === "Official newsroom");
      const multi = official.filter((c) => [c.rss, c.listing, c.sitemap, c.search].filter(Boolean).length >= 2).length;
      const k = [
        [official.length, "official newsrooms scraped"],
        [cov.length - official.length, "agencies and outlets"],
        [Math.round((multi / Math.max(official.length, 1)) * 100) + "%", "of newsrooms with 2+ ways in"],
        ["$0", "hosting and scheduling cost"],
      ];
      $("kpis").innerHTML = k.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
      $("cov-sum").textContent = `${cov.length} sources · generated from the source registry in the code`;
      $("coverage").innerHTML = `<thead><tr><th>Source</th><th>Type</th><th>Zone</th><th>Domain</th><th>RSS</th><th>Listing</th><th>Sitemap</th><th>Search</th></tr></thead><tbody>` +
        cov.map((c) => `<tr><td>${esc(c.name)}</td><td>${esc(c.kind)}</td><td>${esc(c.zone ? (zones[c.zone] || {}).name || c.zone : "All")}</td><td>${esc(c.domain)}</td><td>${yes(c.rss)}</td><td>${yes(c.listing)}</td><td>${yes(c.sitemap)}</td><td>${yes(c.search)}</td></tr>`).join("") + "</tbody>";

      const h = d.health || { alerts: [], sources: [] };
      if (!h.sources.length) {
        $("health-sum").textContent = "Appears after the first automated run";
        $("alerts").innerHTML = `<p class="hint" style="margin:0">The scheduled job has not run on this deployment yet, so there are no live health results. The data shown on the briefing comes from the verified set. Run <code>python -m tracker.check</code> on any machine with internet access for a live check of every source.</p>`;
        return;
      }
      const n = (st) => h.sources.filter((x) => x.status === st).length;
      $("health-sum").textContent = `${n("ok")} ok · ${n("degraded")} degraded · ${n("down")} down`;
      const md = (t) => esc(t).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`(.+?)`/g, "<code>$1</code>");
      $("alerts").innerHTML = h.alerts.map((a) => `<div class="alert">${md(a)}</div>`).join("");
      const order = { down: 0, degraded: 1, ok: 2 };
      $("health").innerHTML = h.sources.filter((x) => !/-search:/.test(x.id)).sort((a, b) => order[a.status] - order[b.status] || a.name.localeCompare(b.name))
        .map((x) => `<div class="hs" title="${esc("Working: " + x.working.join(", "))}"><span class="dot ${x.status}"></span><span>${esc(x.name)}</span></div>`).join("");
    });
})();
