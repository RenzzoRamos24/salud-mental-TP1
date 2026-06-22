// Sami — Mi historial, Recursos, Perfil

/* ---------- Recursos ---------- */

function Recursos() {
  const r = SAMI_DATA.resources;
  return (
    <div className="page" data-screen-label="Recursos">
      <div className="page-inner" style={{ maxWidth: 820 }}>
        <h1>Recursos</h1>
        <p className="sub">Para cuando escribir no alcanza. Pedir ayuda también es cuidarse.</p>

        <div style={{ fontSize: 13.5, fontWeight: 700, margin: "0 0 10px" }}>Si necesitás ayuda ahora</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 30 }}>
          {r.urgent.map((u) => (
            <div key={u.name} className="card" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ color: "var(--accent)" }}>{Icons.phone(18)}</div>
              <div style={{ fontSize: 14, fontWeight: 700, marginTop: 4 }}>{u.name}</div>
              <p style={{ margin: 0, fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5, flex: 1 }}>{u.desc}</p>
              <div style={{ fontSize: 19, fontWeight: 700, letterSpacing: "-0.01em", marginTop: 6 }}>{u.phone}</div>
              <div style={{ fontSize: 11.5, color: "var(--ink-3)" }}>{u.hours}</div>
            </div>
          ))}
        </div>

        <div style={{ fontSize: 13.5, fontWeight: 700, margin: "0 0 10px" }}>Para leer con calma</div>
        <div className="card rowlist">
          {r.tips.map((t) => (
            <button key={t.title} style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "15px 20px", border: 0, background: "none", textAlign: "left", width: "100%" }}
                    className="tiprow" onMouseDown={(e) => e.preventDefault()}>
              <span style={{ color: "var(--ink-3)", marginTop: 1 }}>{Icons.doc(17)}</span>
              <span style={{ minWidth: 0, flex: 1 }}>
                <span style={{ display: "block", fontSize: 13.5, fontWeight: 600 }}>{t.title}</span>
                <span style={{ display: "block", fontSize: 12.5, color: "var(--ink-2)", marginTop: 2, lineHeight: 1.5 }}>{t.desc}</span>
              </span>
              <span style={{ fontSize: 11.5, color: "var(--ink-3)", flex: "none", marginTop: 2 }}>{t.read}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------- Perfil ---------- */

function Perfil({ showToast }) {
  const u = SAMI_DATA.user;
  const [nombre, setNombre] = React.useState(u.name);
  const [hora, setHora] = React.useState("21:00");
  const [confirmar, setConfirmar] = React.useState(false);

  return (
    <div className="page" data-screen-label="Perfil">
      <div className="page-inner" style={{ maxWidth: 560 }}>
        <h1>Perfil</h1>
        <p className="sub">Tus datos y tu cuenta.</p>

        <div className="card" style={{ padding: 24, marginBottom: 14 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 16 }}>Datos personales</div>
          <div className="field">
            <label>Nombre</label>
            <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </div>
          <div className="field">
            <label>Email institucional</label>
            <input value={u.email} disabled style={{ color: "var(--ink-3)", background: "var(--bg)" }} />
          </div>
          <div className="field" style={{ marginBottom: 20 }}>
            <label>Recordatorio diario</label>
            <select value={hora} onChange={(e) => setHora(e.target.value)}>
              <option value="off">Sin recordatorio</option>
              <option value="08:00">08:00 — a la mañana</option>
              <option value="14:00">14:00 — después de almorzar</option>
              <option value="21:00">21:00 — a la noche</option>
            </select>
          </div>
          <button className="btn primary" onClick={() => showToast("Cambios guardados")}>Guardar cambios</button>
        </div>

        <div className="card" style={{ padding: 24, marginBottom: 14 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 16 }}>Contraseña</div>
          <div className="field"><label>Contraseña actual</label><input type="password" placeholder="••••••••" /></div>
          <div className="field"><label>Contraseña nueva</label><input type="password" placeholder="Mínimo 8 caracteres" /></div>
          <div className="field" style={{ marginBottom: 20 }}><label>Repetila</label><input type="password" placeholder="Una vez más" /></div>
          <button className="btn" onClick={() => showToast("Contraseña actualizada")}>Cambiar contraseña</button>
        </div>

        <div className="card" style={{ padding: 24, borderColor: "#f0d2d2" }}>
          <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 6 }}>Borrar mi cuenta</div>
          <p style={{ margin: "0 0 16px", fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.55 }}>
            Se borra todo: entradas, ciclos y encuestas. No hay manera de recuperarlo, ni siquiera escribiéndonos.
          </p>
          {confirmar ? (
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn danger" onClick={() => { setConfirmar(false); showToast("Es un prototipo — tu cuenta sigue acá :)"); }}>Sí, borrar todo</button>
              <button className="btn" onClick={() => setConfirmar(false)}>Mejor no</button>
            </div>
          ) : (
            <button className="btn danger" onClick={() => setConfirmar(true)}>Borrar cuenta</button>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Recursos, Perfil });
