// Sami — Encuesta de cierre de ciclo (PHQ-A + GAD-7), 16 ítems

const CLOSE_KEY = "sami-close-v1";

function useCloseSurvey() {
  const [state, setState] = React.useState(() => {
    try { return JSON.parse(localStorage.getItem(CLOSE_KEY)) || { status: "pending" }; }
    catch { return { status: "pending" }; }
  });
  const saveClose = React.useCallback((answers) => {
    const next = { status: "done", answers, ts: Date.now() };
    localStorage.setItem(CLOSE_KEY, JSON.stringify(next));
    setState(next);
  }, []);
  const resetClose = React.useCallback(() => {
    localStorage.removeItem(CLOSE_KEY);
    setState({ status: "pending" });
  }, []);
  return { close: state, saveClose, resetClose };
}

function scoreSurvey(answers) {
  const cs = SAMI_DATA.closeSurvey;
  const phqa = answers.slice(0, 9).reduce((n, v) => n + (v || 0), 0);
  const gad7 = answers.slice(9).reduce((n, v) => n + (v || 0), 0);
  const nivel = (tabla, score) => tabla.find((r) => score <= r.hasta);
  return {
    phqa, gad7,
    phqaNivel: nivel(cs.sevPhqa, phqa),
    gadNivel: nivel(cs.sevGad7, gad7),
    crisis: (answers[8] || 0) >= 1,
  };
}

function lvlClass(nivel) {
  if (/severa/i.test(nivel)) return "lvl bad";
  if (/moderada/i.test(nivel)) return "lvl warn";
  return "lvl";
}

/* ---------- Banner de invitación (vive en el diario) ---------- */

function SurveyBanner({ close, onStart, onResults }) {
  const cycleN = SAMI_DATA.cycle.number;
  if (close.status === "done") {
    const s = scoreSurvey(close.answers);
    return (
      <div className="invite" data-comment-anchor="close-survey-banner">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700 }}>Encuesta de cierre completada</div>
          <div style={{ fontSize: 12.5, color: "var(--ink-2)", marginTop: 2 }}>
            Ciclo {cycleN} · PHQ-A {s.phqa}/27 · GAD-7 {s.gad7}/21
          </div>
        </div>
        <button className="btn" onClick={onResults}>Ver resultados</button>
      </div>
    );
  }
  return (
    <div className="invite" data-comment-anchor="close-survey-banner">
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700 }}>Cerraste tu ciclo de 14 días.</div>
        <div style={{ fontSize: 12.5, color: "var(--ink-2)", marginTop: 2, lineHeight: 1.5 }}>
          Cuéntale a Sami cómo te sentiste estas dos semanas. Son 16 preguntas, te toma 5 minutos.
        </div>
      </div>
      <button className="btn primary" onClick={onStart}>Empezar encuesta</button>
    </div>
  );
}

/* ---------- Resumen final ---------- */

function SurveyResumen({ answers, onExit }) {
  const s = scoreSurvey(answers);
  const cycleN = SAMI_DATA.cycle.number;
  const bloques = [
    { name: "PHQ-A · Depresión", score: s.phqa, max: 27, nivel: s.phqaNivel },
    { name: "GAD-7 · Ansiedad", score: s.gad7, max: 21, nivel: s.gadNivel },
  ];
  return (
    <div className="survey-col" data-screen-label="Encuesta de cierre · Resumen">
      <div className="q-mod">Encuesta de cierre</div>
      <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", margin: "0 0 8px" }}>Gracias por responder.</h1>
      <p style={{ fontSize: 14.5, color: "var(--ink-2)", lineHeight: 1.6, margin: 0 }}>
        Estos son los puntajes de tu ciclo {cycleN}. Quedan guardados para que los conversen con tu psicóloga.
      </p>
      <div className="score-grid">
        {bloques.map((b) => (
          <div className="score-card" key={b.name}>
            <div className="name">{b.name}</div>
            <div className="num">{b.score}<small> /{b.max}</small></div>
            <span className={lvlClass(b.nivel.nivel)}>{b.nivel.nivel}</span>
            <div className="act">{b.nivel.accion}</div>
          </div>
        ))}
      </div>
      {s.crisis && (
        <div className="crisis-card" data-comment-anchor="crisis-block">
          <h3>Pide ayuda ahora.</h3>
          <p>
            Marcaste tener pensamientos de hacerte daño. Por favor llama a la <strong>Línea 113, opción 5</strong>.
            Es gratuita, confidencial y atiende 24/7. También avisa a tu psicóloga o a alguien de tu casa hoy mismo.
          </p>
        </div>
      )}
      <button className="btn primary" onClick={onExit}>Volver al diario</button>
    </div>
  );
}

/* ---------- Flujo de preguntas ---------- */

function EncuestaCierre({ close, saveClose, onExit, simError }) {
  const cs = SAMI_DATA.closeSurvey;
  const total = cs.questions.length;

  const [view, setView] = React.useState(close.status === "done" ? "resumen" : "preguntas");
  const [answers, setAnswers] = React.useState(() =>
    close.status === "done" ? close.answers : Array(total).fill(null)
  );
  const [idx, setIdx] = React.useState(0);
  const [enviando, setEnviando] = React.useState(false);
  const [error, setError] = React.useState(false);
  const timer = React.useRef(null);
  React.useEffect(() => () => clearTimeout(timer.current), []);

  const q = cs.questions[idx];
  const ultima = idx === total - 1;

  const elegir = (v) => {
    setAnswers((a) => { const n = [...a]; n[idx] = v; return n; });
    if (!ultima) {
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setIdx((i) => Math.min(i + 1, total - 1)), 260);
    }
  };

  const terminar = () => {
    setEnviando(true);
    setError(false);
    timer.current = setTimeout(() => {
      setEnviando(false);
      if (simError) { setError(true); return; }
      saveClose(answers);
      setView("resumen");
    }, 900);
  };

  if (view === "resumen") {
    return (
      <div className="survey">
        <SurveyResumen answers={answers} onExit={onExit} />
      </div>
    );
  }

  return (
    <div className="survey" data-screen-label="Encuesta de cierre · Pregunta">
      <div className="survey-col">
        <div className="survey-top">
          <span>Cierre del ciclo {SAMI_DATA.cycle.number}</span>
          <span>{idx + 1}/{total}</span>
        </div>
        <div className="seg-progress">
          {answers.map((a, i) => (
            <i key={i} className={i === idx ? "cur" : a != null ? "done" : ""}></i>
          ))}
        </div>

        <div className="q-mod">{q.mod} · pregunta {q.n}</div>
        <p className="q-text">{q.q}</p>
        <p className="q-sub">Pensando en los últimos 14 días</p>

        <div className="likert">
          {cs.likert.map((o) => (
            <button key={o.v} className={answers[idx] === o.v ? "on" : ""} onClick={() => elegir(o.v)}>
              <span className="val">{o.v}</span>
              <span>
                <span className="lab">{o.label}</span>
                <span className="des">{o.desc}</span>
              </span>
            </button>
          ))}
        </div>

        <div className="survey-nav">
          <button className="btn" disabled={idx === 0 || enviando} style={{ opacity: idx === 0 ? 0.45 : 1 }}
                  onClick={() => setIdx((i) => Math.max(0, i - 1))}>Atrás</button>
          {ultima ? (
            <button className="btn primary" disabled={enviando} onClick={terminar}>
              {enviando ? "Enviando…" : "Terminar"}
            </button>
          ) : (
            <button className="btn" onClick={() => setIdx((i) => i + 1)}>Saltar</button>
          )}
        </div>

        {error && <div className="err-card">No pudimos guardar tu respuesta. Intenta de nuevo.</div>}

        <p className="survey-foot">Tus respuestas son confidenciales. Solo las ve tu psicóloga.</p>
      </div>
    </div>
  );
}

Object.assign(window, { useCloseSurvey, scoreSurvey, SurveyBanner, EncuestaCierre });
