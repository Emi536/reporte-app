import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import datetime

st.set_page_config(page_title="VIPS", layout="wide")
st.markdown("<h1 style='text-align: center; color:#F44336;'>Player Metrics</h1>", unsafe_allow_html=True)


seccion = st.sidebar.radio("Seleccioná una sección:", ["👑 Comunidad VIP"])

def preparar_dataframe(df):
    df = df.rename(columns={
        "operación": "Tipo",
        "Depositar": "Monto",
        "Retirar": "Retiro",
        "Wager": "?2",
        "Límites": "?3",
        "Balance antes de operación": "Balance_Inicial",
        "Jugador": "Jugador",
        "Fecha": "Fecha",
        "Hora": "Hora",
    })
    return df

# --- SECCIÓN: COMUNIDAD VIP ---
elif seccion == "👑 Comunidad VIP":
    st.header("👑 Comunidad VIP - Seguimiento de Jugadores Premium")

    archivo = st.file_uploader("📁 Subí tu archivo de cargas recientes:", type=["xlsx", "xls", "csv"], key="vip")
    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)

        if df is not None:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
            df["Días sin cargar"] = (pd.Timestamp.now() - df["Fecha"]).dt.days
            df["Última fecha"] = df.groupby("Jugador")["Fecha"].transform("max")

            df_vip = (
                df[df["Tipo"] == "in"]
                .groupby("Jugador")
                .agg({
                    "Monto": "sum",
                    "Fecha": ["count", "max"]
                })
            )
            df_vip.columns = ["Monto_Total", "Cantidad_Cargas", "Última_Carga"]
            df_vip = df_vip.reset_index()
            df_vip["Días_sin_cargar"] = (pd.Timestamp.now() - df_vip["Última_Carga"]).dt.days

            def calcular_nivel_vip(monto, cantidad):
                if monto > 100000 and cantidad > 15:
                    return "VIP Diamante"
                elif monto > 50000:
                    return "VIP Oro"
                elif monto > 20000:
                    return "VIP Plata"
                else:
                    return "Regular"

            df_vip["Nivel_VIP"] = df_vip.apply(lambda row: calcular_nivel_vip(row["Monto_Total"], row["Cantidad_Cargas"]), axis=1)

            nivel_filtro = st.selectbox("🔍 Filtrar por Nivel VIP", ["Todos"] + sorted(df_vip["Nivel_VIP"].unique().tolist()))
            if nivel_filtro != "Todos":
                df_vip = df_vip[df_vip["Nivel_VIP"] == nivel_filtro]

            dias_inactivos = st.slider("📆 Mostrar jugadores con más de X días sin cargar:", 0, 60, 7)
            df_filtrado = df_vip[df_vip["Días_sin_cargar"] >= dias_inactivos]

            st.subheader("📋 Jugadores VIP inactivos")
            st.dataframe(df_filtrado)

            # --- Descargar Excel ---
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_filtrado.to_excel(writer, sheet_name="VIP Inactivos", index=False)
                st.download_button("📤 Descargar lista de VIPs inactivos", output.getvalue(), file_name="VIP_inactivos.xlsx")
            except Exception as e:
                st.error(f"Error al generar archivo: {e}")
        else:
            st.error("❌ El archivo no tiene el formato esperado.")
