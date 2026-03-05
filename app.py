import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Dashboard ESG Intégré", layout="wide")

# --- CHARGEMENT ET NETTOYAGE DES DONNÉES ---
@st.cache_data
def load_all_data():
    # 1. Température
    df_temp = pd.read_csv(r"C:\Users\aguic\Downloads\dataset\changements_climatiques.csv")
    df_temp = df_temp.rename(columns={"Change in global mean surface temperature caused by greenhouse gas emissions": "temp_change"})
    df_temp = df_temp[df_temp["Code"].notna()]

    # 2. CO2
    df_co2 = pd.read_csv(r"C:\Users\aguic\Downloads\dataset\emission_deC02_annuel_par pays.csv")
    df_co2 = df_co2.rename(columns={"Annual CO₂ emissions": "co2"})
    df_co2 = df_co2[df_co2["Code"].notna()].copy()

    # 3. Écart Salarial H/F
    df_gender = pd.read_csv(r"C:\Users\aguic\Downloads\dataset\ecart_salariales_hommes_vs_femmes.csv")
    try:
        df_gender = df_gender[['Zone de référence', 'Opération d\'agrégation', 'TIME_PERIOD', 'OBS_VALUE']]
    except:
        df_gender = df_gender.iloc[:, [0, 1, 4, 5]] # Backup si noms diffèrent
    df_gender.columns = ['Pays', 'Methode', 'Annee', 'Ecart']
    df_gender = df_gender.dropna(subset=['Ecart'])

    # 4. CEO Pay
    df_ceo = pd.read_csv(r"C:\Users\aguic\Downloads\dataset\ceo_salaires_vs_employés.csv")
    def clean_val(x): return float(str(x).replace('$', '').replace(',', '').strip())
    df_ceo['salary'] = df_ceo['salary'].apply(clean_val)
    df_ceo['pay_ratio_num'] = df_ceo['pay_ratio'].apply(lambda x: float(str(x).split(':')[0].replace(',', '')))
    df_ceo['industry'] = df_ceo['industry'].str.replace('%20', ' ')

    # 5. Niveau des mers
    df_sea = pd.read_csv(r"C:\Users\aguic\Downloads\dataset\hausse_du_niveau_desmers_par an.csv", sep=';')
    df_sea['Day'] = pd.to_datetime(df_sea['Day'], format='mixed', dayfirst=True)
    col_sea = "Average of Church and White (2011) and UHSLC"
    
    return df_temp, df_co2, df_gender, df_ceo, df_sea, col_sea

df_temp, df_co2, df_gender, df_ceo, df_sea, col_sea = load_all_data()

# --- BARRE LATÉRALE ---
st.sidebar.title("🌿 Dashboard ESG")
menu = st.sidebar.radio("Navigation", ["🌍 Climat (Temp & CO2)", "🌊 Risque Physique (Mers)", "⚖️ Social (Genre)", "🏛️ Gouvernance (CEO)"])

# --- PAGE 1 : CLIMAT (TEMP & CO2) ---
if menu == "🌍 Climat (Temp & CO2)":
    st.title("Analyse Environnementale : Température & CO2")
    
    pays = st.selectbox("Sélectionner un Pays", sorted(df_temp['Entity'].unique()), index=0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Température : {pays}")
        d_t = df_temp[df_temp['Entity'] == pays]
        fig_t = px.line(d_t, x="Year", y="temp_change", title="Variation (°C)")
        st.plotly_chart(fig_t, use_container_width=True)
        
    with col2:
        st.subheader(f"Émissions CO2 : {pays}")
        d_c = df_co2[df_co2['Entity'] == pays] if 'Entity' in df_co2.columns else df_co2[df_co2['country'] == pays]
        fig_c = px.line(d_c, x="year" if "year" in d_c.columns else "Year", y="co2", title="Émissions annuelles")
        st.plotly_chart(fig_c, use_container_width=True)

# --- PAGE 2 : NIVEAU DES MERS ---
elif menu == "🌊 Risque Physique (Mers)":
    st.title("Risque Physique : Élévation du niveau des mers")
    
    hausse_totale = df_sea[col_sea].iloc[-1] - df_sea[col_sea].iloc[0]
    
    c1, c2 = st.columns(2)
    c1.metric("Élévation Totale", f"{hausse_totale:.1f} mm")
    c2.metric("Tendance", "Accélération mesurée", delta="Positive")
    
    fig_sea = px.area(df_sea, x='Day', y=col_sea, title="Niveau moyen global des mers (1880-2020)")
    st.plotly_chart(fig_sea, use_container_width=True)

# --- PAGE 3 : SOCIAL (GENDER GAP) ---
elif menu == "⚖️ Social (Genre)":
    st.title("Inégalités Salariales Hommes / Femmes")
    
    pays_g = st.selectbox("Pays", sorted(df_gender['Pays'].unique()))
    meth = st.multiselect("Méthodes", df_gender['Methode'].unique(), default=['Médiane'])
    
    df_g_filtered = df_gender[(df_gender['Pays'] == pays_g) & (df_gender['Methode'].isin(meth))]
    fig_g = px.line(df_g_filtered, x='Annee', y='Ecart', color='Methode', markers=True)
    fig_g.add_hline(y=0, line_dash="dash", line_color="green")
    st.plotly_chart(fig_g, use_container_width=True)

# --- PAGE 4 : GOUVERNANCE (CEO) ---
else:
    st.title("Gouvernance : Rémunération des Dirigeants")
    
    secteur = st.selectbox("Secteur", sorted(df_ceo['industry'].unique()))
    df_s = df_ceo[df_ceo['industry'] == secteur].sort_values('pay_ratio_num', ascending=False).head(15)
    
    fig_ceo = px.bar(df_s, x='pay_ratio_num', y='company_name', orientation='h', 
                     color='pay_ratio_num', color_continuous_scale='Reds',
                     title=f"Ratios CEO/Employés dans le secteur {secteur}")
    st.plotly_chart(fig_ceo, use_container_width=True)