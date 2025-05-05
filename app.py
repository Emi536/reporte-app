import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Análisis VIP", layout="wide")
st.title("🌻 Análisis Diario de Actividad VIP")

# --- CONEXIÓN A GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
gc = gspread.authorize(credentials)
sh = gc.open("seguimiento_vip")

# --- HOJAS ---
hoja_vips = sh.worksheet("vip_list")
hoja_bonos = sh.worksheet("bonos_ofrecidos")
hoja_actividad = sh.worksheet("actividad_diaria_vip")

# --- FUNCIONES ---
def cargar_data():
    vip_list = pd.DataFrame(hoja_vips.get_all_records())
    bonos = pd.DataFrame(hoja_bonos.get_all_records())
    return vip_list, bonos

def analizar_participacion(df_reporte, vip_list, bonos):
    df_reporte['Fecha'] = pd.to_datetime(df_reporte['Fecha'], errors='coerce')
    df_reporte['Hora'] = pd.to_datetime(df_reporte['Tiempo'], format="%H:%M:%S", errors='coerce').dt.hour
    df_reporte['Depositar'] = pd.to_numeric(df_reporte['Depositar'], errors='coerce').fillna(0)
    df_reporte = df_reporte.dropna(subset=['Fecha', 'Hora'])

    resultados = []
    df_reporte.sort_values(by=['Al usuario', 'Fecha', 'Hora'], inplace=True)

    for _, row in df_reporte.iterrows():
        usuario = row['Al usuario']
        del_usuario = row['Del usuario']
        hora = row['Hora']
        monto = row['Depositar']
        fecha = row['Fecha'].date()

        if "Fenix" in del_usuario:
            comunidad = "Fenix"
        elif "Eros" in del_usuario:
            comunidad = "Eros"
        else:
            comunidad = ""

        bonos_del_dia = bonos[(bonos['Fecha'] == fecha.strftime("%d/%m/%Y")) & (bonos['Comunidad'].str.lower() == comunidad.lower())]
        participo = False
        bono_usado = ""

        for _, b in bonos_del_dia.iterrows():
            try:
                h_ini = int(str(b['Hora inicio']).split(":")[0].strip())
                h_fin = int(str(b['Hora fin']).split(":")[0].strip())
            except:
                continue

            try:
                min_carga = int(str(b['Mínimo carga']).strip()) if b['Mínimo carga'] else 0
            except:
                min_carga = 0

            try:
                min_mejorado = int(str(b['Mínimo mejorado']).strip()) if b['Mínimo mejorado'] else None
            except:
                min_mejorado = None

            bono_tipo = str(b.get('Tipo bono', '')).lower()

            if h_ini <= hora <= h_fin:
                if bono_tipo == "primera carga":
                    if min_mejorado and monto >= min_mejorado:
                        participo = True
                        bono_usado = f"{b['Bono % mejorado']} ({comunidad})"
                    elif monto >= min_carga:
                        participo = True
                        bono_usado = f"{b['Bono % base']} ({comunidad})"
                else:
                    if monto >= min_carga:
                        participo = True
                        bono_usado = f"{b['Bono % base']} ({comunidad})"

        resultados.append({
            "Fecha": fecha,
            "Usuario": usuario,
            "Monto": monto,
            "Hora": hora,
            "Bono Usado": bono_usado if participo else "No",
            "Participó": "✅" if participo else "❌"
        })

    return pd.DataFrame(resultados)

# --- UI: SUBIDA DE REPORTE ---
archivo = st.file_uploader("📁 Subí el reporte diario del casino", type=["csv", "xlsx"])

if archivo:
    df_reporte = pd.read_excel(archivo) if archivo.name.endswith(".xlsx") else pd.read_csv(archivo)
    vip_list, bonos = cargar_data()
    df_resultado = analizar_participacion(df_reporte, vip_list, bonos)

    st.success("✅ Análisis completo. Resultados:")
    st.dataframe(df_resultado)

    if not df_resultado.empty:
        # --- GUARDADO EN LA HOJA DE ACTIVIDAD ---
        datos_guardar = [df_resultado.columns.tolist()] + df_resultado.values.tolist()
        hoja_actividad.clear()
        hoja_actividad.update("A1", datos_guardar)
        st.success("📊 Los resultados fueron guardados en la hoja 'actividad_diaria_vip'.")

        # --- GRÁFICO DE PARTICIPACIÓN ---
        if "Participó" in df_resultado.columns:
            st.subheader("📊 Participación de los VIPs en el día")
            participacion_count = df_resultado["Participó"].value_counts().reset_index()
            participacion_count.columns = ["Resultado", "Cantidad"]
            st.bar_chart(participacion_count.set_index("Resultado"))

        # --- FILTRO POR USUARIO ---
        st.subheader("🔎 Filtrar actividad por jugador")
        jugador_seleccionado = st.selectbox("Elegí un jugador:", options=df_resultado["Usuario"].unique())
        filtrado = df_resultado[df_resultado["Usuario"] == jugador_seleccionado]
        st.dataframe(filtrado)

        # --- DESCARGA CSV ---
        st.download_button("📤 Descargar resultados", data=df_resultado.to_csv(index=False), file_name="actividad_vip.csv")
    else:
        st.warning("⚠️ No se encontraron jugadores VIP activos o no coincidieron los criterios del bono.")
