import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import datetime

st.set_page_config(page_title="VIPS", layout="wide")
st.markdown("<h1 style='text-align: center; color:#F44336;'>Player Metrics</h1>", unsafe_allow_html=True)

seccion = st.sidebar.radio("Seleccioná una sección:", ["\U0001F451 Comunidad VIP"])

# --- FUNCIONES ---
def preparar_dataframe(df):
    df = df.rename(columns={
        "operación": "Tipo",
        "Depositar": "Monto",
        "Retirar": "Retiro",
        "Wager": "?2",
        "Límites": "?3",
        "Balance antes de operación": "Saldo",
        "Fecha": "Fecha",
        "Tiempo": "Hora",
        "Iniciador": "UsuarioSistema",
        "Del usuario": "Plataforma",
        "Sistema": "Admin",
        "Al usuario": "Jugador",
        "IP": "Extra"
    })
    return df

if seccion == "\U0001F451 Comunidad VIP":
    st.header("\U0001F451 Comunidad VIP - Gestión y Expansión")

    archivo = st.file_uploader("\U0001F4C1 Subí tu archivo de cargas recientes:", type=["xlsx", "xls", "csv"], key="vip_exp")
    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)

        if df is not None:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
            df["Jugador"] = df["Jugador"].astype(str).str.strip()
            df["Jugador_normalizado"] = df["Jugador"].str.lower()

            # --- 1. Cargar lista de VIPs desde text_area ---
            st.subheader("\U0001F4E5 Lista de jugadores VIP actual")
            lista_vips = st.text_area("Pegá los nombres de jugadores VIP (uno por línea):", height=200)
            vips_actuales = [nombre.strip().lower() for nombre in lista_vips.split("\n") if nombre.strip() != ""]

            # --- 2. Actividad de jugadores VIP ---
            vip_df = df[df["Jugador_normalizado"].isin(vips_actuales)]
            resumen_vips = (
                vip_df.groupby("Jugador")
                .agg(Monto_Total=("Monto", "sum"),
                     Cantidad_Cargas=("Jugador", "count"),
                     Última_Carga=("Fecha", "max"))
                .reset_index()
            )
            resumen_vips["Días_sin_cargar"] = (pd.Timestamp.now() - resumen_vips["Última_Carga"]).dt.days

            st.subheader("\U0001F4CB Actividad de Jugadores VIP")
            dias_filtro = st.slider("Mostrar VIPs con más de X días sin cargar", 0, 30, 7)
            vip_filtrados = resumen_vips[resumen_vips["Días_sin_cargar"] >= dias_filtro]
            st.dataframe(vip_filtrados)

            # --- 3. Exportar para remarketing ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                vip_filtrados.to_excel(writer, index=False)
            st.download_button("\U0001F4E4 Descargar VIPs inactivos", output.getvalue(), file_name="vips_inactivos.xlsx")

            # --- 4. Posibles nuevos VIPs ---
            st.subheader("\U0001F195 Posibles nuevos VIPs (no registrados)")
            df_no_vip = df[~df["Jugador_normalizado"].isin(vips_actuales)]
            posibles_vips = (
                df_no_vip.groupby("Jugador")
                .agg(Monto_Total=("Monto", "sum"),
                     Cantidad_Cargas=("Jugador", "count"),
                     Última_Carga=("Fecha", "max"))
                .reset_index()
            )
            posibles_vips = posibles_vips[
                (posibles_vips["Monto_Total"] > 10000) |
                (posibles_vips["Cantidad_Cargas"] >= 5)
            ]
            posibles_vips["Días_sin_cargar"] = (pd.Timestamp.now() - posibles_vips["Última_Carga"]).dt.days
            st.dataframe(posibles_vips)

            # --- 5. Simulación crecimiento mensual ---
            st.subheader("\U0001F4C8 Simulación de Crecimiento Mensual de VIPs")
            fecha_simulada = st.date_input("Fecha simulada de ingreso de estos posibles VIPs", pd.Timestamp.today())
            posibles_vips["Fecha_Ingreso"] = pd.to_datetime(fecha_simulada)
            posibles_vips["Mes"] = posibles_vips["Fecha_Ingreso"].dt.to_period("M")
            crecimiento = posibles_vips.groupby("Mes").size().reset_index(name="Nuevos_VIPs")
            crecimiento["Mes"] = crecimiento["Mes"].astype(str)
            if not crecimiento.empty:
                graf_vip = px.bar(crecimiento, x="Mes", y="Nuevos_VIPs", title="Crecimiento estimado de la comunidad VIP")
                st.plotly_chart(graf_vip, use_container_width=True)

            # --- 6. Simulador de recompensa ---
            st.subheader("\U0001F381 Simulador de Recompensa VIP")
            jugador_input = st.selectbox("Seleccioná un jugador para simular", df["Jugador"].unique())
            monto_total = df[df["Jugador"] == jugador_input]["Monto"].sum()
            bonus_simulado = monto_total * 1.5
            st.info(f"Si {jugador_input} fuera VIP con 150% de bono, recibiría aproximadamente: **${bonus_simulado:,.0f}**")

            # --- 7. Registro manual de contacto ---
            st.subheader("\U0001F4D2 Registro de contacto (manual)")
            jugador_contactado = st.selectbox("Seleccioná un jugador VIP contactado", resumen_vips["Jugador"].unique())
            fue_contactado = st.checkbox("\u2705 Fue contactado")
            observacion = st.text_area("\U0001F5D2\uFE0F Observaciones (respuesta, bono ofrecido, etc.)")

            if st.button("\U0001F4BE Guardar registro de contacto"):
                st.success(f"Registro guardado para {jugador_contactado}: Contactado = {fue_contactado}, Observación = {observacion}")
                # En futuro: guardar en Google Sheets o base de datos
