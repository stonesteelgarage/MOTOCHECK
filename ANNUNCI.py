import re
import streamlit as st

st.set_page_config(
    page_title="StoneSteel Annunci Moto",
    layout="centered"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #000000 !important;
    color: white !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stMain"],
.block-container {
    background-color: #000000 !important;
}

h1, h2, h3, h4, h5, h6,
p, div, span, label {
    color: white !important;
}

.stTextInput input {
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid #555555 !important;
    border-radius: 8px !important;
}

.stButton button {
    background-color: #f0c040 !important;
    color: black !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
}

.stButton button * {
    color: black !important;
}

.card {
    background-color: #111111 !important;
    border: 1px solid #444444 !important;
    border-radius: 14px !important;
    padding: 16px !important;
    margin-bottom: 14px !important;
    color: white !important;
}

.card * {
    color: white !important;
}

.card-title {
    color: white !important;
    font-size: 18px !important;
    font-weight: bold !important;
    margin-bottom: 10px !important;
}

.card-description {
    color: #cccccc !important;
    margin-bottom: 12px !important;
}

.card-link a {
    color: #f0c040 !important;
    text-decoration: none !important;
    font-weight: bold !important;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNZIONI
# ============================================================

def pulisci_query(testo):

    testo = str(testo).strip()

    testo = re.sub(
        r"\s+",
        " ",
        testo
    )

    return testo


def genera_link_ricerche(marca, modello):

    query = pulisci_query(
        f"{marca} {modello}"
    )

    query_plus = query.replace(
        " ",
        "+"
    )

    query_dash = (
        query
        .replace(" ", "-")
        .lower()
    )

    return [

        {
            "sito": "Subito",

            "descrizione":
            "Ricerca annunci moto usate su Subito",

            "link":
            f"https://www.subito.it/annunci-italia/vendita/moto-e-scooter/?q={query_plus}"
        },

        {
            "sito": "Moto.it",

            "descrizione":
            "Ricerca moto usate su Moto.it",

            "link":
            f"https://www.moto.it/moto-usate/ricerca?term={query_plus}"
        },

        {
            "sito": "AutoScout24 Moto",

            "descrizione":
            "Ricerca moto usate su AutoScout24",

            "link":
            f"https://www.autoscout24.it/lst-moto/{query_dash}"
        },

        {
            "sito": "Bakeca",

            "descrizione":
            "Ricerca annunci su Bakeca",

            "link":
            f"https://www.bakeca.it/annunci/motori/?q={query_plus}"
        },

        {
            "sito": "Facebook Marketplace",

            "descrizione":
            "Ricerca Marketplace Facebook",

            "link":
            f"https://www.facebook.com/marketplace/search/?query={query_plus}"
        },

        {
            "sito": "Google Ricerca",

            "descrizione":
            "Ricerca Google dedicata alla moto",

            "link":
            f"https://www.google.com/search?q={query_plus}+moto+usata"
        },

        {
            "sito": "Google Shopping",

            "descrizione":
            "Confronto prezzi online",

            "link":
            f"https://www.google.com/search?tbm=shop&q={query_plus}"
        },

        {
            "sito": "YouTube",

            "descrizione":
            "Video recensioni e prove",

            "link":
            f"https://www.youtube.com/results?search_query={query_plus}"
        },

        {
            "sito": "Forum e Reddit",

            "descrizione":
            "Problemi noti e opinioni utenti",

            "link":
            f"https://www.google.com/search?q={query_plus}+forum+reddit"
        },

        {
            "sito": "Ricerca Prezzi",

            "descrizione":
            "Analisi mercato usato",

            "link":
            f"https://www.google.com/search?q={query_plus}+prezzo+usato"
        },
    ]

# ============================================================
# UI
# ============================================================

st.title("StoneSteel Annunci Moto")

st.subheader(
    "Ricerca mercato usato"
)

st.write(
    "Inserisci marca e modello per generare "
    "ricerche rapide sui principali portali moto."
)

marca = st.text_input("Marca")

modello = st.text_input("Modello")

# ============================================================
# GENERAZIONE
# ============================================================

if st.button("Genera ricerche annunci"):

    if not marca or not modello:

        st.error(
            "Inserisci marca e modello."
        )

    else:

        risultati = genera_link_ricerche(
            marca,
            modello
        )

        st.success(
            "Ricerche generate."
        )

        st.subheader(
            "Portali disponibili"
        )

        for i, risultato in enumerate(
            risultati,
            start=1
        ):

            st.markdown(
                f"""
                <div class="card">

                    <div class="card-title">
                        {i}. {risultato["sito"]}
                    </div>

                    <div class="card-description">
                        {risultato["descrizione"]}
                    </div>

                    <div class="card-link">
                        <a href="{risultato["link"]}" target="_blank">
                            Apri ricerca
                        </a>
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )
