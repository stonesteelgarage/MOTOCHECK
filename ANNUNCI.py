import re
import streamlit as st

# ============================================================
# CONFIG
# ============================================================

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
    background-color: #000000;
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

hr {
    border-color: #333333 !important;
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


def genera_link_ricerche(
    marca,
    modello
):

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
            "Annunci moto usate su Subito",

            "link":
            f"https://www.subito.it/annunci-italia/vendita/moto-e-scooter/?q={query_plus}"
        },

        {
            "sito": "Moto.it",

            "descrizione":
            "Annunci usato su Moto.it",

            "link":
            f"https://www.moto.it/moto-usate/ricerca?term={query_plus}"
        },

        {
            "sito": "AutoScout24 Moto",

            "descrizione":
            "Ricerca usato su AutoScout24",

            "link":
            f"https://www.autoscout24.it/lst-moto/{query_dash}"
        },

        {
            "sito": "Bakeca",

            "descrizione":
            "Annunci moto su Bakeca",

            "link":
            f"https://www.bakeca.it/annunci/motori/?q={query_plus}"
        },

        {
            "sito": "Facebook Marketplace",

            "descrizione":
            "Marketplace Facebook",

            "link":
            f"https://www.facebook.com/marketplace/search/?query={query_plus}"
        },

        {
            "sito": "Google Ricerca",

            "descrizione":
            "Ricerca Google dedicata",

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
    "Inserisci marca e modello "
    "per generare ricerche rapide "
    "sui principali portali moto."
)

marca = st.text_input(
    "Marca"
)

modello = st.text_input(
    "Modello"
)

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

        for risultato in risultati:

            st.markdown(
                f"### {risultato['sito']}"
            )

            st.write(
                risultato["descrizione"]
            )

            st.link_button(
                "Apri ricerca",
                risultato["link"]
            )

            st.markdown("---")
