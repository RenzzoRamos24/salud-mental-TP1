// Sami clínico — helpers compartidos: severidad, topbar, gráfico de evolución

const { useState: pUseState, useMemo: pUseMemo, useCallback: pUseCallback } = React;

/* ---------- Severidad ---------- */

function nivelPhqa(score) {
  return PSICO_DATA.sevPhqa.find((r) => score <= r.hasta);
}
function nivelGad7(score) {
  return PSICO_DATA.sevGad7.find((r) => score <= r.hasta);
}
function sevClass(nivel) {
  if (/severa/i.test(nivel) && /moderada/i.test(nivel)) return "alta";
  if (/severa/i.test(nivel)) return "severa";
  if (/moderada/i.test(nivel)) return "moderada";
  if (/leve/i.test(nivel)) return "leve";
  return "minima";
}
function SevChip({ nivel }) {
  return <span className={"sev " + sevClass(nivel)}><span className="pip"></span>{nivel}</span>;
}

// prioridad de riesgo: crisis > severa > moderada-severa > moderada > leve > mínima
function riesgoEstudiante(s) {
  const last = s.cycles[s.cycles.length - 1];
  if (last.crisis) return { rank: 5, label: "Crisis", cls: "severa" };
  const p = nivelPhqa(last.phqa), g = nivelGad7(last.gad7);
  const peor = (p.hasta >= g.hasta ? p : g);
  const cls = sevClass(peor.nivel);
  const rank = { severa: 5, alta: 4, moderada: 3, leve: 2, minima: 1 }[cls];
  return { rank, label: peor.nivel, cls };
}

function tendencia(s) {
  if (s.cycles.length < 2) return { dir: "flat", txt: "Primer ciclo" };
  const a = s.cycles[s.cycles.length - 2].phqa;
  const b = s.cycles[s.cycles.length - 1].phqa;
  const d = b - a;
  if (d >= 3) return { dir: "up", txt: `+${d} en PHQ-A` };
  if (d <= -3) return { dir: "down", txt: `${d} en PHQ-A` };
  return { dir: "flat", txt: "Estable" };
}

const AVATAR_COLORS = ["#0d9488", "#5b8def", "#e8883a", "#8e6fd8", "#3aa66f", "#d3792c"];
function avatarColor(id) {
  let h = 0; for (const c of id) h = (h * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length;
  return AVATAR_COLORS[h];
}

/* ---------- Fechas (reusa los helpers globales si existen) ---------- */

const P_MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
function pParse(iso) { const [y,m,d] = iso.split("-").map(Number); return new Date(y, m-1, d); }
function pCorto(iso) { const d = pParse(iso); return `${d.getDate()} ${P_MESES[d.getMonth()].slice(0,3)}`; }
function pRango(a, b) { return `${pCorto(a)} – ${pCorto(b)}`; }
function pHaceCuanto(iso) {
  const dias = Math.round((pParse(PSICO_DATA.today) - pParse(iso)) / 86400000);
  if (dias <= 0) return "hoy";
  if (dias === 1) return "ayer";
  if (dias < 7) return `hace ${dias} días`;
  if (dias < 14) return "hace 1 semana";
  return `hace ${Math.floor(dias / 7)} semanas`;
}

/* ---------- Iconos extra ---------- */

const PIc = {
  grid: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>,
  people: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.2 2.7-5 6-5s6 1.8 6 5"/><path d="M16 5.2A3 3 0 0 1 16 11M21 20c0-2.6-1.6-4.3-4-4.8"/></svg>,
  bell: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9a6 6 0 1 1 12 0c0 5 2 6 2 6H4s2-1 2-6"/><path d="M10.5 19a1.7 1.7 0 0 0 3 0"/></svg>,
  alert: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>,
  moon: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.8A8 8 0 1 1 11.2 3 6.3 6.3 0 0 0 21 12.8z"/></svg>,
  chev: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 6l6 6-6 6"/></svg>,
  back: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>,
  lock: <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>,
};

/* ---------- Topbar clínico ---------- */

const P_NAV = [["panel","Panel"],["estudiantes","Estudiantes"],["alertas","Alertas"]];

function PTopbar({ route, onNav, alertCount }) {
  const u = PSICO_DATA.pro;
  return (
    <header className="topbar">
      <button className="wordmark" onClick={() => onNav("panel")}>
        <span className="mark">S</span>
        <span>Sami <span style={{ fontWeight: 500, color: "var(--ink-3)" }}>· Clínico</span></span>
      </button>
      <nav className="topnav">
        {P_NAV.map(([id, label]) => (
          <button key={id} className={route === id ? "on" : ""} onClick={() => onNav(id)}>
            {label}
            {id === "alertas" && alertCount > 0 && (
              <span style={{ marginLeft: 6, fontSize: 11, fontWeight: 700, background: "#c0392b", color: "#fff", borderRadius: 999, padding: "1px 6px" }}>{alertCount}</span>
            )}
          </button>
        ))}
      </nav>
      <span className="spacer"></span>
      <button className="userchip">
        <span className="avatar" style={{ background: "var(--accent)" }}>{u.initials}</span>
        <span>{u.name}</span>
      </button>
    </header>
  );
}

/* ---------- Gráfico de evolución (SVG, con bandas de severidad) ---------- */

function EvolChart({ cycles, metric }) {
  // metric: { key: "phqa"|"gad7", max, bands:[{hasta,color}] }
  const W = 460, H = 150, padL = 28, padR = 12, padT = 12, padB = 22;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const n = cycles.length;
  const x = (i) => padL + (n === 1 ? innerW / 2 : (innerW * i) / (n - 1));
  const y = (v) => padT + innerH - (innerH * v) / metric.max;

  const pts = cycles.map((c, i) => [x(i), y(c[metric.key])]);
  const line = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }}>
      {metric.bands.map((b, i) => {
        const top = y(b.hasta);
        const prev = i === 0 ? metric.max : metric.bands[i - 1].hasta;
        const bottom = y(b.hasta);
        const yTop = y(prev);
        return <rect key={i} x={padL} y={Math.min(yTop, bottom)} width={innerW} height={Math.abs(bottom - yTop)} fill={b.color} opacity="0.5" />;
      })}
      {[0, metric.max].map((v) => (
        <g key={v}>
          <line x1={padL} x2={W - padR} y1={y(v)} y2={y(v)} stroke="#d8d8de" strokeWidth="1" />
          <text x={padL - 6} y={y(v) + 3.5} textAnchor="end" fontSize="9.5" fill="#8e8e95">{v}</text>
        </g>
      ))}
      <path d={line} fill="none" stroke="var(--accent)" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />
      {pts.map((p, i) => (
        <g key={i}>
          <circle cx={p[0]} cy={p[1]} r="4" fill="#fff" stroke="var(--accent)" strokeWidth="2.2" />
          <text x={p[0]} y={H - 7} textAnchor="middle" fontSize="9.5" fill="#8e8e95">C{cycles[i].n}</text>
          <text x={p[0]} y={p[1] - 9} textAnchor="middle" fontSize="10.5" fontWeight="700" fill="var(--ink)">{cycles[i][metric.key]}</text>
        </g>
      ))}
    </svg>
  );
}

/* ---------- Toast ---------- */

function PToast({ msg }) {
  if (!msg) return null;
  return <div className="toast">{msg}</div>;
}

Object.assign(window, {
  nivelPhqa, nivelGad7, sevClass, SevChip, riesgoEstudiante, tendencia,
  avatarColor, P_MESES, pParse, pCorto, pRango, pHaceCuanto, PIc, PTopbar, EvolChart, Toast: PToast,
});
