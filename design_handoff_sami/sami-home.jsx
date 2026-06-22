// Sami — Inicio: tres direcciones (Hoy / Tarjetas / Calma)

function saludo() {
  return "Buenas tardes"; // jueves 12 de junio, prototipo
}

function CycleStrip({ closeDone, onNav }) {
  const { day, length } = cycleInfo();
  const done = day >= length;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
      <span style={{ fontSize: 12.5, color: "var(--ink-3)" }}>
        {done ? `Ciclo ${SAMI_DATA.cycle.number} · 14 días completados` : `Ciclo del diario · día ${day} de ${length}`}
      </span>
      <span className="cycle-progress">
        {Array.from({ length }, (_, i) => <i key={i} className={i < day ? "done" : ""}></i>)}
      </span>
      {done && !closeDone && onNav && (
        <button onClick={() => onNav("encuesta")}
                style={{ border: 0, background: "none", padding: 0, color: "var(--accent)", fontSize: 12.5, fontWeight: 600 }}>
          Responder encuesta de cierre →
        </button>
      )}
    </div>
  );
}

/* ---------- A · "Hoy" — al estilo Day One ---------- */

function HomeHoy({ entries, onNav, closeDone }) {
  const hoy = SAMI_DATA.today;
  const entryHoy = entries.find((e) => e.date === hoy);
  const recientes = entries.filter((e) => e.date !== hoy).slice(0, 4);

  return (
    <div className="page" data-screen-label="Inicio · Hoy">
      <div className="page-inner">
        <p className="sub" style={{ marginBottom: 2 }}>{fmtLong(hoy)}</p>
        <h1>{saludo()}, {SAMI_DATA.user.name.split(" ")[0]}</h1>
        <div style={{ height: 24 }}></div>

        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14, alignItems: "start" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="card" style={{ padding: 24 }}>
              {entryHoy ? (
                <>
                  <p style={{ margin: "0 0 4px", fontSize: 12.5, color: "var(--ink-3)" }}>La entrada de hoy</p>
                  <h3 style={{ margin: "0 0 8px", fontSize: 17, fontWeight: 700 }}>{entryHoy.title || "Sin título"}</h3>
                  <p style={{ margin: "0 0 18px", fontSize: 13.5, color: "var(--ink-2)", lineHeight: 1.55 }}>
                    {(entryHoy.body || "").slice(0, 150)}{(entryHoy.body || "").length > 150 ? "…" : ""}
                  </p>
                  <button className="btn primary" onClick={() => onNav("diario", { selectId: entryHoy.id })}>Seguir escribiendo</button>
                </>
              ) : (
                <>
                  <p style={{ margin: "0 0 4px", fontSize: 12.5, color: "var(--ink-3)" }}>Pregunta del día</p>
                  <h3 style={{ margin: "0 0 18px", fontSize: 18, fontWeight: 700, letterSpacing: "-0.01em", lineHeight: 1.35 }}>
                    {SAMI_DATA.prompts[0]}
                  </h3>
                  <button className="btn primary" onClick={() => onNav("diario", { compose: true })}>Escribir la entrada de hoy</button>
                </>
              )}
            </div>
            <div className="card" style={{ padding: "16px 24px" }}>
              <CycleStrip closeDone={closeDone} onNav={onNav} />
            </div>
          </div>

          <div className="card">
            <div style={{ padding: "14px 18px 10px", borderBottom: "1px solid var(--line-soft)", display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <strong style={{ fontSize: 13.5 }}>Entradas recientes</strong>
              <button className="btn" style={{ border: 0, padding: "2px 0", fontSize: 12.5, color: "var(--accent)", background: "none" }}
                      onClick={() => onNav("diario")}>Ver todas</button>
            </div>
            <div className="rowlist">
              {recientes.map((e) => (
                <button key={e.id} className="entry-row" onClick={() => onNav("diario", { selectId: e.id })}>
                  <span className="datebox">
                    <span className="dow">{dowAb(e.date)}</span>
                    <span className="num">{dayNum(e.date)}</span>
                  </span>
                  <span className="meta">
                    <span className="t">{e.title}</span>
                    <span className="x">{e.body.split("\n")[0]}</span>
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- B · "Tarjetas" — hub de secciones ---------- */

function HomeTarjetas({ entries, onNav }) {
  const { day, length } = cycleInfo();
  const cicloMeta = day >= length ? `Ciclo ${SAMI_DATA.cycle.number} completado` : `Ciclo actual · día ${day} de ${length}`;
  const cards = [
    { id: "diario", icon: "book", title: "Diario", desc: "Escribí cómo estuvo tu día. Tres líneas también cuentan.", meta: `${entries.length} entradas` },
    { id: "historial", icon: "clock", title: "Mi historial", desc: "Tus ciclos y tu actividad de escritura, para mirar atrás con calma.", meta: cicloMeta },
    { id: "recursos", icon: "heart", title: "Recursos", desc: "Líneas de ayuda y lecturas cortas para cuando las necesités.", meta: `${SAMI_DATA.resources.urgent.length} líneas · ${SAMI_DATA.resources.tips.length} lecturas` },
    { id: "perfil", icon: "person", title: "Perfil", desc: "Tus datos, tu recordatorio diario y tu cuenta.", meta: SAMI_DATA.user.email },
  ];
  return (
    <div className="page" data-screen-label="Inicio · Tarjetas">
      <div className="page-inner" style={{ maxWidth: 820 }}>
        <p className="sub" style={{ marginBottom: 2 }}>{fmtLong(SAMI_DATA.today)}</p>
        <h1>Hola, {SAMI_DATA.user.name.split(" ")[0]}</h1>
        <p className="sub">¿Por dónde querés empezar hoy?</p>
        <div className="hub-grid">
          {cards.map((c) => (
            <button key={c.id} className="hub-card" onClick={() => onNav(c.id)}>
              <span className="ic">{Icons[c.icon](18)}</span>
              <h3>{c.title}</h3>
              <p>{c.desc}</p>
              <span className="meta">{c.meta}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------- C · "Calma" — una sola cosa a la vez ---------- */

function HomeCalma({ entries, onNav, closeDone }) {
  const hoy = SAMI_DATA.today;
  const entryHoy = entries.find((e) => e.date === hoy);
  return (
    <div className="page" data-screen-label="Inicio · Calma" style={{ display: "flex" }}>
      <div style={{ margin: "auto", textAlign: "center", maxWidth: 560, paddingBottom: 60 }}>
        <p style={{ fontSize: 12, fontWeight: 600, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-3)", margin: "0 0 22px" }}>
          {fmtLong(hoy)}
        </p>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.025em", lineHeight: 1.25, margin: "0 0 14px" }}>
          {entryHoy ? "Hoy ya escribiste." : SAMI_DATA.prompts[0]}
        </h1>
        <p style={{ fontSize: 15, color: "var(--ink-2)", margin: "0 0 30px", lineHeight: 1.6 }}>
          {entryHoy
            ? "Podés volver a la entrada cuando quieras, o simplemente dejarla descansar."
            : "No hace falta una respuesta larga. Empezá por donde te salga."}
        </p>
        <button className="btn primary" style={{ padding: "10px 22px", fontSize: 14.5 }}
                onClick={() => onNav("diario", entryHoy ? { selectId: entryHoy.id } : { compose: true })}>
          {entryHoy ? "Abrir la entrada de hoy" : "Escribir ahora"}
        </button>
        <div style={{ marginTop: 44, display: "flex", justifyContent: "center" }}>
          <CycleStrip closeDone={closeDone} onNav={onNav} />
        </div>
      </div>
    </div>
  );
}

function Home({ variant, entries, onNav, closeDone }) {
  if (variant === "tarjetas") return <HomeTarjetas entries={entries} onNav={onNav} />;
  if (variant === "calma") return <HomeCalma entries={entries} onNav={onNav} closeDone={closeDone} />;
  return <HomeHoy entries={entries} onNav={onNav} closeDone={closeDone} />;
}

Object.assign(window, { Home });
