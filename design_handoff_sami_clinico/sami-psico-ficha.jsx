// Sami clínico — Ficha clínica del estudiante

const NOTES_KEY = "sami-psico-notas-v1";

function useNotas(studentId, base) {
  const [extra, setExtra] = pUseState(() => {
    try { return (JSON.parse(localStorage.getItem(NOTES_KEY)) || {})[studentId] || []; }
    catch { return []; }
  });
  const add = pUseCallback((texto) => {
    const nota = { fecha: PSICO_DATA.today, autor: PSICO_DATA.pro.initials, texto, propia: true };
    setExtra((prev) => {
      const next = [...prev, nota];
      let all = {};
      try { all = JSON.parse(localStorage.getItem(NOTES_KEY)) || {}; } catch {}
      all[studentId] = next;
      localStorage.setItem(NOTES_KEY, JSON.stringify(all));
      return next;
    });
  }, [studentId]);
  const todas = [...base, ...extra].sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
  return { notas: todas, add };
}

// Preguntas resumidas para el desglose por ítem (módulo abreviado)
const ITEMS_PHQA = ["Interés/placer", "Ánimo decaído", "Sueño", "Energía", "Apetito", "Autoimagen", "Concentración", "Movimiento/habla", "Pensamientos de daño"];
const ITEMS_GAD7 = ["Nervios", "No parar de preocuparse", "Preocupación excesiva", "Dificultad para relajarse", "Inquietud", "Irritabilidad", "Miedo a algo malo"];

// Genera un desglose plausible por ítem que suma el puntaje total (solo para visualización del prototipo)
function desglose(total, n, max, forzarUltimo) {
  const arr = Array(n).fill(0);
  let resto = total;
  if (forzarUltimo) { arr[n - 1] = Math.min(2, max); resto -= arr[n - 1]; }
  let i = 0;
  while (resto > 0) {
    const idx = i % (forzarUltimo ? n - 1 : n);
    if (arr[idx] < max) { arr[idx]++; resto--; }
    i++;
    if (i > 500) break;
  }
  return arr;
}

function CycleDetail({ cycle }) {
  const phqa = desglose(cycle.phqa, 9, 3, cycle.crisis);
  const gad7 = desglose(cycle.gad7, 7, 3, false);
  const Row = ({ q, v }) => (
    <div className="item-line">
      <span className="q">{q}</span>
      <span className="bar"><i style={{ width: (v / 3 * 100) + "%" }}></i></span>
      <span className="sc">{v}</span>
    </div>
  );
  return (
    <div className="cyc-detail">
      <div style={{ fontSize: 11.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--ink-3)", margin: "6px 0" }}>PHQ-A · depresión</div>
      {ITEMS_PHQA.map((q, i) => <Row key={q} q={q} v={phqa[i]} />)}
      <div style={{ fontSize: 11.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--ink-3)", margin: "12px 0 6px" }}>GAD-7 · ansiedad</div>
      {ITEMS_GAD7.map((q, i) => <Row key={q} q={q} v={gad7[i]} />)}
    </div>
  );
}

function Ficha({ student, onBack, showToast }) {
  const s = student;
  const last = s.cycles[s.cycles.length - 1];
  const r = riesgoEstudiante(s);
  const np = nivelPhqa(last.phqa), ng = nivelGad7(last.gad7);
  const { notas, add } = useNotas(s.id, s.notas);
  const [draft, setDraft] = pUseState("");
  const [abierto, setAbierto] = pUseState(s.cycles.length - 1);

  const guardarNota = () => {
    if (!draft.trim()) return;
    add(draft.trim());
    setDraft("");
    showToast("Nota guardada en la ficha");
  };

  const phqaMetric = { key: "phqa", max: 27, bands: [
    { hasta: 27, color: "#f6dfdc" }, { hasta: 19, color: "#f6e6d6" }, { hasta: 14, color: "#f7eed9" }, { hasta: 9, color: "#e7eef8" }, { hasta: 4, color: "#e9f1ea" },
  ] };
  const gad7Metric = { key: "gad7", max: 21, bands: [
    { hasta: 21, color: "#f6dfdc" }, { hasta: 14, color: "#f7eed9" }, { hasta: 9, color: "#e7eef8" }, { hasta: 4, color: "#e9f1ea" },
  ] };

  return (
    <div className="page" data-screen-label="Ficha clínica">
      <div className="page-inner" style={{ maxWidth: 920 }}>
        <button className="back-link" onClick={onBack}>{PIc.back} Volver</button>

        <div className="ficha-head">
          <span className="avatar" style={{ background: avatarColor(s.id) }}>{s.initials}</span>
          <div>
            <h1>{s.name}</h1>
            <div className="meta">{s.carrera} · {s.anio} · {s.email}</div>
            <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center" }}>
              {last.crisis ? <span className="crisis-flag">{PIc.alert} Señal de crisis</span> : <SevChip nivel={r.label} />}
              <span style={{ fontSize: 12.5, color: "var(--ink-3)" }}>Última actividad {pHaceCuanto(s.ultimaActividad)}</span>
            </div>
          </div>
          <div className="actions">
            <button className="btn" onClick={() => showToast("Abriendo el correo del estudiante…")}>Contactar</button>
            <button className="btn primary" onClick={() => showToast("Agenda abierta (demo)")}>Agendar sesión</button>
          </div>
        </div>

        {last.crisis && (
          <div className="crisis-banner">
            <span className="ic">{PIc.alert}</span>
            <div>
              <h3>Protocolo de crisis activado</h3>
              <p>En la encuesta del ciclo {last.n}, {s.name.split(" ")[0]} marcó pensamientos de hacerse daño. Contactar hoy y registrar la gestión en las notas. Si hay riesgo inminente, derivar a la Línea 113 (opción 5) o a urgencias.</p>
            </div>
          </div>
        )}

        <div className="ficha-grid">
          {/* Columna principal */}
          <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>

            <div className="panel-card">
              <div className="h">Evolución por ciclos</div>
              <div className="b">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 22 }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                      <span style={{ fontSize: 12.5, fontWeight: 700 }}>PHQ-A · Depresión</span>
                      <span style={{ fontSize: 12, color: "var(--ink-3)" }}>último: {last.phqa}/27</span>
                    </div>
                    <EvolChart cycles={s.cycles} metric={phqaMetric} />
                  </div>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                      <span style={{ fontSize: 12.5, fontWeight: 700 }}>GAD-7 · Ansiedad</span>
                      <span style={{ fontSize: 12, color: "var(--ink-3)" }}>último: {last.gad7}/21</span>
                    </div>
                    <EvolChart cycles={s.cycles} metric={gad7Metric} />
                  </div>
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="h">Ciclos completados</div>
              {[...s.cycles].reverse().map((c) => {
                const idx = s.cycles.indexOf(c);
                const cp = nivelPhqa(c.phqa), cg = nivelGad7(c.gad7);
                const open = abierto === idx;
                return (
                  <div className="cyc-item" key={c.n}>
                    <button className="cyc-row" onClick={() => setAbierto(open ? -1 : idx)}>
                      <span className="cn">Ciclo {c.n}{c.encurso && <span style={{ fontWeight: 500, color: "var(--accent)" }}> · en curso</span>}</span>
                      <span className="cd">{pRango(c.start, c.end)} · {c.dias} de 14 días</span>
                      <span className="cyc-scores">
                        {c.crisis && <span className="crisis-flag">{PIc.alert}Crisis</span>}
                        <span className="s"><span className="v">{c.phqa}</span><span className="k">PHQ-A</span></span>
                        <span className="s"><span className="v">{c.gad7}</span><span className="k">GAD-7</span></span>
                        <span style={{ transform: open ? "rotate(90deg)" : "none", color: "var(--ink-3)", transition: "transform .15s" }}>{PIc.chev}</span>
                      </span>
                    </button>
                    {open && (
                      <>
                        <div style={{ display: "flex", gap: 8, padding: "0 20px 4px" }}>
                          <SevChip nivel={cp.nivel} /><SevChip nivel={cg.nivel} />
                        </div>
                        <CycleDetail cycle={c} />
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Columna lateral */}
          <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
            <div className="panel-card">
              <div className="h">Notas clínicas</div>
              <div className="b">
                <textarea className="nota-input" placeholder="Anotá observaciones de la sesión, acuerdos, derivaciones…"
                          value={draft} onChange={(e) => setDraft(e.target.value)}></textarea>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
                  <button className="btn primary" onClick={guardarNota} disabled={!draft.trim()} style={{ opacity: draft.trim() ? 1 : 0.5 }}>Guardar nota</button>
                </div>
                <div style={{ marginTop: 16 }}>
                  {notas.length === 0 && <p style={{ fontSize: 12.5, color: "var(--ink-3)", margin: 0 }}>Todavía no hay notas en esta ficha.</p>}
                  {notas.map((nota, i) => (
                    <div className="nota" key={i}>
                      <div className="meta">{pCorto(nota.fecha)} · {nota.autor}{nota.propia ? " (tú)" : ""}</div>
                      <div className="txt">{nota.texto}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="h">Diario del estudiante</div>
              <div className="b">
                <div className="privacy-note">
                  <span style={{ color: "var(--ink-3)" }}>{PIc.lock}</span>
                  <span>
                    {s.entradasCompartidas
                      ? <>{s.name.split(" ")[0]} eligió compartir sus entradas contigo. Léelas con cuidado: son su espacio privado.</>
                      : <>El contenido del diario es privado. Solo ves los resultados de las encuestas, no lo que {s.name.split(" ")[0]} escribe.</>}
                  </span>
                </div>
                {s.entradasCompartidas && (
                  <button className="btn" style={{ marginTop: 12, width: "100%", justifyContent: "center" }}
                          onClick={() => showToast("Entradas compartidas (demo)")}>Ver entradas compartidas</button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Ficha });
