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
    df = df_reporte[df_reporte['Del usuario'].isin(vip_list['usuario'])].copy()
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Hora'] = pd.to_datetime(df['Tiempo'], format="%H:%M:%S", errors='coerce').dt.hour

    resultados = []
    df.sort_values(by=['Del usuario', 'Fecha', 'Hora'], inplace=True)
    primera_carga = df.groupby(['Del usuario', 'Fecha']).first().reset_index()

    for _, row in primera_carga.iterrows():
        usuario = row['Del usuario']
        hora = row['Hora']
        monto = row['Depositar']
        fecha = row['Fecha'].date()

        bonos_del_dia = bonos[bonos['Fecha'] == fecha.strftime("%d/%m/%Y")]
        participo = False
        bono_usado = ""

        for _, b in bonos_del_dia.iterrows():
            h_ini = int(b['Hora inicio'].split(":")[0])
            h_fin = int(b['Hora fin'].split(":")[0])
            min_carga = int(b['Mínimo carga']) if b['Mínimo carga'] else 0
            bono_tipo = b.get('Tipo bono', '').lower()

            if h_ini <= hora <= h_fin:
                if bono_tipo == "primera carga":
                    if monto >= min_carga:
                        participo = True
                        bono_usado = f"{b['Bono % mejorado']} (Primera carga)"
                    else:
                        participo = True
                        bono_usado = f"{b['Bono % base']} (Primera carga)"
                    break
                else:
                    if monto >= min_carga:
                        participo = True
                        bono_usado = f"{b['Bono %']} ({b['Comunidad']})"
                        break

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

    # --- GUARDADO EN LA HOJA DE ACTIVIDAD ---
    datos_guardar = [df_resultado.columns.tolist()] + df_resultado.values.tolist()
    hoja_actividad.clear()
    hoja_actividad.update("A1", datos_guardar)
    st.success("📊 Los resultados fueron guardados en la hoja 'actividad_diaria_vip'.")

    # --- GRÁFICO DE PARTICIPACIÓN ---
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


