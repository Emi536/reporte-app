import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import datetime

st.set_page_config(page_title="VIPS", layout="wide")
st.markdown("<h1 style='text-align: center; color:#F44336;'>Player Metrics</h1>", unsafe_allow_html=True)


seccion = st.sidebar.radio("Seleccioná una sección:", ["👑 Comunidad VIP"])

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

if seccion == "👑 Comunidad VIP":
    st.header("👑 Comunidad VIP - Gestión y Expansión")

    archivo = st.file_uploader("📁 Subí tu archivo de cargas recientes:", type=["xlsx", "xls", "csv"], key="vip_exp")
    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)

        if df is not None:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
            df["Jugador"] = df["Jugador"].astype(str).str.strip()
            df["Días sin cargar"] = (pd.Timestamp.now() - df["Fecha"]).dt.days

            # --- 1. Cargar lista de VIPs desde archivo adicional o lista integrada ---
            st.subheader("📥 Lista de jugadores VIP actual")
            lista_vips = st.text_area("Pegá los nombres de jugadores VIP (uno por línea):", height=200)
            vips_actuales = [nombre.strip().lower() for nombre in lista_vips.split("\n") if nombre.strip() != ""]

            df["Jugador_normalizado"] = df["Jugador"].str.lower()

            # --- 2. Tabla de jugadores VIP actuales (para controlar actividad e inactividad) ---
            vip_df = df[df["Jugador_normalizado"].isin(vips_actuales)]
            resumen_vips = (
                vip_df.groupby("Jugador")
                .agg(Monto_Total=("Monto", "sum"),
                     Cantidad_Cargas=("Jugador", "count"),
                     Última_Carga=("Fecha", "max"))
                .reset_index()
            )
            resumen_vips["Días_sin_cargar"] = (pd.Timestamp.now() - resumen_vips["Última_Carga"]).dt.days

            st.subheader("📋 Actividad de Jugadores VIP")
            dias_filtro = st.slider("Mostrar VIPs con más de X días sin cargar", 0, 30, 7)
            vip_filtrados = resumen_vips[resumen_vips["Días_sin_cargar"] >= dias_filtro]
            st.dataframe(vip_filtrados)

            # --- 3. Exportar para remarketing ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                vip_filtrados.to_excel(writer, index=False)
            st.download_button("📤 Descargar VIPs inactivos", output.getvalue(), file_name="vips_inactivos.xlsx")

            # --- 4. Detectar nuevos posibles VIPs ---
            st.subheader("🆕 Posibles nuevos VIPs (no registrados)")
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

            # --- 5. Visualización de crecimiento mensual de VIPs (si tenés fechas de ingreso) ---
            # Esto es opcional: si tenés una columna con "Fecha_Ingreso_VIP"
            # podés graficar cómo crece la comunidad VIP
            st.subheader("📈 Simulación de Crecimiento Mensual de VIPs (manual)")
            fecha_simulada = st.date_input("Fecha simulada de ingreso de nuevos VIPs", pd.Timestamp.today())
            posibles_vips["Fecha_Ingreso"] = fecha_simulada
            posibles_vips["Mes"] = posibles_vips["Fecha_Ingreso"].dt.to_period("M")
            crecimiento = posibles_vips.groupby("Mes").size().reset_index(name="Nuevos_VIPs")
            if not crecimiento.empty:
                graf_vip = px.bar(crecimiento, x="Mes", y="Nuevos_VIPs", title="Crecimiento estimado de la comunidad VIP")
                st.plotly_chart(graf_vip, use_container_width=True)

            # --- 6. Simulador de Recompensa VIP ---
            st.subheader("🎁 Simulador de Recompensa VIP")
            jugador_input = st.selectbox("Seleccioná un jugador para simular", df["Jugador"].unique())
            monto_total = df[df["Jugador"] == jugador_input]["Monto"].sum()
            bonus_simulado = monto_total * 1.5
            st.info(f"Si {jugador_input} fuera VIP con 150% de bono, recibiría aproximadamente: **${bonus_simulado:,.0f}**")

            # --- 7. Sistema de contacto manual y observaciones (en preparación) ---
            st.subheader("📒 Registro de contacto (manual)")
            jugador_contactado = st.selectbox("Seleccioná un jugador VIP contactado", resumen_vips["Jugador"].unique())
            fue_contactado = st.checkbox("✅ Fue contactado")
            observacion = st.text_area("🗒️ Observaciones (respuesta, bono ofrecido, etc.)")

            if st.button("💾 Guardar registro de contacto"):
                st.success(f"Registro guardado para {jugador_contactado}: Contactado = {fue_contactado}, Observación = {observacion}")
                # En futuro: se puede conectar con Google Sheets o guardar localmente

