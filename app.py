import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import datetime

st.set_page_config(page_title="VIPS", layout="wide")
st.markdown("<h1 style='text-align: center; color:#F44336;'>Player Metrics</h1>", unsafe_allow_html=True)

seccion = st.sidebar.radio("Seleccioná una sección:", ["👑 Comunidad VIP", "🎰 Comunidad VIP - Eros"])

# --- FUNCIONES ---
def preparar_dataframe(df):
    df.columns = df.columns.str.strip().str.lower()  # normalizar columnas
    df = df.rename(columns={
        "operación": "Tipo",
        "depositar": "Monto",
        "retirar": "Retiro",
        "wager": "?2",
        "límites": "?3",
        "balance antes de operación": "Saldo",
        "fecha": "Fecha",
        "Tiempo": "Hora",
        "iniciador": "UsuarioSistema",
        "del usuario": "Plataforma",
        "sistema": "Admin",
        "al usuario": "Jugador",
        "ip": "Extra"
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
            df["Hora"] = pd.to_datetime(df["Hora"], errors="coerce").dt.time
            df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
            df["Jugador"] = df["Jugador"].astype(str).str.strip()
            df["Jugador_normalizado"] = df["Jugador"].str.lower()
            df["Plataforma"] = df["Plataforma"].astype(str).str.strip()
            df = df[df["Tipo"] == "in"]

            hl_fuente = "hl_casinofenix"
            salas_wagger = {
                "Fenix_Wagger100", "Fenix_Wagger40", "Fenix_Wagger30",
                "Fenix_Wagger50", "Fenix_Wagger150", "Fenix_Wagger200"
            }
            df["Fuente"] = df["Plataforma"].apply(lambda x: "HL" if x == hl_fuente else ("WAGGER" if x in salas_wagger else "OTRO"))

            cargas_hl = df[df["Fuente"] == "HL"].groupby("Jugador")["Monto"].sum().rename("HL")
            cargas_wagger = df[df["Fuente"] == "WAGGER"].groupby("Jugador")["Monto"].sum().rename("WAGGER")
            cantidad_cargas = df[df["Fuente"].isin(["HL", "WAGGER"])].groupby("Jugador")["Monto"].count().rename("Cantidad_Cargas")
            ultima_carga = df[df["Fuente"].isin(["HL", "WAGGER"])].groupby("Jugador")["Fecha"].max().rename("Última_Carga")
            dias_sin_cargar = (pd.Timestamp.now() - ultima_carga).dt.days.rename("Días_sin_cargar")

            df_resumen = pd.concat([cargas_hl, cargas_wagger, cantidad_cargas, ultima_carga, dias_sin_cargar], axis=1).fillna(0)
            df_resumen["HL"] = df_resumen["HL"].astype(float)
            df_resumen["WAGGER"] = df_resumen["WAGGER"].astype(float)
            df_resumen["Cantidad_Cargas"] = df_resumen["Cantidad_Cargas"].astype(int)

            st.subheader("📊 Resumen Consolidado HL + WAGGER")
            st.dataframe(df_resumen)

            st.subheader("📥 Lista de jugadores VIP actual")
            lista_vips = st.text_area("Pegá los nombres de jugadores VIP (uno por línea):", height=200)
            vips_actuales = [nombre.strip().lower() for nombre in lista_vips.split("\n") if nombre.strip() != ""]

            vip_resumen = df_resumen.reset_index()
            vip_resumen["Jugador_normalizado"] = vip_resumen["Jugador"].str.lower()
            vip_df = vip_resumen[vip_resumen["Jugador_normalizado"].isin(vips_actuales)]

            dias_filtro = st.slider("Mostrar VIPs con más de X días sin cargar", 0, 30, 7)
            vip_filtrados = vip_df[vip_df["Días_sin_cargar"] >= dias_filtro]
            st.subheader("📋 Actividad de Jugadores VIP")
            st.dataframe(vip_filtrados)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                vip_filtrados.to_excel(writer, index=False)
            st.download_button("📤 Descargar VIPs inactivos", output.getvalue(), file_name="vips_inactivos.xlsx")

            st.subheader("🆕 Posibles nuevos VIPs (no registrados)")
            df_no_vip = vip_resumen[~vip_resumen["Jugador_normalizado"].isin(vips_actuales)]
            posibles_vips = df_no_vip[(df_no_vip["HL"] + df_no_vip["WAGGER"] > 10000) | (df_no_vip["Cantidad_Cargas"] >= 5)]
            st.dataframe(posibles_vips)

            # --- Análisis de franja horaria VIPs ---
            st.subheader("⏰ Segmentación horaria de jugadores VIP")
            st.caption("🕒 Madrugada (00–06), Mañana (06–12), Tarde (12–18), Noche (18–24)")

            df_vips_full = df[df["Jugador_normalizado"].isin(vips_actuales)].copy()
            df_vips_full["HoraReal"] = pd.to_datetime(df_vips_full["Hora"].astype(str), format="%H:%M:%S", errors="coerce")
            df_vips_full["HoraEntera"] = df_vips_full["HoraReal"].dt.hour
            df_vips_full = df_vips_full.dropna(subset=["HoraEntera"])

            def clasificar_franja(h):
                if 0 <= h < 6:
                    return "Madrugada"
                elif 6 <= h < 12:
                    return "Mañana"
                elif 12 <= h < 18:
                    return "Tarde"
                else:
                    return "Noche"

            df_vips_full["Franja"] = df_vips_full["HoraEntera"].apply(clasificar_franja)

            franja_dominante = (
                df_vips_full.groupby(["Jugador", "Franja"]).size()
                .reset_index(name="Cargas")
                .sort_values(by=["Jugador", "Cargas"], ascending=[True, False])
                .drop_duplicates("Jugador")
            )

            hora_frecuente = (
                df_vips_full.groupby(["Jugador", "HoraEntera"]).size()
                .reset_index(name="Frecuencia")
                .sort_values(by=["Jugador", "Frecuencia"], ascending=[True, False])
                .drop_duplicates("Jugador")
            )
            hora_frecuente["Hora"] = hora_frecuente["HoraEntera"].astype(int).astype(str).str.zfill(2) + ":00"

            patron_horario = franja_dominante.merge(hora_frecuente[["Jugador", "Hora"]], on="Jugador")
            patron_horario.rename(columns={"Hora": "Hora_Más_Frecuente"}, inplace=True)

            st.subheader("📋 Comportamiento Horario de VIPs")
            st.dataframe(patron_horario)

            st.subheader("📊 VIPs agrupados por franja horaria")
            tabla_franjas = patron_horario.groupby("Franja").agg({
                "Jugador": list,
                "Jugador": "count"
            }).rename(columns={"Jugador": "Total_VIPs"}).reset_index()

            tabla_franjas["Jugadores con hora pico"] = tabla_franjas["Franja"].apply(lambda fr: ", ".join([
                f"{row['Jugador']} ({row['Hora_Más_Frecuente']})"
                for _, row in patron_horario[patron_horario["Franja"] == fr].iterrows()
            ]))

            st.dataframe(tabla_franjas[["Franja", "Total_VIPs", "Jugadores con hora pico"]])


elif seccion == "🎰 Comunidad VIP - Eros":
    st.header("🎰 Comunidad VIP - Eros")

    archivo_eros = st.file_uploader("📁 Subí el archivo de cargas de Eros:", type=["xlsx", "xls", "csv"], key="vip_eros")
    if archivo_eros:
        df = pd.read_excel(archivo_eros) if archivo_eros.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo_eros)
        df = preparar_dataframe(df)

        if df is not None:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce").fillna(0)
            df["Jugador"] = df["Jugador"].astype(str).str.strip()
            df["Jugador_normalizado"] = df["Jugador"].str.lower()
            df["Plataforma"] = df["Plataforma"].astype(str).str.strip()
            df = df[df["Tipo"] == "in"]

            hl_eros = "hl_Erosonline"
            salas_eros = {
                "Eros_wagger30%", "Eros_wagger40%", "Eros_wagger50%",
                "Eros_wagger100%", "Eros_wagger150%", "Eros_wagger200%"
            }
            df["Fuente"] = df["Plataforma"].apply(lambda x: "HL" if x == hl_eros else ("WAGGER" if x in salas_eros else "OTRO"))

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

            st.subheader("📊 Resumen Consolidado HL + WAGGER - Eros")
            st.dataframe(df_resumen)

            st.subheader("📥 Lista de jugadores VIP de Eros")
            lista_vips = st.text_area("Pegá los nombres de jugadores VIP (uno por línea):", height=200, key="vip_list_eros")
            vips_actuales = [nombre.strip().lower() for nombre in lista_vips.split("\n") if nombre.strip() != ""]

            vip_resumen = df_resumen.reset_index()
            vip_resumen["Jugador_normalizado"] = vip_resumen["Jugador"].str.lower()
            vip_df = vip_resumen[vip_resumen["Jugador_normalizado"].isin(vips_actuales)]

            dias_filtro = st.slider("Mostrar VIPs con más de X días sin cargar", 0, 30, 7, key="eros_dias")
            vip_filtrados = vip_df[vip_df["Días_sin_cargar"] >= dias_filtro]
            st.subheader("📋 Actividad de Jugadores VIP - Eros")
            st.dataframe(vip_filtrados)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                vip_filtrados.to_excel(writer, index=False)
            st.download_button("📤 Descargar VIPs inactivos (Eros)", output.getvalue(), file_name="vips_inactivos_eros.xlsx")

            st.subheader("🆕 Posibles nuevos VIPs (Eros)")
            df_no_vip = vip_resumen[~vip_resumen["Jugador_normalizado"].isin(vips_actuales)]
            posibles_vips = df_no_vip[(df_no_vip["HL"] + df_no_vip["WAGGER"] > 10000) | (df_no_vip["Cantidad_Cargas"] >= 5)]
            st.dataframe(posibles_vips)
