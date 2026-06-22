// Sami — app: router, tweaks (paleta + dirección del inicio), toast

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accentColor": "#0d9488",
  "inicio": "Hoy",
  "simError": false
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = React.useState("inicio");
  const [diaryIntent, setDiaryIntent] = React.useState(null);
  const [toast, setToast] = React.useState(null);
  const toastTimer = React.useRef(null);

  const { entries, saveEntry } = useDiary();
  const { close, saveClose, resetClose } = useCloseSurvey();

  React.useEffect(() => {
    document.documentElement.style.setProperty("--accent", t.accentColor);
  }, [t.accentColor]);

  const showToast = React.useCallback((msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2400);
  }, []);

  const nav = React.useCallback((r, intent) => {
    setRoute(r);
    if (r === "diario" && intent) setDiaryIntent(intent);
    window.scrollTo(0, 0);
  }, []);

  const homeVariant = t.inicio.toLowerCase(); // "hoy" | "tarjetas" | "calma"

  return (
    <div className="app">
      <Topbar route={route} onNav={nav} />
      {route === "inicio" && <Home variant={homeVariant} entries={entries} onNav={nav} closeDone={close.status === "done"} />}
      {route === "diario" && (
        <Diary entries={entries} saveEntry={saveEntry}
               intent={diaryIntent} onIntentDone={() => setDiaryIntent(null)}
               showToast={showToast} onNav={nav} close={close} />
      )}
      {route === "encuesta" && (
        <EncuestaCierre key={close.status} close={close} saveClose={saveClose}
                        onExit={() => nav("diario")} simError={t.simError} />
      )}
      {route === "historial" && <Historial entries={entries} onNav={nav} close={close} />}
      {route === "recursos" && <Recursos />}
      {route === "perfil" && <Perfil showToast={showToast} />}

      <Toast msg={toast} />

      <TweaksPanel>
        <TweakSection label="Paleta" />
        <TweakColor label="Color de acento" value={t.accentColor}
                    options={["#0d9488", "#0a84ff", "#1c1c22"]}
                    onChange={(v) => setTweak("accentColor", v)} />
        <TweakSection label="Inicio" />
        <TweakRadio label="Dirección" value={t.inicio}
                    options={["Hoy", "Tarjetas", "Calma"]}
                    onChange={(v) => setTweak("inicio", v)} />
        <TweakSection label="Encuesta de cierre" />
        <TweakToggle label="Simular error al guardar" value={t.simError}
                     onChange={(v) => setTweak("simError", v)} />
        <TweakButton label="Reiniciar encuesta (demo)" secondary
                     onClick={() => { resetClose(); showToast("Encuesta de cierre reiniciada"); }} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
