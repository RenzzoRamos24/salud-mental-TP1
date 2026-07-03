"""
Siembra DASS-21 al banco de instrumentos.

Uso:
    venv/bin/python -m scripts.seed_dass21

El SVM `models/svm_dass21.joblib` ya está entrenado esperando este instrumento.
Después de correr esto, el evaluator puede llamar automáticamente al SVM como
segunda opinión cuando la plantilla incluye DASS-21 (ver
`app/services/evaluator_service.py:_segunda_opinion_svm`).
"""
from app.database import SessionLocal
from app.models.bank import BankInstrumento, BankItem


DASS21_ITEMS = [
    "Me costó mucho relajarme.",
    "Me di cuenta que tenía la boca seca.",
    "No podía sentir ningún sentimiento positivo.",
    "Se me hizo difícil respirar.",
    "Se me hizo difícil tomar la iniciativa para hacer cosas.",
    "Reaccioné exageradamente en ciertas situaciones.",
    "Sentí que mis manos temblaban.",
    "Sentí que tenía muchos nervios.",
    "Estaba preocupado por situaciones en las que podría tener pánico.",
    "Sentí que no tenía nada por que esperar.",
    "Noté que me agitaba.",
    "Se me hizo difícil relajarme.",
    "Me sentí triste y deprimido.",
    "No toleré nada que no me permitiera continuar con lo que hacía.",
    "Sentí que estaba al punto del pánico.",
    "No me pude entusiasmar por nada.",
    "Sentí que valía muy poco como persona.",
    "Sentí que estaba muy irritable.",
    "Sentí los latidos de mi corazón sin haber hecho esfuerzo físico.",
    "Tuve miedo sin razón.",
    "Sentí que la vida no tenía ningún sentido.",
]


def main() -> None:
    db = SessionLocal()

    inst = db.query(BankInstrumento).filter_by(codigo="DASS-21").first()
    if inst is not None:
        print(f"DASS-21 ya existe (id={inst.id}). Nada que hacer.")
        db.close()
        return

    inst = BankInstrumento(
        codigo="DASS-21",
        nombre="Escala de Depresión, Ansiedad y Estrés (versión corta)",
        autor="Lovibond & Lovibond",
        anio=1995,
        dominio="depresion_ansiedad_estres",
        tipo_escala="likert",
        likert_min=0,
        likert_max=3,
        n_items=21,
        tiempo_min=10,
        instruccion=(
            "Por favor lee cada frase y marca cuánto te aplicó esta semana. "
            "0=No me aplicó, 1=Un poco, 2=Bastante, 3=Mucho."
        ),
        citacion=(
            "Lovibond, S.H. & Lovibond, P.F. (1995). Manual for the Depression "
            "Anxiety Stress Scales. Sydney: Psychology Foundation."
        ),
        validacion_es="Antúnez & Vinet (2012) — validación en adolescentes chilenos",
        activo=1,
    )
    db.add(inst)
    db.flush()  # obtener id

    for numero, texto in enumerate(DASS21_ITEMS, start=1):
        db.add(BankItem(
            instrumento_id=inst.id,
            numero=numero,
            texto=texto,
            inverso=0,
            bandera_crisis=1 if numero == 21 else 0,  # ítem 21 "vida sin sentido"
        ))

    db.commit()
    print(f"OK — DASS-21 sembrado con id={inst.id} y 21 ítems.")
    db.close()


if __name__ == "__main__":
    main()
