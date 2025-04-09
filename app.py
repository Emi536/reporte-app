
import pandas as pd
import streamlit as st

def procesar_reporte(df):
    df.columns = [
        "ID", "Tipo", "Monto", "?1", "?2", "?3", "Saldo",
        "Fecha", "Hora", "UsuarioSistema", "Plataforma", "Admin", "Jugador"
    ]

    df_cargas = df[df["Tipo"] == "in"]

    top_cantidades = (
        df_cargas.groupby("Jugador")
        .agg(Cantidad_Cargas=("Jugador", "count"), Monto_Total_Cargado=("Monto", "sum"))
        .sort_values(by="Cantidad_Cargas", ascending=False)
        .head(10)
        .reset_index()
    )

    top_montos = (
        df_cargas.groupby("Jugador")
        .agg(Monto_Total_Cargado=("Monto", "sum"), Cantidad_Cargas=("Jugador", "count"))
        .sort_values(by="Monto_Total_Cargado", ascending=False)
        .head(10)
        .reset_index()
    )

    return top_cantidades, top_montos

# App con Streamlit
st.title("📊 Reporte de Cargas del Casino")

archivo = st.file_uploader("Subí tu archivo de reporte (.xlsx):", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)
    st.success("Archivo cargado correctamente ✅")

    top_cant, top_monto = procesar_reporte(df)

    st.subheader("🔢 Top 10 por Cantidad de Cargas")
    st.dataframe(top_cant)

    st.subheader("💰 Top 10 por Monto Total Cargado")
    st.dataframe(top_monto)

    excel_writer = pd.ExcelWriter("reporte_casino_resultado.xlsx", engine="xlsxwriter")
    top_cant.to_excel(excel_writer, sheet_name="Top Cantidad", index=False)
    top_monto.to_excel(excel_writer, sheet_name="Top Monto", index=False)
    excel_writer.close()

    with open("reporte_casino_resultado.xlsx", "rb") as file:
        st.download_button("📥 Descargar Reporte en Excel", file, file_name="Top_Reporte_Casino.xlsx")
