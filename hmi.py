import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata
import base64

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Dashboard Transport", layout="wide")

PRIMARY = "#7CC043"   # vert BLS (comme les cartes)
DARK_BG = "#0B0F14"   # fond noir de la sidebar
TEXT_DARK = "#0E1117" # texte foncé sur fond vert




st.markdown(f"""
<style>
/* --- Sidebar noir + séparation verte --- */
[data-testid="stSidebar"] {{
  background-color: {DARK_BG} !important;
  border-right: 2px solid {PRIMARY} !important;
    border-top-right-radius: 18px;           /* ← ajuste le rayon ici */
  border-bottom-right-radius: 18px;     
   overflow: hidden;                        /* pour que le contenu suive la courbe */
  position: relative;                      /* nécessaire pour le ::after ci-dessous */
  box-shadow: 4px 0 14px rgba(0,0,0,.35);  /* (optionnel) un peu de profondeur */
}}   


/* --- Selectbox verte comme les cartes --- */
[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
  background-color: {PRIMARY} !important;
  color: {TEXT_DARK} !important;
  border: 1px solid {PRIMARY} !important;
  border-radius: 10px !important;
  min-height: 42px;
  font-weight: 600;
}}
/* Texte et icônes dans le select */
[data-testid="stSidebar"] div[data-baseweb="select"] input,
[data-testid="stSidebar"] div[data-baseweb="select"] span {{
  color: {TEXT_DARK} !important;
}}
[data-testid="stSidebar"] div[data-baseweb="select"] svg {{
  fill: {TEXT_DARK} !important;
}}

/* --- Menu déroulant (popup des options) --- */
div[data-baseweb="popover"] [role="listbox"] {{
  background-color: #101418 !important;
  border: 1px solid {PRIMARY} !important;
  border-radius: 10px !important;
}}
div[data-baseweb="popover"] [role="option"]:hover {{
  background-color: rgba(124,192,67,0.15) !important;
}}
div[data-baseweb="popover"] [aria-selected="true"] {{
  background-color: rgba(124,192,67,0.3) !important;
}}
</style>
""", unsafe_allow_html=True)


# charge le fichier image et l’encode en base64
with open("logo2.png", "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()
st.markdown(f"""
<style>


#header {{
    display: flex;
    align-items: center;
    justify-content: center; /* ✅ Centre horizontalement */
    background-color: #0E1117;
    padding: 15px 30px;
    border-bottom: 2px solid #7CC043;
    border-radius: 8px;
    margin-bottom: 25px;
    position: relative;
}}
#header-left {{
    display: flex;
    align-items: center;
    gap: 15px;
    position: absolute; /* ✅ Garde le logo à gauche */
    left: 30px;
}}
#header-left img {{
    height: 65px;
}}
#header h1 {{
    color: white;
    font-size: 26px;
    font-weight: 800;
    margin: 0;
    text-align: center;
}}
</style>

<div id="header">
    <div id="header-left">
        <img src="data:image/png;base64,{logo_b64}" alt="logo" />    
    </div>
    <h1> Suivi du transport de personnel</h1>
</div>
""", unsafe_allow_html=True)



# 
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #7CC043 0%, #5BAA29 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 12px 14px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.25) !important;
}

/* Label */
div[data-testid="stMetricLabel"] {
    color: white !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 15px !important;
}

/* Valeur */
div[data-testid="stMetricValue"] {
    color: white !important;
    font-weight: 900 !important;
    font-size: 30px !important;
}

/* Effet au survol */
div[data-testid="stMetric"]:hover {
    transform: scale(1.03);
    transition: 0.3s ease;
}
</style>
""", unsafe_allow_html=True)




GREEN_SCALE = [
    (0.00, "#F3FAE9"),
    (0.10, "#E6F4D3"),
    (0.20, "#D5EDB5"),
    (0.35, "#B6E27F"),
    (0.50, "#99D652"),
    (0.70, "#7CC043"),  # ta couleur principale
    (0.85, "#5AA52D"),
    (1.00, "#1E6A0E"),
]




st.divider()




# --- HMI ---
SHEET_ID_HMI = "1MsEzKIjae3pYGFgZVPRft6Zv21k7Jzt8-iXwyiLnoo0"  # 👈 remplace si besoin
SHEET_URL_HMI = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_HMI}/export?format=csv&gid=813428560"
SHEET_URL_HMI_NORMAL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_HMI}/export?format=csv&gid=1643109752"
SHEET_URL_HMI_SHIFT1 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_HMI}/export?format=csv&gid=407350218"
SHEET_URL_HMI_SHIFT2 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_HMI}/export?format=csv&gid=1002680487"
SHEET_URL_HMI_SHIFT3 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_HMI}/export?format=csv&gid=1117573875"



# ==============================
# UTILS
# ==============================
@st.cache_data
def load_csv(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.warning(f"Erreur de chargement : {e}")
        return pd.DataFrame()

def normalize(text):
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", text)

def convert_duration_to_minutes(duration_str):
    if pd.isna(duration_str) or not isinstance(duration_str, str):
        return 0
    h = re.search(r'(\d+)\s*h', duration_str)
    m = re.search(r'(\d+)\s*min', duration_str)
    total = 0
    if h:
        total += int(h.group(1)) * 60
    if m:
        total += int(m.group(1))
    return total

# ==============================
# LOAD DATA
# ==============================



# --- HMI ---
df_hmi = load_csv(SHEET_URL_HMI)
df_hmi_normal = load_csv(SHEET_URL_HMI_NORMAL)
df_hmi_shift1 = load_csv(SHEET_URL_HMI_SHIFT1)
df_hmi_shift2 = load_csv(SHEET_URL_HMI_SHIFT2)
df_hmi_shift3 = load_csv(SHEET_URL_HMI_SHIFT3)



# ==============================
# SIDEBAR
# ==============================
# st.sidebar.image("logo2.png", use_container_width =True)

st.sidebar.header("Filtres")
CAPACITE = 20
# st.sidebar.number_input("Capacité par véhicule", min_value=1, max_value=60, value=20)
entreprise = st.sidebar.selectbox("Site", ["HMI"])

# ==============================
# CHOIX DU SITE
# ==============================
if entreprise == "HMI":
    df_site = df_hmi
    df_normal_site = df_hmi_normal
    df_shift1_site = df_hmi_shift1
    df_shift2_site = df_hmi_shift2
    df_shift3_site = df_hmi_shift3



else:
    df_site = pd.DataFrame()
    df_normal_site = df_shift1_site = df_shift2_site = pd.DataFrame()

# ==============================
# METRIQUES
# ==============================
mask_personnes = (
    df_site["nom&prenom"].notna()
    & ~df_site["nom&prenom"].str.contains("arret|depart|pt de depart", case=False, na=False)
)

nb_vehicules = df_site["matricule"].dropna().nunique()
nb_chauffeurs = df_site["chauffeur"].dropna().nunique()
nb_shifts = df_site["shift"].dropna().nunique()
nb_personnes = df_site[mask_personnes]["nom&prenom"].count()

c1, c2, c3, c4 = st.columns(4)
c1.metric("🚐 Véhicules", nb_vehicules)
c2.metric("🧑‍✈️ Chauffeurs", nb_chauffeurs)
c3.metric("🕐 Equipes", nb_shifts)
c4.metric("👥 Personnes", nb_personnes)

st.divider()

# ==============================
# GRAPH TAUX DE REMPLISSAGE
# ==============================
st.subheader("📈 Taux de remplissage (%) par Chauffeur et Shift")

df_valid = df_site[mask_personnes].copy()
df_valid["chauffeur_norm"] = df_valid["chauffeur"].apply(normalize)

grouped = (
    df_valid.groupby(["shift", "chauffeur_norm"], dropna=True)
    .agg(nb_personnes=("nom&prenom", "nunique"))
    .reset_index()
)
grouped["taux_pct"] = (grouped["nb_personnes"] / CAPACITE * 100).round(1)

shifts = sorted(grouped["shift"].dropna().unique())
for i in range(0, len(shifts), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j >= len(shifts):
            break
        shift = shifts[i + j]
        df_s = grouped[grouped["shift"] == shift].sort_values("taux_pct", ascending=False)
        fig = px.bar(
            df_s,
            x="chauffeur_norm",
            y="taux_pct",
            text="taux_pct",
            title=f"{shift} — Taux de remplissage (%)",
            color="taux_pct",
            color_continuous_scale=GREEN_SCALE,   
            range_color=(0, 100)                 # pour garder la même échelle sur tous les graphes
        )
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig.update_yaxes(range=[0, 100], title="Taux (%)")
        fig.update_layout(xaxis_title="Chauffeur", margin=dict(l=20, r=20, t=60, b=20))
        cols[j].plotly_chart(fig, use_container_width=True)

st.divider()

# ==============================
# TABLEAUX PAR SHIFT
# ==============================
st.subheader("📋 Détails par Shift")

def prepare_shift_table(df_shift, shift_name):
    if df_shift.empty:
        return pd.DataFrame(columns=["Chauffeur", "Shift", "Circuit","Nb personnes"])

    df_shift = df_shift.rename(columns={
        "chauffeur": "Chauffeur",
        "shift": "Shift",
        "circuit": "Circuit",
        
    })
    df_shift["chauffeur_norm"] = df_shift["Chauffeur"].apply(normalize)
    df_shift["Durée_min"] = df_shift["Durée"].apply(convert_duration_to_minutes)
    df_shift["Durée"] = df_shift.apply(
        lambda r: f"{r['Durée']} ⚠️" if r["Durée_min"] > 90 else r["Durée"], axis=1
    )

    merged = pd.merge(
        df_shift,
        grouped[["shift", "chauffeur_norm", "nb_personnes"]],
        how="left",
        left_on=["Shift", "chauffeur_norm"],
        right_on=["shift", "chauffeur_norm"]
    )

    merged = merged[["Chauffeur", "Shift", "Circuit", "nb_personnes"]]
    merged = merged.rename(columns={"nb_personnes": "Nb personnes"})
    return merged
    

# --- TABLES ---
# === Entêtes vertes pour st.dataframe (Streamlit 1.50–1.51) ===
st.markdown(f"""
<style>
/* 1) Header cells (sélecteur principal) */
div[data-testid="stDataFrame"] div[role="columnheader"] {{
  background: linear-gradient(135deg, {PRIMARY} 0%, #5BAA29 100%) !important;
  color: {TEXT_DARK} !important;
  font-weight: 800 !important;
  border-bottom: 2px solid #5BAA29 !important;
  border-top-left-radius: 8px !important;
  border-top-right-radius: 8px !important;
  display: flex; align-items: center; justify-content: center;
  padding: 6px 0 !important;
}}

/* 2) Fallbacks (selon builds 1.50/1.51) */
div[data-testid="stDataFrame"] [data-testid="stHeader"] > div,
div[data-testid="stDataFrame"] div[aria-rowindex="1"] div[role="columnheader"] {{
  background: linear-gradient(135deg, {PRIMARY} 0%, #5BAA29 100%) !important;
  color: {TEXT_DARK} !important;
  font-weight: 800 !important;
}}

/* 3) Texte à l’intérieur des headers */
div[data-testid="stDataFrame"] div[role="columnheader"] p {{
  color: {TEXT_DARK} !important;
  font-weight: 800 !important;
  margin: 0 !important;
  text-transform: capitalize;
}}

/* 4) Corps + hover (optionnel) */
div[data-testid="stDataFrame"] div[role="cell"] {{
  border-bottom: 1px solid rgba(124,192,67,.15) !important;
}}
div[data-testid="stDataFrame"] div[role="row"]:hover div[role="cell"] {{
  background-color: rgba(124,192,67,.08) !important;
  transition: .25s ease;
}}

/* 5) Contour global (optionnel) */
div[data-testid="stDataFrame"] {{
  border: 1.5px solid rgba(124,192,67,.4) !important;
  border-radius: 10px !important;
  padding: 4px !important;
  box-shadow: 0 4px 14px rgba(0,0,0,.15);
}}
</style>
""", unsafe_allow_html=True)



# if entreprise == "Logiprod":
#     st.markdown("### 🕐 Normal [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1AWwS0Fh7kGqF45LLthDnNUw98p6ZhOA&ll=33.5164216889364%2C-7.668005000000008&z=11)", unsafe_allow_html=True)
#     table_normal = prepare_shift_table(df_normal_site, "normal")
#     st.dataframe(table_normal, use_container_width=True, hide_index=True)

#     st.markdown("### 🕐 Shift 1 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1ORX0VuY0VO8heJBnkg7sm3IkfZqbM9s&ll=33.47766561562251%2C-7.736224999999992&z=12)", unsafe_allow_html=True)
#     table1 = prepare_shift_table(df_shift1_site, "shift 1")
#     st.dataframe(table1, use_container_width=True, hide_index=True)

#     st.markdown("### 🕐 Shift 2 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1CgnWy11ud3Zyuow2S587sD8BQsdowQo&ll=33.454163890190735%2C-7.728035000000006&z=12)", unsafe_allow_html=True)
#     table2 = prepare_shift_table(df_shift2_site, "shift 2")
#     st.dataframe(table2, use_container_width=True, hide_index=True)

# if entreprise == "Casa hub":
#     st.markdown("### 🕐 Shift 1 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1o3MrlHn32N8xH_PWpIsxtd163sYAshM&ll=33.515104057542175%2C-7.642830999999996&z=11)", unsafe_allow_html=True)
#     table1 = prepare_shift_table(df_shift1_site, "shift 1")
#     st.dataframe(table1, use_container_width=True, hide_index=True)

#     st.markdown("### 🕐 Shift 2 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1gVo5H_-DJbb5mUe7vgdh-nruCKeiEos&ll=33.56991600416464%2C-7.599525499999997&z=10)", unsafe_allow_html=True)
#     table2 = prepare_shift_table(df_shift2_site, "shift 2")
#     st.dataframe(table2, use_container_width=True, hide_index=True)

# if entreprise == "HMI":
#     st.markdown("### 🕐 Normal [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=19yMtXMhZd1EVtHXctcFAr2ilP3IiNTs&ll=33.48111573873554%2C-7.4896835&z=10)", unsafe_allow_html=True)
#     table_normal = prepare_shift_table(df_normal_site, "normal")
#     st.dataframe(table_normal, use_container_width=True, hide_index=True)

#     st.markdown("### 🕐 Shift 1 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1-VcA0vHT4PFN8RTvyYoDPypTF01zkc4&ll=33.625196155892226%2C-7.468961&z=12)", unsafe_allow_html=True)
#     table1 = prepare_shift_table(df_shift1_site, "shift 1")
#     st.dataframe(table1, use_container_width=True, hide_index=True)

#     st.markdown("### 🕐 Shift 2 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=1l7Fq0MjTwsa5JrMuda4SjaYJvl55zrE&ll=33.62434149775241%2C-7.442983499999993&z=12)", unsafe_allow_html=True)
#     table2 = prepare_shift_table(df_shift2_site, "shift 2")
#     st.dataframe(table2, use_container_width=True, hide_index=True)

#     st.markdown("### 🕐 Shift 3 [🗺](https://www.google.com/maps/d/edit?hl=fr&mid=11ebs_NXb-dgNQyG_51BMMYaMsn6UtWk&ll=33.6677255772706%2C-7.378471999999998&z=15)", unsafe_allow_html=True)
#     table3 = prepare_shift_table(df_shift3_site, "shift 3")
#     st.dataframe(table3, use_container_width=True, hide_index=True)

# if entreprise == "Steripharma":
#     st.markdown("### 🕐 Normal [🗺](https://www.google.com/maps/d/viewer?mid=LIEN_MYMAPS_NORMAL)", unsafe_allow_html=True)
#     table1 = prepare_shift_table(df_normal_site, "normal")
#     st.dataframe(table1, use_container_width=True, hide_index=True)

# --- Icône localisation (vert BLS). Mets fill="#FFD43B" si tu la veux jaune. ---
MAP_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22"
     viewBox="0 0 24 24" fill="#7CC043" style="vertical-align:-3px;">
  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5
           c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5
           s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
</svg>
"""

def shift_header(title: str, url: str):
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin:6px 0;'>
      <h3 style='margin:0;color:white;'>{title}</h3>
      <a href="{url}" target="_blank" style="text-decoration:none;">{MAP_ICON_SVG}</a>
    </div>
    """, unsafe_allow_html=True)


# =========================
# Tes blocs, avec l'icône :
# =========================


if entreprise == "HMI":
    shift_header("🕐 Normal", "https://www.google.com/maps/d/edit?mid=19yMtXMhZd1EVtHXctcFAr2ilP3IiNTs&usp=sharing")
    table_normal = prepare_shift_table(df_normal_site, "normal")
    st.dataframe(table_normal, use_container_width=True, hide_index=True)

    shift_header("🕐 Shift 1", "https://www.google.com/maps/d/edit?mid=1-VcA0vHT4PFN8RTvyYoDPypTF01zkc4&usp=sharing")
    table1 = prepare_shift_table(df_shift1_site, "shift 1")
    st.dataframe(table1, use_container_width=True, hide_index=True)

    shift_header("🕐 Shift 2", "https://www.google.com/maps/d/edit?mid=1l7Fq0MjTwsa5JrMuda4SjaYJvl55zrE&usp=sharing")
    table2 = prepare_shift_table(df_shift2_site, "shift 2")
    st.dataframe(table2, use_container_width=True, hide_index=True)

    shift_header("🕐 Shift 3", "https://www.google.com/maps/d/edit?mid=11ebs_NXb-dgNQyG_51BMMYaMsn6UtWk&usp=sharing")
    table3 = prepare_shift_table(df_shift3_site, "shift 3")
    st.dataframe(table3, use_container_width=True, hide_index=True)




st.divider()
st.info("⚠️ = durée supérieure à 1h30min")
