import re
import streamlit as st

# ============================================================
# STREAMLIT CONFIG
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
    color: white;
}

h1, h2, h3, h4, h5, h6, p, div, span, label {
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

    background-color: #111111;

    border: 1px solid #444444;

    border-radius: 14px;

    padding: 16px;

    margin-bottom: 14px;
}

.card-title {

    font-size: 18px;

    font-weight: bold;

    margin-bottom: 10px;
}

.card-link a {

    color: #f0c040 !important;

    text-decoration: none !important;

    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# UTILITY
# ============================================================

def pulisci_query(testo):

    testo = str(testo).strip()

    testo = re.sub(
        r"\s+",
        " ",
        testo
    )

    return testo


# ============================================================
# GENERA LINK RICERCHE
# ============================================================

def genera_link_ricerche(
    marca,
    modello
):

    query = f"{marca} {modello}"

    query = pulisci_query(query)

    query_plus = query.replace(
        " ",
        "+"
    )

    query_dash = (
        query
        .replace(" ", "-")
        .lower()
    )

    risultati = [

        {
            "sito": "Subito",

            "descrizione":
            "Ricerca annunci usato su Subito",

            "link":
            f"https://www.subito.it/annunci-italia/vendita/moto-e-scooter/?q={query_plus}"
        },

        {
            "sito": "Moto.it",

            "descrizione":
            "Ricerca annunci usato su Moto.it",

            "link":
            f"https://www.moto.it/moto-usate/ricerca?term={query_plus}"
        },

        {
            "sito": "AutoScout24 Moto",

            "descrizione":
            "Ricerca annunci usato su AutoScout24",

            "link":
            f"https://www.autoscout24.it/lst-moto/{query_dash}"
        },

        {
            "sito": "Bakeca",

            "descrizione":
            "Ricerca annunci moto su Bakeca",

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
            "Ricerca Google Shopping",

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
            "sito": "Forum / Reddit",

            "descrizione":
            "Discussioni utenti e problemi noti",

            "link":
            f"https://www.google.com/search?q={query_plus}+reddit+forum"
        },

        {
            "sito": "Ricerca prezzi",

            "descrizione":
            "Confronto prezzi usato",

            "link":
            f"https://www.google.com/search?q={query_plus}+prezzo+usato"
        },
    ]

    return risultati


# ============================================================
# UI
# ============================================================

st.title("StoneSteel Annunci Moto")

st.subheader(
    "Ricerca annunci e mercato usato"
)

st.write(
    "Inserisci marca e modello per ottenere "
    "link rapidi ai principali portali "
    "di annunci moto."
)

marca = st.text_input(
    "Marca"
)

modello = st.text_input(
    "Modello"
)

# ============================================================
# GENERA RICERCHE
# ============================================================

if st.button("Genera ricerche annunci"):

    if not marca or not modello:

        st.error(
            "Inserisci marca e modello."
        )

    else:

        try:

            risultati = genera_link_ricerche(
                marca,
                modello
            )

            st.success(
                "Ricerche generate."
            )

            st.subheader(
                "Portali e ricerche disponibili"
            )

            for i, risultato in enumerate(
                risultati,
                start=1
            ):

                sito = risultato["sito"]

                descrizione = risultato["descrizione"]

                link = risultato["link"]

                st.markdown(
                    f"""
                    <div class="card">

                        <div class="card-title">
                            {i}. {sito}
                        </div>

                        <p>
                            {descrizione}
                        </p>

                        <div class="card-link">
                            <a href="{link}" target="_blank">
                                Apri ricerca
                            </a>
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

        except Exception as e:

            st.error(
                f"Errore durante la generazione: {e}"
            )
