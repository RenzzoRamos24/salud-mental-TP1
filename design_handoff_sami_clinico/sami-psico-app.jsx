// Sami clínico — router + montaje

function PsicoApp() {
  const [route, setRoute] = React.useState("panel");
  const [studentId, setStudentId] = React.useState(null);
  const [toast, setToast] = React.useState(null);
  const toastTimer = React.useRef(null);

  const showToast = React.useCallback((msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2400);
  }, []);

  const openStudent = React.useCallback((id) => { setStudentId(id); setRoute("ficha"); window.scrollTo(0, 0); }, []);
  const nav = React.useCallback((r) => { setRoute(r); window.scrollTo(0, 0); }, []);

  const alertCount = buildAlerts().filter((a) => a.tipo === "crit").length;
  const student = PSICO_DATA.students.find((s) => s.id === studentId);

  return (
    <div className="app">
      <PTopbar route={route} onNav={nav} alertCount={alertCount} />
      {route === "panel" && <PPanel onOpen={openStudent} onNav={nav} />}
      {route === "estudiantes" && <PEstudiantes onOpen={openStudent} />}
      {route === "alertas" && <PAlertas onOpen={openStudent} />}
      {route === "ficha" && student && <Ficha student={student} onBack={() => nav("panel")} showToast={showToast} />}
      <Toast msg={toast} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<PsicoApp />);
