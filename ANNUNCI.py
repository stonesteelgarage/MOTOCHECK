import re
import requests
import streamlit as st
from bs4 import BeautifulSoup

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

    testo = str(testo).strip().lower()

    testo = re.sub(
        r"\s+",
        "-",
        testo
    )

    return testo


# ============================================================
# CERCA ANNUNCI
# ============================================================

def cerca_annunci_subito(
    marca,
    modello,
    max_annunci=10
):

    query = f"{marca} {modello}"

    query_url = pulisci_query(query)

    url = (
        "https://www.subito.it/annunci-italia/"
        f"vendita/moto-e-scooter/?q={query_url}"
    )

    headers = {

        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    if response.status_code != 200:

        raise ValueError(
            f"Errore Subito {response.status_code}"
        )

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    annunci = []

    links = soup.find_all("a")

    visti = set()

    for link in links:

        href = link.get("href", "")

        titolo = link.get_text(
            " ",
            strip=True
        )

        if not href:
            continue

        if not titolo:
            continue

        if "subito.it" not in href:
            continue

        if href in visti:
            continue

        if len(titolo) < 10:
            continue

        visti.add(href)

        annunci.append({

            "titolo": titolo[:180],

            "link": href
        })

        if len(annunci) >= max_annunci:
            break

    return annunci, url


# ============================================================
# UI
# ============================================================

st.title("StoneSteel Annunci Moto")

st.subheader(
    "Trova annunci moto compatibili"
)

st.write(
    "Inserisci marca e modello per cercare "
    "10 annunci compatibili online."
)

marca = st.text_input(
    "Marca"
)

modello = st.text_input(
    "Modello"
)

# ============================================================
# RICERCA
# ============================================================

if st.button("Cerca 10 annunci"):

    if not marca or not modello:

        st.error(
            "Inserisci marca e modello."
        )

    else:

        try:

            with st.spinner(
                "StoneSteel sta cercando annunci..."
            ):

                annunci, url_ricerca = (
                    cerca_annunci_subito(
                        marca,
                        modello
                    )
                )

            st.success(
                "Ricerca completata."
            )

            st.markdown(
                f"""
                <a href="{url_ricerca}" target="_blank">
                    <button style="
                        background-color:#f0c040;
                        color:black;
                        font-weight:bold;
                        border:none;
                        padding:12px 20px;
                        border-radius:10px;
                        cursor:pointer;
                        width:100%;
                        margin-bottom:20px;
                    ">
                        Apri ricerca completa su Subito
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

            if not annunci:

                st.warning(
                    "Non ho trovato annunci leggibili automaticamente."
                )

            else:

                st.subheader(
                    "Annunci trovati"
                )

                for i, annuncio in enumerate(
                    annunci,
                    start=1
                ):

                    titolo = annuncio["titolo"]

                    link = annuncio["link"]

                    st.markdown(
                        f"""
                        <div class="card">

                            <div class="card-title">
                                {i}. {titolo}
                            </div>

                            <div class="card-link">
                                <a href="{link}" target="_blank">
                                    Apri annuncio
                                </a>
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        except Exception as e:

            st.error(
                f"Errore durante la ricerca: {e}"
            )
