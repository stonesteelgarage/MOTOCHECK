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
.info-box {
    background-color: #1a1a1a;
    border-left: 5px solid #f5c400;
    padding: 16px;
    border-radius: 10px;
    margin-top: 18px;
    margin-bottom: 18px;
}
</style>
""", unsafe_allow_html=True)


try:
    st.image(LOGO_PATH, width=170)
except Exception:
    pass


st.title("StoneSteel Analisi Annuncio")

st.write(
    "Incolla il link di un annuncio moto. StoneSteel proverà a leggerlo automaticamente "
    "e produrrà un'analisi d'acquisto completa."
)


st.markdown("""
<div class="info-box">
<b>Se il report non legge l'annuncio</b>, incolla nel box qui sotto tutte le informazioni dell'annuncio:
marca, modello, anno, chilometri, prezzo, accessori, descrizione, città, tagliandi, proprietari, eventuali difetti dichiarati.
Procederemo comunque con l'analisi StoneSteel.
</div>
""", unsafe_allow_html=True)


def estrai_testo_annuncio(url):
    if not url.strip():
        return ""

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
                f"Pagina non leggibile direttamente. Codice errore: {response.status_code}. "
                "Usare le informazioni manuali inserite dall'utente."
            )

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = soup.title.string if soup.title else ""

        testo = soup.get_text(separator="\n")
        righe = [r.strip() for r in testo.splitlines() if r.strip()]
        testo_pulito = "\n".join(righe)

        return f"TITOLO PAGINA:\n{title}\n\nTESTO ANNUNCIO:\n{testo_pulito}"[:12000]

    except Exception as e:
        return (
            f"Errore lettura annuncio: {str(e)}. "
            "Usare le informazioni manuali inserite dall'utente."
        )


def analizza_annuncio_con_ai(url, testo_annuncio, info_manuali):
    if not OPENAI_API_KEY:
        return "Errore: manca OPENAI_API_KEY nei Secrets di Streamlit."

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Sei StoneSteel Garage, consulente esperto di moto usate.

L'utente ha inserito questo link annuncio:
{url}

Testo letto automaticamente dall'annuncio:
{testo_annuncio}

Informazioni manuali inserite dall'utente:
{info_manuali}

Devi produrre un'analisi professionale in italiano.

Regole fondamentali:
- Se il link non è leggibile ma l'utente ha inserito informazioni manuali, usa quelle informazioni come base principale.
- Non dire che l'analisi è generica se sono presenti marca, modello, anno, prezzo, km e descrizione.
- Se mancano dati importanti, evidenzialo chiaramente.
- Non inventare dati certi non presenti.
- Puoi però fare valutazioni tecniche prudenti basate su modello, categoria e anno.
- Non usare markdown complesso.
- Non usare ###.
- Non usare simboli strani.
- Scrivi in modo concreto, professionale e leggibile.

Struttura obbligatoria del report:

1. Sintesi StoneSteel dell'annuncio
Spiega che moto è, che tipo di acquisto rappresenta e per quale motociclista può essere adatta.

2. Qualità dell'annuncio
Valuta se l'annuncio è completo, povero di informazioni, credibile, interessante o da approfondire.

3. Prima impressione sul prezzo
Valuta se il prezzo sembra:
- interessante
- corretto
- alto
- da trattare
- non valutabile per mancanza dati

4. Punti positivi evidenti
Elenca i punti favorevoli emersi.

5. Punti critici dell'annuncio
Indica cosa non convince:
- dati mancanti
- foto mancanti
- prezzo poco chiaro
- tagliandi non dichiarati
- chilometraggio da verificare
- accessori non omologati
- descrizione troppo povera

6. Difetti e rischi possibili del modello
Indica le fragilità tipiche del modello o della categoria.
Se il modello non è identificato con certezza, ragiona per categoria.

7. Checklist prima dell'acquisto
Scrivi almeno 18 controlli pratici:
- libretto
- targa
- telaio
- proprietari
- tagliandi
- gomme
- freni
- sospensioni
- trasmissione
- frizione
- motore
- perdite olio
- elettronica
- batteria
- scarichi
- accessori
- omologazioni
- prova su strada

8. Domande da fare al venditore
Scrivi almeno 12 domande concrete.

9. Valutazione rischio StoneSteel
Scegli uno:
- Basso
- Medio
- Alto

Spiega bene il motivo.

10. Opinione finale StoneSteel
Dai un parere netto:
- da vedere subito
- interessante ma da trattare
- da verificare con attenzione
- meglio lasciar perdere

11. Tre modelli alternativi
Suggerisci tre modelli alternativi coerenti.
Per ciascuno indica:
- perché sceglierlo
- pro
- contro
- per chi è più adatto
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
    height=80,
    placeholder="https://www.subito.it/..."
)


info_manuali = st.text_area(
    "Se il link non viene letto, incolla qui testo annuncio o caratteristiche moto",
    height=220,
    placeholder=(
        "Esempio:\n"
        "Harley-Davidson Road Glide 114\n"
        "Anno 2021\n"
        "Km 18.000\n"
        "Prezzo 25.900 euro\n"
        "Città Cuneo\n"
        "Tagliandi Harley ufficiali\n"
        "Scarichi omologati\n"
        "Unico proprietario\n"
        "Descrizione del venditore..."
    )
)


if st.button("Analizza annuncio con StoneSteel"):
    if not link_annuncio.strip() and not info_manuali.strip():
        st.warning("Inserisci almeno il link dell'annuncio oppure le informazioni manuali della moto.")
    else:
        with st.spinner("StoneSteel sta analizzando l'annuncio..."):
            testo = estrai_testo_annuncio(link_annuncio.strip())
            report = analizza_annuncio_con_ai(
                link_annuncio.strip(),
                testo,
                info_manuali.strip()
            )

        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.subheader("Analisi StoneSteel")
        st.write(report)
        st.markdown("</div>", unsafe_allow_html=True)
