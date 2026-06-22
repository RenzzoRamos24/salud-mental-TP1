// Sami — Mi historial: combo de período + un solo calendario + detalle al costado

const CICLOS = [
  {
    id: 3, nombre: "Ciclo 3",
    start: "2026-05-30", end: "2026-06-12",
    rango: "30 de mayo – 12 de junio de 2026",
    nota: "Terminaste este ciclo hoy.",
    cierre: true,
  },
  {
    id: 2, nombre: "Ciclo 2",
    start: "2026-05-12", end: "2026-05-25",
    rango: "12 – 25 de mayo de 2026",
    nota: "Tu segundo ciclo completo.",
  },
];

function enCiclo(iso, c) { return iso >= c.start && iso <= c.end; }

function isoDeFecha(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// Un solo calendario: las semanas que cubre el período elegido
function CalPeriodo({ ciclo, porFecha, onOpen }) {
  const ini = parseDate(ciclo.start);
  const fin = parseDate(ciclo.end);
  const desde = new Date(ini); desde.setDate(desde.getDate() - desde.getDay());           // domingo previo
  const hasta = new Date(fin); hasta.setDate(hasta.getDate() + (6 - hasta.getDay()));     // sábado posterior

  const celdas = [];
  for (let d = new Date(desde); d <= hasta; d.setDate(d.getDate() + 1)) {
    celdas.push({ iso: isoDeFecha(d), dia: d.getDate(), mes: d.getMonth() });
  }

  const titulo = ini.getMonth() === fin.getMonth()
    ? `${MESES[ini.getMonth()][0].toUpperCase()}${MESES[ini.getMonth()].slice(1)} ${ini.getFullYear()}`
    : `${MESES[ini.getMonth()][0].toUpperCase()}${MESES[ini.getMonth()].slice(1)} – ${MESES[fin.getMonth()]} ${fin.getFullYear()}`;

  return (
    <div>
      <div className="cal-title" style={{ marginTop: 4 }}>{titulo}</div>
      <div className="cal-grid">
        {DIAS_AB.map((d) => <div className="cal-dow" key={d}>{d}</div>)}
        {celdas.map((c) => {
          const dentro = enCiclo(c.iso, ciclo);
          const entry = dentro ? porFecha[c.iso] : null;
          const cls = [
            "cal-cell",
            entry ? "entry" : "",
            !entry && dentro ? "range" : "",
            c.iso === SAMI_DATA.today ? "today" : "",
            !dentro ? "future" : "",
          ].filter(Boolean).join(" ");
          return entry ? (
            <button key={c.iso} className={cls} title={entry.title || "Sin título"} onClick={() => onOpen(entry.id)}>{c.dia}</button>
          ) : (
            <div key={c.iso} className={cls}>{c.dia}</div>
          );
        })}
      </div>
    </div>
  );
}

function Historial({ entries, onNav, close }) {
  const closeDone = close && close.status === "done";
  const [cicloSel, setCicloSel] = React.useState(CICLOS[0].id);
  const ciclo = CICLOS.find((c) => c.id === cicloSel);

  const porFecha = {};
  for (const e of entries) if (!porFecha[e.date]) porFecha[e.date] = e;

  const abrir = (id) => onNav("diario", { selectId: id });
  const delCiclo = entries.filter((e) => enCiclo(e.date, ciclo)).sort((a, b) => (a.date < b.date ? -1 : 1));

  return (
    <div className="page" data-screen-label="Mi historial">
      <div className="page-inner" style={{ maxWidth: 880 }}>
        <h1>Mi historial</h1>
        <p className="sub">Elegí un período y mirá qué días escribiste. Esto solo lo ves vos.</p>

        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 28, alignItems: "start" }}>

          <div className="card" style={{ padding: "20px 24px 22px" }}>
            <div className="field" style={{ marginBottom: 18 }}>
              <label htmlFor="periodo">Período</label>
              <select id="periodo" value={cicloSel} onChange={(e) => setCicloSel(Number(e.target.value))}>
                {CICLOS.map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre} · {c.rango}</option>
                ))}
              </select>
            </div>

            <CalPeriodo ciclo={ciclo} porFecha={porFecha} onOpen={abrir} />

            <div style={{ display: "flex", gap: 18, marginTop: 16, fontSize: 12, color: "var(--ink-3)", alignItems: "center", flexWrap: "wrap" }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <i style={{ width: 12, height: 12, borderRadius: 4, background: "var(--accent)", display: "inline-block" }}></i>
                Escribiste — clic para releer
              </span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <i style={{ width: 12, height: 12, borderRadius: 4, background: "color-mix(in srgb, var(--accent) 11%, #fff)", display: "inline-block" }}></i>
                Días del ciclo
              </span>
            </div>
          </div>

          <div className="card">
            <div style={{ padding: "16px 20px 14px", borderBottom: "1px solid var(--line-soft)" }}>
              <div style={{ fontSize: 14.5, fontWeight: 700 }}>{ciclo.nombre}</div>
              <div style={{ fontSize: 12.5, color: "var(--ink-3)", marginTop: 2 }}>{ciclo.rango}</div>
              <div style={{ fontSize: 13, color: "var(--ink-2)", marginTop: 8, lineHeight: 1.55 }}>
                {ciclo.nota} Escribiste {delCiclo.length} de 14 días.
              </div>
              {ciclo.cierre && (
                <button onClick={() => onNav("encuesta")}
                        style={{ border: 0, background: "none", padding: 0, marginTop: 10, color: "var(--accent)", fontSize: 12.5, fontWeight: 600 }}>
                  {closeDone ? "Encuesta de cierre respondida · ver resultados" : "Contale a Sami cómo te fue →"}
                </button>
              )}
            </div>
            <div style={{ padding: "10px 20px 6px", fontSize: 11.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--ink-3)" }}>
              Entradas de este período
            </div>
            <div className="rowlist">
              {delCiclo.map((e) => (
                <button key={e.id} className="entry-row" onClick={() => abrir(e.id)}>
                  <span className="datebox">
                    <span className="dow">{dowAb(e.date)}</span>
                    <span className="num">{dayNum(e.date)}</span>
                  </span>
                  <span className="meta">
                    <span className="t">{e.title || "Sin título"}</span>
                    <span className="x">{(e.body || "").split("\n")[0]}</span>
                  </span>
                </button>
              ))}
              {delCiclo.length === 0 && (
                <p style={{ padding: "18px 20px", fontSize: 13, color: "var(--ink-3)" }}>No escribiste en este período.</p>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Historial });
