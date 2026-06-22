// Sami — Diario: tres paneles (sidebar · lista · editor), guarda en localStorage

function DiarySidebar({ filter, setFilter, entries }) {
  const tags = SAMI_DATA.tags;
  const countBy = (fn) => entries.filter(fn).length;
  const hoy = SAMI_DATA.today;

  return (
    <aside className="d-side">
      <div className="group">
        <button className={"row" + (filter === "hoy" ? " on" : "")} onClick={() => setFilter("hoy")}>
          Hoy
          <span className="count">{countBy((e) => e.date === hoy)}</span>
        </button>
        <button className={"row" + (filter === "all" ? " on" : "")} onClick={() => setFilter("all")}>
          Todas las entradas
          <span className="count">{entries.length}</span>
        </button>
      </div>
      <div className="group">
        <div className="group-label">Etiquetas</div>
        {Object.entries(tags).map(([id, t]) => (
          <button key={id} className={"row" + (filter === id ? " on" : "")} onClick={() => setFilter(id)}>
            <span className="dot" style={{ background: t.color }}></span>
            {t.label}
            <span className="count">{countBy((e) => e.tag === id)}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}

function DiaryList({ entries, selectedId, onSelect, onNew }) {
  // agrupar por mes (las entradas ya vienen ordenadas desc)
  const groups = [];
  for (const e of entries) {
    const m = fmtMonth(e.date);
    if (!groups.length || groups[groups.length - 1].month !== m) groups.push({ month: m, items: [] });
    groups[groups.length - 1].items.push(e);
  }
  const tags = SAMI_DATA.tags;

  return (
    <div className="d-list">
      <div className="d-list-head">
        <span className="month">Diario</span>
        <button className="newbtn" title="Nueva entrada" onClick={onNew}>+</button>
      </div>
      {groups.map((g) => (
        <div key={g.month}>
          <div className="month-label">{g.month}</div>
          {g.items.map((e) => (
            <button key={e.id} className={"entry-row" + (e.id === selectedId ? " on" : "")} onClick={() => onSelect(e.id)}>
              <span className="datebox">
                <span className="dow">{dowAb(e.date)}</span>
                <span className="num">{dayNum(e.date)}</span>
              </span>
              <span className="meta">
                <span className="t">{e.title || "Sin título"}</span>
                <span className="x">{(e.body || "").split("\n")[0] || "Todavía no escribiste nada."}</span>
                {e.tag && tags[e.tag] && (
                  <span className="tagline">
                    <span className="dot" style={{ background: tags[e.tag].color }}></span>
                    {tags[e.tag].label}
                  </span>
                )}
              </span>
            </button>
          ))}
        </div>
      ))}
      {entries.length === 0 && (
        <p style={{ padding: "28px 16px", fontSize: 13, color: "var(--ink-3)", textAlign: "center" }}>
          No hay entradas con este filtro.
        </p>
      )}
    </div>
  );
}

/* ---------- Encuesta de ciclo (solo en la entrada de hoy) ---------- */

function CycleSurvey({ onSubmit, submitted }) {
  const { day, length, questions } = { ...cycleInfo(), questions: SAMI_DATA.cycle.questions };
  const [values, setValues] = React.useState({});
  const listo = questions.every((q) => values[q.id] != null);

  if (submitted) {
    return (
      <div className="cycle-card" data-comment-anchor="cycle-survey">
        <h3>Encuesta del ciclo · día {day} de {length}</h3>
        <p className="hint" style={{ marginBottom: 0 }}>Listo por hoy. Gracias por tomarte el minuto — esto le da contexto a tus entradas.</p>
      </div>
    );
  }

  return (
    <div className="cycle-card" data-comment-anchor="cycle-survey">
      <h3>Encuesta del ciclo · día {day} de {length}</h3>
      <p className="hint">Un minuto, tres preguntas. Acompaña tu entrada de hoy.</p>
      {questions.map((q) => (
        <div className="scale-q" key={q.id}>
          <div className="q">{q.q}</div>
          <div className="opts">
            {q.opts.map((o, i) => (
              <button key={o} className={values[q.id] === i ? "on" : ""}
                      onClick={() => setValues((v) => ({ ...v, [q.id]: i }))}>{o}</button>
            ))}
          </div>
        </div>
      ))}
      <button className="btn primary" disabled={!listo} style={{ opacity: listo ? 1 : 0.45 }}
              onClick={() => onSubmit(values)}>Enviar</button>
    </div>
  );
}

/* ---------- Editor ---------- */

function DiaryEditor({ entry, onChange, survey, banner }) {
  if (!entry) {
    return (
      <div className="d-editor">
        {banner}
        <div style={{ flex: 1, display: "grid", placeItems: "center" }}>
          <p style={{ color: "var(--ink-3)", fontSize: 13.5 }}>Elegí una entrada, o creá una nueva con el botón +</p>
        </div>
      </div>
    );
  }

  const tags = SAMI_DATA.tags;
  const words = wordCount(entry.body);
  const esHoy = entry.date === SAMI_DATA.today;

  return (
    <div className="d-editor">
      <div className="ed-head">
        <span className="when">{fmtLong(entry.date)}</span>
        {esHoy && <span style={{ fontSize: 12, color: "var(--accent)", fontWeight: 600 }}>Hoy</span>}
      </div>
      {banner}
      <div className="ed-body">
        <input className="ed-title" value={entry.title} placeholder="Ponle un título (o no)"
               onChange={(e) => onChange({ ...entry, title: e.target.value })} />
        <textarea className="ed-text" value={entry.body} rows={Math.max(10, (entry.body || "").split("\n").length + 3)}
                  placeholder="Cuéntale a Sami cómo te has sentido…"
                  onChange={(e) => onChange({ ...entry, body: e.target.value })}></textarea>
      </div>
      {esHoy && survey}
      <div className="ed-foot">
        <span className="tagpick">
          {Object.entries(tags).map(([id, t]) => (
            <button key={id} className={entry.tag === id ? "on" : ""}
                    onClick={() => onChange({ ...entry, tag: entry.tag === id ? null : id })}>
              <span className="dot" style={{ background: t.color }}></span>{t.label}
            </button>
          ))}
        </span>
        <span style={{ marginLeft: "auto" }}>{words} {words === 1 ? "palabra" : "palabras"} · guardado</span>
      </div>
    </div>
  );
}

/* ---------- Pantalla completa ---------- */

function Diary({ entries, saveEntry, intent, onIntentDone, showToast, onNav, close }) {
  const [filter, setFilter] = React.useState("all");
  const [selectedId, setSelectedId] = React.useState(entries[0] ? entries[0].id : null);
  const { answers, submit } = useCycleSurvey();
  const hoy = SAMI_DATA.today;
  const cycleDone = cycleInfo().day >= cycleInfo().length;

  const nuevaEntrada = React.useCallback(() => {
    const existente = entries.find((e) => e.date === hoy);
    if (existente) { setSelectedId(existente.id); setFilter("all"); return; }
    const nueva = { id: "u-" + Date.now(), date: hoy, title: "", body: "", tag: null };
    saveEntry(nueva);
    setSelectedId(nueva.id);
    setFilter("all");
  }, [entries, saveEntry]);

  // intents de navegación (desde Inicio)
  React.useEffect(() => {
    if (!intent) return;
    if (intent.selectId) { setSelectedId(intent.selectId); setFilter("all"); }
    else if (intent.compose) nuevaEntrada();
    onIntentDone();
  }, [intent]);

  const visibles = entries.filter((e) =>
    filter === "all" ? true : filter === "hoy" ? e.date === hoy : e.tag === filter
  );

  const selected = entries.find((e) => e.id === selectedId) || null;

  return (
    <div className="diary" data-screen-label="Diario">
      <DiarySidebar filter={filter} setFilter={setFilter} entries={entries} />
      <DiaryList entries={visibles} selectedId={selectedId} onSelect={setSelectedId} onNew={nuevaEntrada} />
      <DiaryEditor
        entry={selected}
        onChange={saveEntry}
        banner={
          cycleDone ? (
            <SurveyBanner close={close} onStart={() => onNav("encuesta")} onResults={() => onNav("encuesta")} />
          ) : null
        }
        survey={
          cycleDone ? null : (
            <CycleSurvey
              submitted={!!answers[hoy]}
              onSubmit={(v) => { submit(hoy, v); showToast("Encuesta del día enviada"); }}
            />
          )
        }
      />
    </div>
  );
}

Object.assign(window, { Diary });
