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
            df["Plataforma"] = df["Plataforma"].astype(str).str.strip()
            df = df[df["Tipo"] == "in"]

            # Identificar HL y WAGGER por Plataforma
            hl_fuente = "hl_casinofenix"
            salas_wagger = {
                "Fenix_Wagger100", "Fenix_Wagger40", "Fenix_Wagger30",
                "Fenix_Wagger50", "Fenix_Wagger150", "Fenix_Wagger200"
            }
            df["Fuente"] = df["Plataforma"].apply(lambda x: "HL" if x == hl_fuente else ("WAGGER" if x in salas_wagger else "OTRO"))

            # Crear resumen consolidado HL + WAGGER
            cargas_hl = df[df["Fuente"] == "HL"].groupby("Jugador")["Monto"].sum().rename("HL")
            cargas_wagger = df[df["Fuente"] == "WAGGER"].groupby("Jugador")["Monto"].sum().rename("WAGGER")
            cantidad_cargas = df[df["Fuente"].isin(["HL", "WAGGER"])].groupby("Jugador")["Monto"].count().rename("Cantidad_Cargas")
            ultima_carga = df[df["Fuente"].isin(["HL", "WAGGER"])].groupby("Jugador")["Fecha"].max().rename("Última_Carga")
            ultima_carga = pd.to_datetime(ultima_carga, errors="coerce")
            dias_sin_cargar = (pd.Timestamp.now() - ultima_carga).dt.days.rename("Días_sin_cargar")

            df_resumen = pd.concat([cargas_hl, cargas_wagger, cantidad_cargas, ultima_carga, dias_sin_cargar], axis=1).fillna(0)
            df_resumen["HL"] = df_resumen["HL"].astype(float)
            df_resumen["WAGGER"] = df_resumen["WAGGER"].astype(float)
            df_resumen["Cantidad_Cargas"] = df_resumen["Cantidad_Cargas"].astype(int)

            st.subheader("\U0001F4CA Resumen Consolidado HL + WAGGER")
            st.dataframe(df_resumen)

            # --- Base para funcionalidades VIP ---
            st.subheader("\U0001F4E5 Lista de jugadores VIP actual")
            lista_vips = st.text_area("Pegá los nombres de jugadores VIP (uno por línea):", height=200)
            vips_actuales = [nombre.strip().lower() for nombre in lista_vips.split("\n") if nombre.strip() != ""]

            vip_resumen = df_resumen.reset_index()
            vip_resumen["Jugador_normalizado"] = vip_resumen["Jugador"].str.lower()
            vip_df = vip_resumen[vip_resumen["Jugador_normalizado"].isin(vips_actuales)]

            dias_filtro = st.slider("Mostrar VIPs con más de X días sin cargar", 0, 30, 7)
            vip_filtrados = vip_df[vip_df["Días_sin_cargar"] >= dias_filtro]
            st.subheader("\U0001F4CB Actividad de Jugadores VIP")
            st.dataframe(vip_filtrados)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                vip_filtrados.to_excel(writer, index=False)
            st.download_button("\U0001F4E4 Descargar VIPs inactivos", output.getvalue(), file_name="vips_inactivos.xlsx")

            # --- 4. Posibles nuevos VIPs ---
            st.subheader("\U0001F195 Posibles nuevos VIPs (no registrados)")
            df_no_vip = vip_resumen[~vip_resumen["Jugador_normalizado"].isin(vips_actuales)]
            posibles_vips = df_no_vip[(df_no_vip["HL"] + df_no_vip["WAGGER"] > 10000) | (df_no_vip["Cantidad_Cargas"] >= 5)]
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
            jugador_input = st.selectbox("Seleccioná un jugador para simular", df_resumen.index)
            if jugador_input in df_resumen.index:
                monto_total = df_resumen.loc[jugador_input, "HL"] + df_resumen.loc[jugador_input, "WAGGER"]
                bonus_simulado = monto_total * 1.5
                st.info(f"Si {jugador_input} fuera VIP con 150% de bono, recibiría aproximadamente: **${bonus_simulado:,.0f}**")

            # --- 7. Registro manual de contacto ---
            st.subheader("\U0001F4D2 Registro de contacto (manual)")
            jugador_contactado = st.selectbox("Seleccioná un jugador VIP contactado", vip_df["Jugador"].unique())
            fue_contactado = st.checkbox("\u2705 Fue contactado")
            observacion = st.text_area("\U0001F5D2\uFE0F Observaciones (respuesta, bono ofrecido, etc.)")

            if st.button("\U0001F4BE Guardar registro de contacto"):
                st.success(f"Registro guardado para {jugador_contactado}: Contactado = {fue_contactado}, Observación = {observacion}"), file_name="vips_inactivos.xlsx")

