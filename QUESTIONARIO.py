import os
import re
import json
import requests
import streamlit as st
from openai import OpenAI

# ============================================================
# CONFIG COMPATIBILE MAC + STREAMLIT CLOUD
# ============================================================

def leggi_secret(nome, default=""):
    try:
        return st.secrets.get(nome, default)
    except Exception:
        return default


try:
    from config import OPENAI_API_KEY, LOGO_PATH
except Exception:
    OPENAI_API_KEY = leggi_secret("OPENAI_API_KEY", "")
    LOGO_PATH = leggi_secret("LOGO_PATH", "stonesteel_logo.png")


st.set_page_config(
    page_title="StoneSteel Moto Advisor",
    page_icon="🏍️",
    layout="centered"
)

# ============================================================
# STILE GRAFICO
# ============================================================

st.markdown("""
<style>
.stApp {
    background-color: #0f1115;
    color: white;
}

.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: white;
    text-align: center;
}

p, label, div {
    color: #d6d6d6;
}

.stTextArea textarea,
.stTextInput input {
    background-color: #1b2029;
    color: white;
    border-radius: 10px;
    border: 1px solid #2f3642;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: white !important;
    color: black !important;
    border-radius: 10px;
    border: 1px solid #2f3642;
}

.stSelectbox div[data-baseweb="select"] * {
    color: black !important;
}

div[data-baseweb="popover"] * {
    color: black !important;
}

.stButton button {
    background-color: #d4af37 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: bold !important;
    padding: 12px 20px !important;
    width: 100% !important;
}

.stButton button * {
    color: #000000 !important;
}

.stButton button p {
    color: #000000 !important;
}

.stButton button span {
    color: #000000 !important;
}

.hero-box {
    background: linear-gradient(135deg, #151922 0%, #0f1115 100%);
    border: 1px solid #2a2f3a;
    border-radius: 18px;
    padding: 30px;
    margin-bottom: 25px;
    text-align: center;
}

.result-box {
    background-color: #151922;
    border: 1px solid #2a2f3a;
    border-radius: 16px;
    padding: 22px;
    margin-top: 20px;
}

.small-text {
    color: #b8b8b8;
    font-size: 15px;
    text-align: center;
}

.motorcycle-placeholder {
    width: 150px;
    height: 100px;
    border-radius: 12px;
    background-color: #1b2029;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #2f3642;
    font-size: 36px;
}

.cancel-button-text {
    color: #b8b8b8;
    font-size: 14px;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNZIONI
# ============================================================

def pulisci_testo(testo):
    if testo is None:
        return ""

    testo = str(testo)

    sostituzioni = {
        "###": "",
        "##": "",
        "#": "",
        "**": "",
        "---": "",
        "€": "EUR",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "•": "-",
    }

    for vecchio, nuovo in sostituzioni.items():
        testo = testo.replace(vecchio, nuovo)

    return testo.strip()


def cerca_foto_moto(nome_modello):
    try:
        query = f"{nome_modello} motorcycle"

        url = "https://commons.wikimedia.org/w/rest.php/v1/search/media"

        params = {
            "q": query,
            "type": "image",
            "limit": 1
        }

        headers = {
            "User-Agent": "StoneSteelMotoCheck/1.0"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()
        pages = data.get("pages", [])

        if not pages:
            return None

        primo = pages[0]

        thumbnail = primo.get("thumbnail", {})
        original = primo.get("originalimage", {})

        if thumbnail and thumbnail.get("url"):
            return thumbnail.get("url")

        if original and original.get("source"):
            return original.get("source")

        return None

    except Exception:
        return None


def estrai_json_da_testo(testo):
    try:
        return json.loads(testo)
    except Exception:
        pass

    match = re.search(r"\{.*\}", testo, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    return None


def genera_5_modelli(risposte):
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY non configurata. Inseriscila nei Secrets di Streamlit Cloud."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Sei StoneSteel Moto Advisor, consulente esperto di moto usate, custom, touring, naked, adventure, scrambler, café racer, moto vintage e moto moderne.

L'utente ha compilato un questionario a risposta libera. Alcune risposte possono essere incomplete, vaghe o mancanti.

Devi interpretare il profilo reale dell'utente e suggerire 5 modelli di moto coerenti.

Non limitarti ai desideri dichiarati: valuta anche uso reale, budget, esperienza, corporatura, sicurezza nelle manovre, peso, altezza sella, comfort, passeggero, manutenzione, rivendibilità, affidabilità e rischio acquisto usato.

Domande e risposte:

1. Tipo di moto che piace istintivamente:
{risposte["q1"]}

2. Moto già amate:
{risposte["q2"]}

3. Moto o categorie escluse:
{risposte["q3"]}

4. Uso reale della moto:
{risposte["q4"]}

5. Ambiente di guida più frequente:
{risposte["q5"]}

6. Chilometri annui previsti:
{risposte["q6"]}

7. Budget massimo di acquisto:
{risposte["q7"]}

8. Nuovo, usato recente o usato economico:
{risposte["q8"]}

9. Budget annuo manutenzione e gestione:
{risposte["q9"]}

10. Esperienza motociclistica:
{risposte["q10"]}

11. Sicurezza nelle manovre da fermo:
{risposte["q11"]}

12. Altezza e corporatura:
{risposte["q12"]}

13. Uso con passeggero:
{risposte["q13"]}

14. Necessità di carico:
{risposte["q14"]}

15. Importanza del comfort:
{risposte["q15"]}

16. Moto emozionale o razionale:
{risposte["q16"]}

17. Tipo di guida preferita:
{risposte["q17"]}

18. Paure principali nell'acquisto:
{risposte["q18"]}

Devi restituire SOLO un JSON valido, senza markdown e senza testo prima o dopo.

Struttura obbligatoria del JSON:

{{
  "profilo_utente": "testo descrittivo concreto",
  "categoria_consigliata": "categoria o combinazione di categorie",
  "modelli": [
    {{
      "marca": "Marca",
      "modello": "Modello",
      "anni_consigliati": "es. 2018-2023",
      "motore": "motore/cilindrata indicativa",
      "perche_adatta": "spiegazione",
      "limiti": "limiti principali",
      "fascia_prezzo_usato": "fascia indicativa in euro",
      "controlli_usato": "cosa controllare",
      "punteggio": 0
    }}
  ],
  "modello_piu_consigliato": "Marca Modello",
  "modello_emozionale": "Marca Modello",
  "modello_razionale": "Marca Modello",
  "modello_da_evitare": "modello o categoria da evitare",
  "conclusione": "conclusione StoneSteel Garage"
}}

Regole:
- Inserisci esattamente 5 modelli.
- I punteggi devono essere da 0 a 100.
- Scrivi in italiano.
- Non inventare prezzi certi: usa fasce indicative.
- Se mancano risposte, ragiona con prudenza.
- Non proporre solo moto costose.
- Inserisci almeno una scelta razionale, una emozionale e una usata intelligente.
- Considera sempre peso, altezza sella, manutenzione, affidabilità, rivendibilità e rischio acquisto usato.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei un consulente motociclistico esperto. Rispondi solo in JSON valido."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    testo = response.choices[0].message.content
    dati = estrai_json_da_testo(testo)

    if dati is None:
        raise ValueError("Non sono riuscito a leggere il JSON restituito da ChatGPT.")

    return dati


def genera_report_modello(nome_modello, profilo_utente):
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY non configurata. Inseriscila nei Secrets di Streamlit Cloud."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Sei StoneSteel Moto Advisor, consulente esperto di moto usate.

Genera un report generale completo sul seguente modello:

MODELLO:
{nome_modello}

CONTESTO PROFILO UTENTE:
{profilo_utente}

Il report deve essere in italiano, concreto, utile per chi sta valutando l'acquisto.

NON usare markdown complesso.
NON usare ###.
NON usare **.

Struttura obbligatoria:

1. SINTESI DEL MODELLO
Descrivi la moto in modo chiaro.

2. IDENTITÀ DELLA MOTO
Spiega che tipo di moto è, a chi parla, che carattere ha.

3. DATI TECNICI INDICATIVI
Motore, cilindrata, potenza indicativa, peso indicativo, altezza sella indicativa, uso principale.
Se non sei sicuro, usa formule prudenti come "indicativamente" o "a seconda dell'anno".

4. PREGI PRINCIPALI
Elenco concreto.

5. DIFETTI E LIMITI
Elenco concreto.

6. PER CHI È ADATTA
Spiega il profilo ideale.

7. PER CHI È SCONSIGLIATA
Spiega chi dovrebbe evitarla.

8. COSA CONTROLLARE SULL'USATO
Controlli pratici prima dell'acquisto.

9. FASCIA PREZZO NUOVO
Indica una fascia realistica se il modello è ancora in vendita.
Se non è più in vendita, scrivi "non più disponibile nuova" e indica l'ultimo posizionamento indicativo.

10. FASCIA PREZZO USATO
Indica fasce indicative per anno, chilometraggio e condizioni.

11. COSTI DI GESTIONE
Manutenzione, gomme, assicurazione, consumi, ricambi.

12. VALUTAZIONE DEGLI ESPERTI STONESTEEL GARAGE
Valutazione lunga, concreta, non generica.

13. CONCLUSIONE FINALE
Spiega se il modello è coerente con il profilo dell'utente e con quali cautele.

Regole:
- Non inventare numeri certi.
- Usa fasce indicative.
- Se ci sono molte versioni, distinguile.
- Non fare promesse assolute.
- Scrivi in stile professionale ma leggibile.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Sei un consulente motociclistico StoneSteel. Scrivi report chiari, concreti e prudenti."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
    )

    return pulisci_testo(response.choices[0].message.content)


def cancella_tutto():
    campi = [
        "q1", "q2", "q3", "q4", "q5", "q6",
        "q7", "q8", "q9", "q10", "q11", "q12",
        "q13", "q14", "q15", "q16", "q17", "q18"
    ]

    for campo in campi:
        st.session_state[campo] = ""

    st.session_state.risultato_advisor = None
    st.session_state.report_modello = None
    st.session_state.modello_selezionato = None


# ============================================================
# SESSION STATE
# ============================================================

if "risultato_advisor" not in st.session_state:
    st.session_state.risultato_advisor = None

if "report_modello" not in st.session_state:
    st.session_state.report_modello = None

if "modello_selezionato" not in st.session_state:
    st.session_state.modello_selezionato = None


# ============================================================
# HEADER
# ============================================================

st.markdown('<div class="hero-box">', unsafe_allow_html=True)

if os.path.exists(LOGO_PATH):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO_PATH, use_container_width=True)
else:
    st.warning("Logo non trovato. Controlla che il file si chiami stonesteel_logo.png")

st.markdown(
    "<h1>Troviamo insieme la moto per te</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p class="small-text">
    Rispondi liberamente anche solo ad alcune domande. StoneSteel analizzerà il tuo profilo e ti proporrà 5 modelli coerenti.<br>
    Ovviamente, a più domande risponderai, più sarà precisa la ricerca.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# QUESTIONARIO
# ============================================================

st.subheader("Questionario StoneSteel Moto Advisor")

q1 = st.text_area("1. Che tipo di moto ti piace istintivamente?", height=70, key="q1")
q2 = st.text_area("2. Ci sono moto che ami già?", height=70, key="q2")
q3 = st.text_area("3. Ci sono moto o categorie che vuoi escludere?", height=70, key="q3")
q4 = st.text_area("4. Come useresti davvero la moto nella vita reale?", height=70, key="q4")
q5 = st.text_area("5. In che ambiente guiderai più spesso?", height=70, key="q5")
q6 = st.text_area("6. Quanti chilometri pensi di fare in un anno?", height=70, key="q6")
q7 = st.text_area("7. Qual è il tuo budget massimo di acquisto?", height=70, key="q7")
q8 = st.text_area("8. Vuoi comprare nuovo, usato recente o usato economico?", height=70, key="q8")
q9 = st.text_area("9. Quanto vuoi spendere ogni anno per manutenzione, gomme, assicurazione e imprevisti?", height=70, key="q9")
q10 = st.text_area("10. Che esperienza hai in moto?", height=70, key="q10")
q11 = st.text_area("11. Quanto ti senti sicuro nelle manovre da fermo?", height=70, key="q11")
q12 = st.text_area("12. Quanto sei alto e che corporatura hai?", height=70, key="q12")
q13 = st.text_area("13. Userai spesso la moto con passeggero?", height=70, key="q13")
q14 = st.text_area("14. Ti servono borse, bauletto o capacità di carico?", height=70, key="q14")
q15 = st.text_area("15. Quanto conta il comfort?", height=70, key="q15")
q16 = st.text_area("16. Preferisci una moto emozionale o razionale?", height=70, key="q16")
q17 = st.text_area("17. Che tipo di guida ti piace?", height=70, key="q17")
q18 = st.text_area("18. Cosa ti spaventa di più nell'acquisto?", height=70, key="q18")

st.markdown(
    """
    <p class="cancel-button-text">
    Vuoi ricominciare da zero?
    </p>
    """,
    unsafe_allow_html=True
)

st.button("Cancella tutti i campi", on_click=cancella_tutto)

risposte = {
    "q1": q1,
    "q2": q2,
    "q3": q3,
    "q4": q4,
    "q5": q5,
    "q6": q6,
    "q7": q7,
    "q8": q8,
    "q9": q9,
    "q10": q10,
    "q11": q11,
    "q12": q12,
    "q13": q13,
    "q14": q14,
    "q15": q15,
    "q16": q16,
    "q17": q17,
    "q18": q18,
}

almeno_una_risposta = any(str(v).strip() for v in risposte.values())

if st.button("Trova le 5 moto più adatte a me"):
    if not almeno_una_risposta:
        st.error("Compila almeno una risposta prima di generare il consiglio.")
    else:
        with st.spinner("StoneSteel sta analizzando il tuo profilo..."):
            try:
                st.session_state.risultato_advisor = genera_5_modelli(risposte)
                st.session_state.report_modello = None
                st.session_state.modello_selezionato = None
                st.success("Analisi completata.")
            except Exception as e:
                st.error(f"Errore durante la generazione: {e}")


# ============================================================
# RISULTATI 5 MODELLI
# ============================================================

if st.session_state.risultato_advisor:

    dati = st.session_state.risultato_advisor
    modelli = dati.get("modelli", [])

    st.markdown('<div class="result-box">', unsafe_allow_html=True)

    st.subheader("Profilo motociclistico")
    st.write(dati.get("profilo_utente", ""))

    st.subheader("Categoria consigliata")
    st.write(dati.get("categoria_consigliata", ""))

    st.subheader("5 modelli consigliati")

    nomi_modelli = []

    for i, moto in enumerate(modelli, start=1):
        marca = moto.get("marca", "")
        modello = moto.get("modello", "")
        nome_completo = f"{marca} {modello}".strip()
        nomi_modelli.append(nome_completo)

        foto_url = cerca_foto_moto(nome_completo)

        col_img, col_text = st.columns([1, 3])

        with col_img:
            if foto_url:
                st.image(foto_url, width=150)
            else:
                st.markdown(
                    """
                    <div class="motorcycle-placeholder">
                        🏍️
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_text:
            st.markdown(f"### {i}. {nome_completo}")
            st.write(f"**Anni consigliati:** {moto.get('anni_consigliati', '')}")
            st.write(f"**Motore:** {moto.get('motore', '')}")
            st.write(f"**Perché è adatta:** {moto.get('perche_adatta', '')}")
            st.write(f"**Limiti:** {moto.get('limiti', '')}")
            st.write(f"**Fascia prezzo usato:** {moto.get('fascia_prezzo_usato', '')}")
            st.write(f"**Cosa controllare:** {moto.get('controlli_usato', '')}")
            st.write(f"**Punteggio coerenza:** {moto.get('punteggio', '')}/100")

        st.divider()

    st.subheader("Sintesi StoneSteel")

    st.write(f"**Modello più consigliato:** {dati.get('modello_piu_consigliato', '')}")
    st.write(f"**Modello emozionale:** {dati.get('modello_emozionale', '')}")
    st.write(f"**Modello razionale:** {dati.get('modello_razionale', '')}")
    st.write(f"**Modello da evitare:** {dati.get('modello_da_evitare', '')}")

    st.write(dati.get("conclusione", ""))

    st.markdown('</div>', unsafe_allow_html=True)

    if nomi_modelli:
        st.subheader("Approfondisci un modello")

        modello_scelto = st.selectbox(
            "Scegli uno dei 5 modelli per generare il report generale",
            nomi_modelli,
            key="select_modello"
        )

        st.session_state.modello_selezionato = modello_scelto

        if st.button("Genera report generale del modello"):
            with st.spinner("StoneSteel sta generando il report del modello..."):
                try:
                    profilo = dati.get("profilo_utente", "")
                    st.session_state.report_modello = genera_report_modello(
                        modello_scelto,
                        profilo
                    )
                    st.success("Report modello generato.")
                except Exception as e:
                    st.error(f"Errore durante la generazione del report modello: {e}")


# ============================================================
# REPORT MODELLO
# ============================================================

if st.session_state.report_modello:

    st.markdown('<div class="result-box">', unsafe_allow_html=True)

    st.subheader(f"Report generale modello - {st.session_state.modello_selezionato}")

    st.write(st.session_state.report_modello)

    st.markdown('</div>', unsafe_allow_html=True)
