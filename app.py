import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Análisis VIP", layout="wide")
st.title("🎰 Análisis Diario de Actividad VIP")

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
            h_ini = int(b['Hora inicio'].split(":")[0])
            h_fin = int(b['Hora fin'].split(":")[0])
            min_carga = int(b['Mínimo carga']) if b['Mínimo carga'] else 0
            min_mejorado = int(b['Mínimo mejorado']) if 'Mínimo mejorado' in b and b['Mínimo mejorado'] else None
            bono_tipo = b.get('Tipo bono', '').lower()

            if h_ini <= hora <= h_fin:
                if bono_tipo == "primera carga":
                    cargas_dia = df_reporte[(df_reporte['Al usuario'] == usuario) & (df_reporte['Fecha'].dt.date == fecha)]
                    if row.equals(cargas_dia.iloc[0]):
                        if min_mejorado and monto >= min_mejorado:
                            participo = True
                            bono_usado = f"{b['Bono % mejorado']} (Primera carga mejorada)"
                        elif monto >= min_carga:
                            participo = True
                            bono_usado = f"{b['Bono % base']} (Primera carga)"
                else:
                    if monto >= min_carga:
                        participo = True
                        bono_usado = f"{b['Bono %']} ({b['Comunidad']})"

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

