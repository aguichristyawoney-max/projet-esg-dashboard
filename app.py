import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Dashboard ESG Intégré", layout="wide")

@st.cache_data
def load_all_data():
    # Chargement des fichiers
    df_temp = pd.read_csv("changements_climatiques.csv")
    df_co2 = pd.read_csv("emission_deC02_annuel_par pays.csv")
    df_gender = pd.read_csv("ecart_salariales_hommes_vs_femmes.csv")
    df_ceo = pd.read_csv("ceo_salaires_vs_employés.csv")
    df_sea = pd.read_csv("hausse_du_niveau_desmers_par an.csv", sep=';')
    
    # Nettoyage
    df_temp = df_temp.rename(columns={"Change in global mean surface temperature caused by greenhouse gas emissions": "temp_change"})
    df_co2 = df_co2.rename(columns={"Annual CO₂ emissions": "co2"})
    
    try:
        df_gender = df_gender[['Zone de référence', 'Opération d\'agrégation', 'TIME_PERIOD', 'OBS_VALUE']]
    except:
        df_gender = df_gender.iloc[:, [0, 1, 4, 5]]
    df_gender.columns = ['Pays', 'Methode', 'Annee', 'Ecart']
    
    def clean_val(x): return float(str(x).replace('$', '').replace(',', '').strip())
    df_ceo['salary'] = df_ceo['salary'].apply(clean_val)
    df_ceo['pay_ratio_num'] = df_ceo['pay_ratio'].apply(lambda x: float(str(x).split(':')[0].replace(',', '')))
    df_ceo['industry'] = df_ceo['industry'].str.replace('%20', ' ')
    
    df_sea['Day'] = pd.to_datetime(df_sea['Day'], format='mixed', dayfirst=True)
    col_sea = "Average of Church and White (2011) and UHSLC"
    
    return df_temp, df_co2, df_gender, df_ceo, df_sea, col_sea

df_temp, df_co2, df_gender, df_ceo, df_sea, col_sea = load_all_data()

# --- BARRE LATÉRALE ---
st.sidebar.title("🌿 Dashboard ESG")
menu = st.sidebar.radio("Navigation", ["🌡️ Climat (Temp & CO2)", "🌊 Niveau des Mers", "⚖️ Social (Genre)", "🏛️ Gouvernance (CEO)"])

# --- 1. CLIMAT (TEMP & CO2) ---
if menu == "🌡️ Climat (Temp & CO2)":
    st.title("Analyse Environnementale : Top Pollueurs & Évolutions")
    
    # --- AJOUT DU CURSEUR PAR ANNÉE ---
    year_col = 'year' if 'year' in df_co2.columns else 'Year'
    min_year = int(df_co2[year_col].min())
    max_year = int(df_co2[year_col].max())
    
    st.subheader("📊 Classement Historique des Émetteurs")
    selected_year = st.slider("Sélectionner une année pour le Top 40", min_year, max_year, max_year)
    
    # Filtrage par année sélectionnée
    df_year = df_co2[df_co2[year_col] == selected_year].sort_values("co2", ascending=False).head(40)
    
    fig_top40 = px.bar(df_year, x="co2", y="Entity" if "Entity" in df_year.columns else "country", 
                       orientation='h', 
                       title=f"Top 40 des émetteurs de CO2 en {selected_year}",
                       labels={"co2": "Émissions (tonnes)", "Entity": "Pays/Région"},
                       color="co2", color_continuous_scale="Reds")
    fig_top40.update_layout(yaxis={'categoryorder':'total ascending'}, height=800)
    st.plotly_chart(fig_top40, use_container_width=True)

    st.markdown("---")

    # --- FOCUS PAR PAYS ---
    st.subheader("🔍 Analyse détaillée par pays (Historique complet)")
    pays = st.selectbox("Sélectionner un Pays pour voir son graphique temporel", sorted(df_temp['Entity'].unique()))
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Température : {pays}**")
        d_t = df_temp[df_temp['Entity'] == pays].sort_values("Year")
        if not d_t.empty:
            var_totale = d_t.iloc[-1]['temp_change'] - d_t.iloc[0]['temp_change']
            st.metric("Variation Totale", f"{var_totale:.2f} °C")
            fig_t = px.line(d_t, x="Year", y="temp_change", template="plotly_white")
            st.plotly_chart(fig_t, use_container_width=True)
        
    with col2:
        st.write(f"**Émissions CO2 : {pays}**")
        c_col = 'Entity' if 'Entity' in df_co2.columns else 'country'
        d_c = df_co2[df_co2[c_col] == pays].sort_values(year_col)
        if not d_c.empty:
            fig_c = px.line(d_c, x=year_col, y="co2", markers=True)
            st.plotly_chart(fig_c, use_container_width=True)

# --- 2. NIVEAU DES MERS ---
elif menu == "🌊 Niveau des Mers":
    st.title("Risque Physique : Élévation des océans")
    hausse_totale = df_sea[col_sea].iloc[-1] - df_sea[col_sea].iloc[0]
    st.metric("Élévation Totale (1880-2020)", f"{hausse_totale:.1f} mm")
    fig_sea = px.area(df_sea, x='Day', y=col_sea, color_discrete_sequence=['#0077be'])
    st.plotly_chart(fig_sea, use_container_width=True)

# --- 3. SOCIAL (GENRE) ---
elif menu == "⚖️ Social (Genre)":
    st.title("Inégalités Salariales Hommes / Femmes")
    pays_g = st.selectbox("Pays", sorted(df_gender['Pays'].unique()))
    meth = st.multiselect("Méthodes", df_gender['Methode'].unique(), default=df_gender['Methode'].unique()[0])
    
    d_g = df_gender[(df_gender['Pays'] == pays_g) & (df_gender['Methode'].isin(meth))]
    fig_g = px.line(d_g, x='Annee', y='Ecart', color='Methode', markers=True)
    fig_g.add_hline(y=0, line_dash="dash", line_color="green")
    st.plotly_chart(fig_g, use_container_width=True)

# --- 4. GOUVERNANCE (CEO) ---
else:
    st.title("Gouvernance : Ratios de Rémunération")
    secteur = st.selectbox("Secteur Industriel", sorted(df_ceo['industry'].unique()))
    top_n = st.slider("Nombre d'entreprises", 5, 20, 10)
    
    df_s = df_ceo[df_ceo['industry'] == secteur].sort_values('pay_ratio_num', ascending=False).head(top_n)
    fig_ceo = px.bar(df_s, x='pay_ratio_num', y='company_name', orientation='h', 
                     color='pay_ratio_num', color_continuous_scale='Reds',
                     hover_data=['ceo_name', 'salary'])
    fig_ceo.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_ceo, use_container_width=True)
