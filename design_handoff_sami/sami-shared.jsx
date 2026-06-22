// Sami — compartidos: iconos, fechas, hooks de datos, topbar

const { useState, useEffect, useMemo, useRef, useCallback } = React;

/* ---------- Iconos (trazo simple, 18px) ---------- */

function Ic({ d, size = 18, sw = 1.7 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
      {d}
    </svg>
  );
}

const Icons = {
  book: (s) => <Ic size={s} d={<><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></>} />,
  clock: (s) => <Ic size={s} d={<><circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></>} />,
  heart: (s) => <Ic size={s} d={<path d="M19.5 12.6 12 20l-7.5-7.4A5 5 0 1 1 12 6.3a5 5 0 1 1 7.5 6.3z"></path>} />,
  person: (s) => <Ic size={s} d={<><circle cx="12" cy="8" r="4"></circle><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"></path></>} />,
  phone: (s) => <Ic size={s} d={<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"></path>} />,
  doc: (s) => <Ic size={s} d={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><path d="M14 2v6h6"></path></>} />,
  arrow: (s) => <Ic size={s} d={<path d="M5 12h14M13 6l6 6-6 6"></path>} />,
};

/* ---------- Fechas ---------- */

const MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
const DIAS = ["domingo","lunes","martes","miércoles","jueves","viernes","sábado"];
const DIAS_AB = ["dom","lun","mar","mié","jue","vie","sáb"];

function parseDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}
function fmtLong(iso) {
  const d = parseDate(iso);
  const s = `${DIAS[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`;
  return s[0].toUpperCase() + s.slice(1);
}
function fmtMonth(iso) {
  const d = parseDate(iso);
  return `${MESES[d.getMonth()][0].toUpperCase()}${MESES[d.getMonth()].slice(1)} ${d.getFullYear()}`;
}
function dayNum(iso) { return parseDate(iso).getDate(); }
function dowAb(iso) { return DIAS_AB[parseDate(iso).getDay()]; }
function daysBetween(a, b) { return Math.round((parseDate(b) - parseDate(a)) / 86400000); }
function wordCount(s) { return (s || "").trim() ? s.trim().split(/\s+/).length : 0; }

/* ---------- Diario persistente ---------- */

const DIARY_KEY = "sami-diary-v1";
const CYCLE_KEY = "sami-cycle-v1";

function readStore(key) {
  try { return JSON.parse(localStorage.getItem(key)) || {}; } catch { return {}; }
}

function useDiary() {
  const [overrides, setOverrides] = useState(() => readStore(DIARY_KEY));

  const entries = useMemo(() => {
    const base = {};
    for (const e of SAMI_DATA.entries) base[e.id] = e;
    for (const [id, e] of Object.entries(overrides)) base[id] = e;
    return Object.values(base).sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : a.id < b.id ? 1 : -1));
  }, [overrides]);

  const saveEntry = useCallback((entry) => {
    setOverrides((prev) => {
      const next = { ...prev, [entry.id]: entry };
      localStorage.setItem(DIARY_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return { entries, saveEntry };
}

function useCycleSurvey() {
  const [answers, setAnswers] = useState(() => readStore(CYCLE_KEY));
  const submit = useCallback((date, values) => {
    setAnswers((prev) => {
      const next = { ...prev, [date]: values };
      localStorage.setItem(CYCLE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);
  return { answers, submit };
}

function cycleInfo() {
  const { start, length } = SAMI_DATA.cycle;
  const day = Math.min(daysBetween(start, SAMI_DATA.today) + 1, length);
  return { day, length, start };
}

/* ---------- Topbar ---------- */

const NAV = [
  ["inicio", "Inicio"],
  ["diario", "Diario"],
  ["historial", "Mi historial"],
  ["recursos", "Recursos"],
];

function Topbar({ route, onNav }) {
  const u = SAMI_DATA.user;
  return (
    <header className="topbar">
      <button className="wordmark" onClick={() => onNav("inicio")}>
        <span className="mark">S</span>
        <span>Sami</span>
      </button>
      <nav className="topnav">
        {NAV.map(([id, label]) => (
          <button key={id} className={route === id ? "on" : ""} onClick={() => onNav(id)}>{label}</button>
        ))}
      </nav>
      <span className="spacer"></span>
      <button className={"userchip" + (route === "perfil" ? " on" : "")} onClick={() => onNav("perfil")} title="Perfil">
        <span className="avatar">{u.initials}</span>
        <span>{u.name.split(" ")[0]}</span>
      </button>
    </header>
  );
}

/* ---------- Toast ---------- */

function Toast({ msg }) {
  if (!msg) return null;
  return <div className="toast">{msg}</div>;
}

Object.assign(window, {
  Icons, Topbar, Toast,
  MESES, DIAS, DIAS_AB,
  parseDate, fmtLong, fmtMonth, dayNum, dowAb, daysBetween, wordCount,
  useDiary, useCycleSurvey, cycleInfo,
});
