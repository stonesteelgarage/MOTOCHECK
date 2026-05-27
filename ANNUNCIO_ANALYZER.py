import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

try:
    from config import OPENAI_API_KEY, LOGO_PATH
except Exception:
    OPENAI_API_KEY = ""
    LOGO_PATH = "stonesteel_logo.png"


st.set_page_config(
    page_title="StoneSteel Analisi Annuncio",
    page_icon="🏍️",
    layout="centered"
)


st.markdown("""
<style>
body {
    background-color: #000000;
    color: white;
}
.stApp {
    background-color: #000000;
    color: white;
}
h1, h2, h3, h4, p, label, span, div {
    color: white !important;
}
textarea, input {
    background-color: #111111 !important;
    color: white !important;
}
.stTextArea textarea {
    background-color: #111111 !important;
    color: white !important;
}
.stButton > button {
    background-color: #f5c400;
    color: black !important;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.7rem 1.2rem;
    border: none;
}
.stButton > button:hover {
    background-color: #ffd700;
    color: black !important;
}
.result-box {
    background-color: #111111;
    border: 1px solid #333333;
    border-radius: 14px;
    padding: 24px;
    margin-top: 20px;
    color: white;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


if LOGO_PATH:
    try:
        st.image(LOGO_PATH, width=170)
    except Exception:
        pass


st.title("StoneSteel Analisi Annuncio")
st.write(
    "Incolla il link di un annuncio moto. StoneSteel analizzerà il mezzo, "
    "i rischi, i difetti probabili, la checklist e tre alternative."
)


def estrai_testo_annuncio(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return (
                "Non sono riuscito a leggere direttamente la pagina. "
                f"Codice errore: {response.status_code}. "
                "L'analisi verrà fatta sul link e sulle informazioni eventualmente deducibili."
            )

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = soup.title.string if soup.title else ""

        testo = soup.get_text(separator="\n")
        righe = [r.strip() for r in testo.splitlines() if r.strip()]
        testo_pulito = "\n".join(righe)

        testo_finale = f"TITOLO PAGINA:\n{title}\n\nTESTO ANNUNCIO:\n{testo_pulito}"

        return testo_finale[:12000]

    except Exception as e:
        return (
            "Errore durante la lettura dell'annuncio: "
            f"{str(e)}. "
            "L'analisi verrà fatta sul link e sulle informazioni disponibili."
        )


def analizza_annuncio_con_ai(url, testo_annuncio):
    if not OPENAI_API_KEY:
        return "Errore: manca OPENAI_API_KEY nel file config.py"

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Sei StoneSteel Garage, un consulente esperto di moto usate, custom, touring, naked, enduro stradali e moto da turismo.

L'utente ha incollato questo link annuncio:
{url}

Testo estratto dall'annuncio:
{testo_annuncio}

Devi produrre un'analisi professionale in italiano, concreta, utile per chi sta valutando se comprare questa moto.

Regole:
- Non usare markdown complesso.
- Non usare simboli strani.
- Non usare ###.
- Non inventare dati certi se non sono presenti.
- Se il testo dell'annuncio è incompleto, dillo chiaramente.
- Se non riesci a leggere l'annuncio, spiega che serve verificare manualmente prezzo, chilometri, anno, tagliandi e foto.

Struttura obbligatoria:

1. Sintesi StoneSteel dell'annuncio
Spiega che moto sembra essere, che tipo di acquisto rappresenta e a che profilo di motociclista può interessare.

2. Prima impressione sul prezzo e sull'annuncio
Valuta se l'annuncio sembra interessante, caro, povero di informazioni, rischioso o da approfondire.

3. Punti positivi evidenti
Elenca i punti favorevoli che emergono dall'annuncio.

4. Difetti e rischi possibili di questo modello
Indica i difetti ricorrenti o le fragilità tipiche del modello o della categoria.
Se non conosci il modello esatto, ragiona per categoria.

5. Cosa controllare prima di comprarla
Crea una checklist pratica con almeno 15 controlli:
- documenti
- tagliandi
- gomme
- freni
- trasmissione
- sospensioni
- telaio
- motore
- perdite olio
- elettronica
- prova su strada
- accessori
- omologazioni
- numero proprietari
- coerenza chilometraggio

6. Domande da fare al venditore
Scrivi almeno 10 domande concrete.

7. Valutazione rischio StoneSteel
Assegna un giudizio:
- Basso
- Medio
- Alto

Spiega perché.

8. Opinione finale StoneSteel
Dai un parere netto:
- da vedere subito
- interessante ma da trattare
- da verificare con attenzione
- meglio lasciar perdere

9. Tre modelli alternativi
Suggerisci tre modelli alternativi coerenti con il tipo di moto, spiegando per ciascuno:
- perché è alternativa valida
- pro
- contro
- per quale tipo di motociclista è più adatta
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei un consulente motociclistico esperto di moto usate e valutazioni d'acquisto."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.35
    )

    return response.choices[0].message.content


link_annuncio = st.text_area(
    "Incolla qui il link all'annuncio",
    height=100,
    placeholder="https://www.subito.it/..."
)

analizza = st.button("Analizza annuncio con StoneSteel")

if analizza:
    if not link_annuncio.strip():
        st.warning("Incolla prima il link dell'annuncio.")
    else:
        with st.spinner("StoneSteel sta analizzando l'annuncio..."):
            testo = estrai_testo_annuncio(link_annuncio.strip())
            report = analizza_annuncio_con_ai(link_annuncio.strip(), testo)

        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.subheader("Analisi StoneSteel")
        st.write(report)
        st.markdown("</div>", unsafe_allow_html=True)
