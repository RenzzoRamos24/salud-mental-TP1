// "Diario estudiantil" — fiel a la imagen D: VERDE + BLANCO, tarjetas blancas,
// coral de acento, sans amable (Gabarito/Hanken). Sin beige, sin serif, sin blobs,
// sin degradados. Ejecutado como producto real: jerarquía, profundidad sutil, pulido.
(function () {
  const { useState } = React;

  const Ico = ({ name, s = 18 }) => {
    const p = { width: s, height: s, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round' };
    switch (name) {
      case 'lock': return <svg {...p}><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>;
      case 'undo': return <svg {...p}><path d="M4 9h11a4 4 0 0 1 0 8h-3"/><path d="M7 6L4 9l3 3"/></svg>;
      default: return null;
    }
  };

  const MoodIco = ({ k, s = 28 }) => {
    const p = { width: s, height: s, viewBox: '0 0 26 26', fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round' };
    if (k === 'bueno') return <svg {...p}><circle cx="13" cy="13" r="4.4"/>{[0,45,90,135,180,225,270,315].map((a,i)=>{const r=a*Math.PI/180;return <line key={i} x1={13+6.9*Math.cos(r)} y1={13+6.9*Math.sin(r)} x2={13+9.7*Math.cos(r)} y2={13+9.7*Math.sin(r)}/>;})}</svg>;
    if (k === 'mezcla') return <svg {...p}><circle cx="16.5" cy="9" r="3.3"/><rect x="4" y="12.5" width="15" height="7.6" rx="3.8"/></svg>;
    if (k === 'apagado') return <svg {...p}><rect x="4" y="9.6" width="18" height="7.8" rx="3.9"/></svg>;
    return <svg {...p}><rect x="4" y="6.6" width="18" height="7.8" rx="3.9"/><line x1="9" y1="17.6" x2="8" y2="20.6"/><line x1="13.5" y1="17.6" x2="12.5" y2="20.6"/><line x1="18" y1="17.6" x2="17" y2="20.6"/></svg>;
  };

  const MOODS = [
    { k: 'bueno', label: 'Buen día' },
    { k: 'mezcla', label: 'Mezclado' },
    { k: 'apagado', label: 'Apagado' },
    { k: 'dificil', label: 'Difícil' },
  ];

  // anillo limpio de progreso (un color, sin degradado)
  function Ring({ value = 6, total = 14 }) {
    const r = 33, C = 2 * Math.PI * r, frac = value / total;
    return (
      <svg width="84" height="84" viewBox="0 0 84 84">
        <circle cx="42" cy="42" r={r} fill="none" stroke="#E4EBDE" strokeWidth="7" />
        <circle cx="42" cy="42" r={r} fill="none" stroke="#4C6B53" strokeWidth="7" strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * (1 - frac)} transform="rotate(-90 42 42)" />
        <text x="42" y="40" textAnchor="middle" fontFamily="Gabarito, sans-serif" fontSize="17" fontWeight="700" fill="#2F4A38">6/14</text>
        <text x="42" y="53" textAnchor="middle" fontFamily="Hanken Grotesk, sans-serif" fontSize="8" fontWeight="600" letterSpacing="0.5" fill="#8A9685">días</text>
      </svg>
    );
  }

  function DiaryStudent() {
    const [text, setText] = useState('');
    const [mood, setMood] = useState(null);
    const [saved, setSaved] = useState(false);
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const canSave = words > 0 || mood;

    return (
      <div className="ds">
        <style>{`
          .ds{position:absolute;inset:0;background:#EDF1E8;color:#27352B;font-family:'Hanken Grotesk',system-ui,sans-serif;overflow:hidden;}
          .ds *{box-sizing:border-box;}
          .ds .gb{font-family:'Gabarito',system-ui,sans-serif;}

          .ds .bar{display:flex;align-items:center;justify-content:space-between;padding:20px 40px;}
          .ds .wm{display:flex;align-items:baseline;gap:10px;}
          .ds .wm b{font-family:'Gabarito',sans-serif;font-weight:700;font-size:20px;color:#2F4A38;letter-spacing:-.2px;}
          .ds .wm s{text-decoration:none;font-size:13px;font-weight:500;color:#9AA694;}
          .ds .who{display:flex;align-items:center;gap:14px;}
          .ds .chip{display:flex;align-items:center;gap:9px;background:#fff;border-radius:999px;padding:5px 15px 5px 6px;box-shadow:0 1px 3px rgba(39,53,43,.07);}
          .ds .av{width:26px;height:26px;border-radius:50%;background:#E08763;color:#fff;display:grid;place-items:center;font-weight:700;font-size:12px;}
          .ds .chip span{font-size:13px;font-weight:600;white-space:nowrap;color:#3A4A3E;}
          .ds .chip small{color:#9AA694;font-weight:500;}
          .ds .out{font-size:13px;font-weight:500;color:#9AA694;cursor:pointer;}
          .ds .out:hover{color:#3A4A3E;}

          .ds .col{max-width:720px;margin:0 auto;padding:30px 30px 0;}
          .ds .eyebrow{font-size:14px;font-weight:700;color:#E08763;margin-bottom:7px;}
          .ds h1{font-family:'Gabarito',sans-serif;font-weight:700;font-size:37px;line-height:1.05;letter-spacing:-.6px;margin:0 0 18px;color:#243A2C;}

          /* cycle — white card, subtle depth, clean ring */
          .ds .card{background:#fff;border-radius:18px;box-shadow:0 1px 2px rgba(39,53,43,.04),0 6px 20px -10px rgba(39,53,43,.16);}
          .ds .cycle{display:flex;align-items:center;gap:22px;padding:22px 26px;}
          .ds .cycle .meta{flex:1;min-width:0;}
          .ds .k{font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#A6B19F;}
          .ds .cycle h2{font-family:'Gabarito',sans-serif;font-size:20px;font-weight:600;margin:7px 0 14px;color:#2A3A30;}
          .ds .dots{display:flex;gap:7px;align-items:center;}
          .ds .dots i{width:13px;height:13px;border-radius:50%;background:#E2E8DD;}
          .ds .dots i.f{background:#4C6B53;}
          .ds .dots i.c{background:#E08763;}
          .ds .cycle .foot{font-size:12.5px;color:#9AA694;margin-top:13px;}

          /* prompt — mint flat panel */
          .ds .prompt{background:#E2EADC;border-radius:16px;padding:18px 22px;margin-top:16px;}
          .ds .prompt .q{font-family:'Gabarito',sans-serif;font-size:19px;font-weight:600;line-height:1.36;color:#2A3A30;margin-top:7px;}

          .ds .streak{display:flex;justify-content:flex-end;margin:16px 0 9px;}
          .ds .streak button{display:inline-flex;align-items:center;gap:8px;white-space:nowrap;background:#fff;border:0;border-radius:999px;padding:9px 16px;font-size:13px;font-weight:600;color:#7E8B79;cursor:pointer;font-family:inherit;box-shadow:0 1px 3px rgba(39,53,43,.07);transition:.13s;}
          .ds .streak button:hover{color:#4C6B53;}

          /* writing — hero white card */
          .ds .sheet{background:#fff;border-radius:18px;box-shadow:0 1px 2px rgba(39,53,43,.04),0 14px 34px -16px rgba(39,53,43,.22);overflow:hidden;}
          .ds textarea{display:block;width:100%;border:0;outline:0;resize:none;background:transparent;font-family:'Hanken Grotesk',sans-serif;font-size:16.5px;line-height:1.62;color:#27352B;height:158px;padding:22px 26px 0;}
          .ds textarea::placeholder{color:#AEB8A8;}
          .ds .sfoot{display:flex;justify-content:space-between;align-items:center;padding:13px 26px;border-top:1px solid #EEF2EA;}
          .ds .sfoot .cnt{font-size:12.5px;font-weight:600;color:#9AA694;}
          .ds .sfoot .auto{display:inline-flex;align-items:center;gap:8px;font-size:12px;color:#AEB8A8;}
          .ds .sfoot .auto i{width:6px;height:6px;border-radius:50%;background:#9EC09B;}

          /* mood — white cards, green on-state */
          .ds .moodq{font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#A6B19F;margin:20px 0 12px;}
          .ds .moods{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
          .ds .mopt{display:flex;flex-direction:column;align-items:center;gap:10px;padding:17px 8px;background:#fff;border:1.5px solid transparent;border-radius:16px;cursor:pointer;color:#7E8B79;transition:.14s;font-family:inherit;box-shadow:0 1px 3px rgba(39,53,43,.05);}
          .ds .mopt:hover{transform:translateY(-2px);box-shadow:0 8px 18px -8px rgba(39,53,43,.2);}
          .ds .mopt.on{background:#3F5D4B;color:#fff;}
          .ds .mopt span{font-size:13.5px;font-weight:600;white-space:nowrap;}

          .ds .priv{display:flex;align-items:center;justify-content:center;gap:8px;font-size:12.5px;color:#9AA694;margin:16px 0;}

          .ds .savebar{display:flex;justify-content:space-between;align-items:center;padding:6px 0 26px;}
          .ds .savebar .note{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;color:#8C988A;}
          .ds .save{background:#3F5D4B;color:#fff;border:0;border-radius:12px;padding:14px 30px;font-family:'Gabarito',sans-serif;font-size:15px;font-weight:600;white-space:nowrap;cursor:pointer;transition:.13s;box-shadow:0 6px 16px -8px rgba(63,93,75,.7);}
          .ds .save:disabled{background:#C9D2C3;color:#fff;cursor:not-allowed;box-shadow:none;}
          .ds .save:not(:disabled):hover{background:#36503f;transform:translateY(-1px);}
          .ds .save.done{background:#E08763;box-shadow:0 6px 16px -8px rgba(224,135,99,.7);}
        `}</style>

        <div className="bar">
          <div className="wm"><b>Sami</b><s>Diario</s></div>
          <div className="who">
            <div className="chip"><span className="av">R</span><span>Renzo <small>· estudiante</small></span></div>
            <span className="out">Cerrar sesión</span>
          </div>
        </div>

        <div className="col">
          <div className="eyebrow">Hola, Renzo</div>
          <h1>Sábado 30 de mayo</h1>

          <div className="card cycle">
            <div className="meta">
              <div className="k">Ciclo 1</div>
              <h2>Día 6 de 14</h2>
              <div className="dots">
                {Array.from({length:14},(_,i)=>(<i key={i} className={i<3?'f':(i===5?'c':'')}></i>))}
              </div>
              <div className="foot">3 entradas · hasta el 7 de junio</div>
            </div>
            <Ring />
          </div>

          <div className="prompt">
            <div className="k">Para empezar</div>
            <div className="q">¿Qué tienes en la cabeza hoy?</div>
          </div>

          <div className="sheet">
            <textarea value={text} onChange={(e)=>{setText(e.target.value);setSaved(false);}} placeholder="Empieza a escribir…" />
            <div className="sfoot">
              <span className="cnt">{words} palabras</span>
            </div>
          </div>

          <div className="moodq">¿Cómo estuvo tu día?</div>
          <div className="moods">
            {MOODS.map(({k,label})=>(
              <button key={k} className={'mopt'+(mood===k?' on':'')} onClick={()=>{setMood(k);setSaved(false);}}>
                <MoodIco k={k} s={27} /><span>{label}</span>
              </button>
            ))}
          </div>

          <div className="savebar">
            <span className="note"><Ico name="lock" s={14} /> Solo tú puedes leerlo.</span>
            <button className={'save'+(saved?' done':'')} disabled={!canSave} onClick={()=>setSaved(true)}>
              {saved ? 'Guardado' : 'Guardar'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  window.DiaryStudent = DiaryStudent;
})();
