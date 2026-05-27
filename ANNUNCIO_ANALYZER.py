import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
LOGO_PATH = st.secrets.get("LOGO_PATH", "stonesteel_logo.png")


st.set_page_config(
    page_title="StoneSteel Analisi Annuncio",
    page_icon="🏍️",
    layout="centered"
)


st.markdown("""
<style>
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
.stButton > button {
    background-color: #f5c400;
    color: black !important;
    font-weight: bold;
    border-radius: 10px;
    padding: 0.7rem 1.2rem;
    border: none;
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


try:
    st.image(LOGO_PATH, width=170)
except Exception:
    pass


st.title("StoneSteel Analisi Annuncio")

st.write(
    "Incolla il link di un annuncio moto. StoneSteel analizzerà il mezzo, "
    "i rischi, i difetti probabili, la checklist e tre modelli alternativi."
)


def estrai_testo_annuncio(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return f"Pagina non leggibile direttamente. Codice errore: {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = soup.title.string if soup.title else ""

        testo = soup.get_text(separator="\n")
        righe = [r.strip() for r in testo.splitlines() if r.strip()]
        testo_pulito = "\n".join(righe)

        return f"TITOLO PAGINA:\n{title}\n\nTESTO ANNUNCIO:\n{testo_pulito}"[:12000]

    except Exception as e:
        return f"Errore lettura annuncio: {str(e)}"


def analizza_annuncio_con_ai(url, testo_annuncio):
    if not OPENAI_API_KEY:
        return "Errore: manca OPENAI_API_KEY nei Secrets di Streamlit."

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Sei StoneSteel Garage, consulente esperto di moto usate.

L'utente ha incollato questo link:
{url}

Testo estratto dall'annuncio:
{testo_annuncio}

Produci un'analisi professionale in italiano.

Regole:
- Non usare markdown complesso.
- Non usare ###.
- Non inventare dati certi se non sono presenti.
- Se l'annuncio è incompleto, dillo chiaramente.
- Se non riesci a leggere bene il link, fai comunque una valutazione prudente.

Struttura obbligatoria:

1. Sintesi StoneSteel dell'annuncio

2. Prima impressione su prezzo e qualità dell'annuncio

3. Punti positivi evidenti

4. Difetti e rischi possibili del modello

5. Checklist prima dell'acquisto
Scrivi almeno 15 controlli pratici.

6. Domande da fare al venditore
Scrivi almeno 10 domande.

7. Valutazione rischio StoneSteel
Scegli tra Basso, Medio, Alto.

8. Opinione finale StoneSteel
Dai un parere netto.

9. Tre modelli alternativi
Per ogni alternativa indica:
- perché sceglierla
- pro
- contro
- per chi è adatta
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei un consulente motociclistico esperto di moto usate."
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

if st.button("Analizza annuncio con StoneSteel"):
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
