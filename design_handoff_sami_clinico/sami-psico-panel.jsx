// Sami clínico — Panel de triaje y lista de Estudiantes

/* ---------- Construcción de alertas a partir de los datos ---------- */

function buildAlerts() {
  const out = [];
  for (const s of PSICO_DATA.students) {
    const last = s.cycles[s.cycles.length - 1];
    const r = riesgoEstudiante(s);
    if (last.crisis) {
      out.push({ tipo: "crit", studentId: s.id, student: s, t: `${s.name} — señal de crisis`,
        s: "Marcó pensamientos de autolesión en la encuesta de cierre. Requiere contacto hoy.", when: pHaceCuanto(last.end), rank: 100 });
    } else if (r.cls === "severa" || r.cls === "alta") {
      out.push({ tipo: "crit", studentId: s.id, student: s, t: `${s.name} — sintomatología ${r.label.toLowerCase()}`,
        s: `PHQ-A ${last.phqa}/27 · GAD-7 ${last.gad7}/21 en el ciclo ${last.n}.`, when: pHaceCuanto(last.end), rank: 80 });
    } else if (r.cls === "moderada") {
      out.push({ tipo: "warn", studentId: s.id, student: s, t: `${s.name} — sintomatología moderada`,
        s: `PHQ-A ${last.phqa}/27 · GAD-7 ${last.gad7}/21. Sugerido seguimiento.`, when: pHaceCuanto(last.end), rank: 50 });
    }
    const dias = Math.round((pParse(PSICO_DATA.today) - pParse(s.ultimaActividad)) / 86400000);
    if (dias >= 14) {
      out.push({ tipo: "idle", studentId: s.id, student: s, t: `${s.name} — sin actividad`,
        s: `No escribe desde hace ${Math.floor(dias / 7)} semanas.`, when: pHaceCuanto(s.ultimaActividad), rank: 30 });
    }
  }
  return out.sort((a, b) => b.rank - a.rank);
}

/* ---------- Panel ---------- */

function PPanel({ onOpen, onNav }) {
  const students = PSICO_DATA.students;
  const alerts = buildAlerts();
  const criticas = alerts.filter((a) => a.tipo === "crit").length;
  const cerradosSemana = students.filter((s) => {
    const last = s.cycles[s.cycles.length - 1];
    return !last.encurso && (pParse(PSICO_DATA.today) - pParse(last.end)) / 86400000 <= 7;
  }).length;
  const enCurso = students.filter((s) => s.cycles[s.cycles.length - 1].encurso).length;

  const tiles = [
    { n: students.length, l: "Estudiantes a tu cargo" },
    { n: criticas, l: "Alertas que requieren atención", alarm: criticas > 0 },
    { n: cerradosSemana, l: "Ciclos cerrados esta semana" },
    { n: enCurso, l: "Ciclos en curso" },
  ];

  const fecha = pParse(PSICO_DATA.today);

  return (
    <div className="page" data-screen-label="Panel clínico">
      <div className="page-inner" style={{ maxWidth: 920 }}>
        <p className="sub" style={{ marginBottom: 2 }}>Sábado {fecha.getDate()} de {P_MESES[fecha.getMonth()]} de {fecha.getFullYear()}</p>
        <h1>Hola, {PSICO_DATA.pro.name.split(" ")[1]}</h1>
        <p className="sub">Esto es lo que pasó con tus estudiantes desde la última vez.</p>

        <div className="tiles">
          {tiles.map((t, i) => (
            <div key={i} className={"tile" + (t.alarm ? " alarm" : "")}>
              <div className="n">{t.n}</div>
              <div className="l">{t.l}</div>
            </div>
          ))}
        </div>

        <div className="panel-card" style={{ marginBottom: 22 }}>
          <div style={{ padding: "14px 18px 12px", borderBottom: "1px solid var(--line-soft)" }} className="section-h">
            <span>Requieren tu atención</span>
            <button className="more" onClick={() => onNav("alertas")}>Ver todas las alertas</button>
          </div>
          <div className="rowlist">
            {alerts.slice(0, 4).map((a, i) => (
              <button key={i} className={"alert-row " + a.tipo} onClick={() => onOpen(a.studentId)}>
                <span className="badge-ico">{a.tipo === "idle" ? PIc.moon : PIc.alert}</span>
                <span className="txt">
                  <span className="t">{a.t}</span>
                  <span className="s">{a.s}</span>
                </span>
                <span className="when">{a.when}</span>
                <span style={{ color: "var(--ink-3)" }}>{PIc.chev}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="section-h"><span>Todos tus estudiantes</span><button className="more" onClick={() => onNav("estudiantes")}>Ver lista completa</button></div>
        <div className="panel-card">
          <StudentTable students={students.slice(0, 4)} onOpen={onOpen} compact />
        </div>
      </div>
    </div>
  );
}

/* ---------- Tabla de estudiantes (reutilizable) ---------- */

function StudentTable({ students, onOpen }) {
  const ordenados = [...students].sort((a, b) => riesgoEstudiante(b).rank - riesgoEstudiante(a).rank);
  return (
    <>
      <div className="list-head">
        <span></span><span>Estudiante</span><span>PHQ-A</span><span>GAD-7</span><span>Estado</span><span></span>
      </div>
      <div className="rowlist">
        {ordenados.map((s) => {
          const last = s.cycles[s.cycles.length - 1];
          const r = riesgoEstudiante(s);
          const tr = tendencia(s);
          return (
            <button key={s.id} className="stu-row" onClick={() => onOpen(s.id)}>
              <span className="avatar" style={{ background: avatarColor(s.id) }}>{s.initials}</span>
              <span>
                <span className="name">{s.name}</span>
                <span className="meta-sm">{s.carrera} · {s.anio}</span>
              </span>
              <span className="score-cell"><span className="big">{last.phqa}</span><span className="cap"> /27</span></span>
              <span className="score-cell"><span className="big">{last.gad7}</span><span className="cap"> /21</span></span>
              <span style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "flex-start" }}>
                {last.crisis ? <span className="crisis-flag">{PIc.alert}Crisis</span> : <SevChip nivel={r.label} />}
                <span className={"trend " + tr.dir}>
                  {tr.dir === "up" ? "↑" : tr.dir === "down" ? "↓" : "→"} {tr.txt}
                </span>
              </span>
              <span className="chev">{PIc.chev}</span>
            </button>
          );
        })}
      </div>
    </>
  );
}

/* ---------- Pantalla Estudiantes ---------- */

function PEstudiantes({ onOpen }) {
  const [q, setQ] = pUseState("");
  const students = PSICO_DATA.students.filter((s) => s.name.toLowerCase().includes(q.toLowerCase()) || s.carrera.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="page" data-screen-label="Estudiantes">
      <div className="page-inner" style={{ maxWidth: 920 }}>
        <h1>Estudiantes</h1>
        <p className="sub">{PSICO_DATA.students.length} estudiantes a tu cargo. Ordenados por nivel de riesgo.</p>
        <div className="field" style={{ maxWidth: 320, marginBottom: 18 }}>
          <input placeholder="Buscar por nombre o carrera…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="panel-card">
          <StudentTable students={students} onOpen={onOpen} />
          {students.length === 0 && <p style={{ padding: "24px", fontSize: 13, color: "var(--ink-3)", textAlign: "center" }}>Sin resultados.</p>}
        </div>
      </div>
    </div>
  );
}

/* ---------- Pantalla Alertas ---------- */

function PAlertas({ onOpen }) {
  const alerts = buildAlerts();
  return (
    <div className="page" data-screen-label="Alertas">
      <div className="page-inner" style={{ maxWidth: 720 }}>
        <h1>Alertas</h1>
        <p className="sub">{alerts.filter((a) => a.tipo === "crit").length} críticas · {alerts.length} en total. Las más urgentes primero.</p>
        <div className="panel-card">
          <div className="rowlist">
            {alerts.map((a, i) => (
              <button key={i} className={"alert-row " + a.tipo} onClick={() => onOpen(a.studentId)}>
                <span className="badge-ico">{a.tipo === "idle" ? PIc.moon : PIc.alert}</span>
                <span className="txt">
                  <span className="t">{a.t}</span>
                  <span className="s">{a.s}</span>
                </span>
                <span className="when">{a.when}</span>
                <span style={{ color: "var(--ink-3)" }}>{PIc.chev}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PPanel, StudentTable, PEstudiantes, PAlertas, buildAlerts });
