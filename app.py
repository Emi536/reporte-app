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
    df_reporte['Tiempo'] = pd.to_datetime(df_reporte['Tiempo'], format="%H:%M:%S", errors='coerce')
    df_reporte['Hora'] = df_reporte['Tiempo'].dt.hour
    df_reporte['Depositar'] = pd.to_numeric(df_reporte['Depositar'], errors='coerce').fillna(0)
    df_reporte = df_reporte.dropna(subset=['Fecha', 'Hora'])

    resultados = []

    for _, row in df_reporte.iterrows():
        usuario = row['Al usuario']
        del_usuario = row['Del usuario']
        hora = row['Hora']
        monto = row['Depositar']
        fecha = row['Fecha'].date()
        tiempo = row['Tiempo'].strftime("%H:%M:%S")

        comunidad = ""
        if "Fenix" in del_usuario:
            comunidad = "Fenix"
        elif "Eros" in del_usuario:
            comunidad = "Eros"

        bonos_del_dia = bonos[(bonos['Fecha'] == fecha.strftime("%d/%m/%Y")) &
                              (bonos['Comunidad'].str.lower() == comunidad.lower())]
        participo = False
        bono_usado = "No"

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
                if min_mejorado and monto >= min_mejorado:
                    participo = True
                    bono_usado = f"{b['Bono % mejorado']}% ({comunidad})"
                elif monto >= min_carga:
                    participo = True
                    bono_usado = f"{b['Bono % base']}% ({comunidad})"

        resultados.append({
            "Fecha": fecha.strftime("%d/%m/%Y"),
            "Usuario": usuario,
            "Comunidad": comunidad,
            "Monto": monto,
            "Hora de carga": tiempo,
            "Bono Usado": bono_usado,
            "Participó": "✅" if participo else "❌"
        })

    df_resultado = pd.DataFrame(resultados)

    # Agrupación por usuario y bono
    resumen = df_resultado[df_resultado["Participó"] == "✅"].groupby(['Usuario', 'Bono Usado', 'Comunidad'], as_index=False).agg({
        'Monto': 'sum',
        'Hora de carga': 'last',
        'Participó': 'count'
    })
    resumen.rename(columns={
        'Monto': 'Monto Total',
        'Participó': 'Veces que usó el bono'
    }, inplace=True)

    # % sobre el total
    total_general = resumen['Monto Total'].sum()
    resumen['% del Total'] = (resumen['Monto Total'] / total_general * 100).round(2).astype(str) + "%"

    # Agregar los usuarios que no participaron
    usuarios_con_datos = resumen['Usuario'].unique()
    for jugador in vip_list['usuario']:
        if jugador not in usuarios_con_datos:
            resumen = pd.concat([resumen, pd.DataFrame([{
                "Usuario": jugador,
                "Bono Usado": "No",
                "Comunidad": "",
                "Monto Total": 0,
                "Hora de carga": "",
                "Veces que usó el bono": 0,
                "% del Total": "0%"
            }])], ignore_index=True)

    return resumen

# --- UI: SUBIDA DE REPORTE ---
archivo = st.file_uploader("📁 Subí el reporte diario del casino", type=["csv", "xlsx"])

if archivo:
    df_reporte = pd.read_excel(archivo) if archivo.name.endswith(".xlsx") else pd.read_csv(archivo)
    vip_list, bonos = cargar_data()
    df_resultado = analizar_participacion(df_reporte, vip_list, bonos)

    st.success("✅ Análisis completo. Resultados:")
    st.dataframe(df_resultado)

    # --- DESCARGA CSV ---
    st.download_button("📤 Descargar resultados", data=df_resultado.to_csv(index=False), file_name="actividad_vip_resumen.csv")
