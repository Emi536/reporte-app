import streamlit as st
import pandas as pd
import datetime
import gspread
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials

# --- THEME CONFIGURATION ---
st.set_page_config(
    page_title="VIP Analysis Dashboard",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': 'VIP Analysis Dashboard v2.0'
    }
)

# --- CUSTOM CSS FOR DARK THEME ---
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stApp {
        background-color: #0E1117;
    }
    .css-1d391kg, .css-12oz5g7 {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2C2C2C;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4B4B4B;
        border-bottom: 2px solid #FFD700;
    }
    .stButton>button {
        background-color: #FFD700;
        color: #0E1117;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #E6C200;
        color: #0E1117;
    }
    .stDownloadButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stDownloadButton>button:hover {
        background-color: #45a049;
    }
    .success-card {
        background-color: #1E3A2F;
        border-left: 5px solid #4CAF50;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .warning-card {
        background-color: #3A2E1E;
        border-left: 5px solid #FFC107;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #2C2C2C;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #FFD700;
    }
    .metric-label {
        font-size: 14px;
        color: #CCCCCC;
    }
    .dataframe {
        background-color: #1E1E1E !important;
    }
    .css-1ht1j8u {
        background-color: #2C2C2C !important;
    }
    .css-1ht1j8u:hover {
        background-color: #3C3C3C !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://via.placeholder.com/100x100.png?text=VIP", width=80)
with col2:
    st.title("🌟 VIP Activity Analysis Dashboard")
    st.markdown("<p style='color: #CCCCCC; margin-top: -10px;'>Track and analyze VIP player activity across communities</p>", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔧 Dashboard Controls")
    st.markdown("---")
    
    st.markdown("### 📅 Date Filter")
    today = datetime.date.today()
    default_date = today
    selected_date = st.date_input("Select Date", default_date)
    
    st.markdown("### 🏆 Community Filter")
    community_filter = st.multiselect(
        "Select Communities",
        ["All", "Fenix", "Eros"],
        default="All"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Dashboard Info")
    st.info("This dashboard analyzes VIP player activity and bonus usage across different communities.")
    
    st.markdown("---")
    st.markdown("### 👤 User Guide")
    with st.expander("How to use this dashboard"):
        st.markdown("""
        1. Upload your daily casino report
        2. View the analysis results
        3. Filter by date or community
        4. Download the results as CSV
        """)

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def connect_to_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open("seguimiento_vip")
    return sh

try:
    sh = connect_to_sheets()
    hoja_vips = sh.worksheet("vip_list")
    hoja_bonos = sh.worksheet("bonos_ofrecidos")
    hoja_actividad = sh.worksheet("actividad_diaria_vip")
    connection_error = False
except Exception as e:
    connection_error = True
    st.error(f"Error connecting to Google Sheets: {e}")

# --- DATA LOADING FUNCTIONS ---
@st.cache_data(ttl=300)
def cargar_data():
    vip_list = pd.DataFrame(hoja_vips.get_all_records())
    bonos = pd.DataFrame(hoja_bonos.get_all_records())
    return vip_list, bonos

def analizar_participacion(df_reporte, vip_list, bonos):
    # Convert and clean data
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
    total_general = resumen['Monto Total'].sum() if not resumen.empty else 0
    if total_general > 0:
        resumen['% del Total'] = (resumen['Monto Total'] / total_general * 100).round(2).astype(str) + "%"
    else:
        resumen['% del Total'] = "0%"

    # Agregar los usuarios que no participaron
    usuarios_con_datos = resumen['Usuario'].unique() if not resumen.empty else []
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

    return df_resultado, resumen

# --- MAIN CONTENT ---
tabs = st.tabs(["📊 Dashboard", "📁 Upload Report", "📋 Data Tables", "📈 Charts"])

with tabs[0]:
    st.markdown("## 📊 VIP Activity Dashboard")
    
    if 'df_resultado' in locals() and 'resumen' in locals():
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Active VIPs</div>
            </div>
            """.format(len(resumen[resumen['Monto Total'] > 0])), unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">${:,.2f}</div>
                <div class="metric-label">Total Deposits</div>
            </div>
            """.format(resumen['Monto Total'].sum()), unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Bonus Uses</div>
            </div>
            """.format(resumen['Veces que usó el bono'].sum()), unsafe_allow_html=True)
            
        with col4:
            participation_rate = len(resumen[resumen['Monto Total'] > 0]) / len(resumen) * 100 if len(resumen) > 0 else 0
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.1f}%</div>
                <div class="metric-label">Participation Rate</div>
            </div>
            """.format(participation_rate), unsafe_allow_html=True)
        
        # Community Distribution
        st.markdown("### 🏆 Community Distribution")
        community_data = resumen.groupby('Comunidad').agg({
            'Monto Total': 'sum',
            'Usuario': 'nunique'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                community_data, 
                values='Monto Total', 
                names='Comunidad',
                title='Deposit Distribution by Community',
                color_discrete_sequence=px.colors.sequential.Plasma,
                hole=0.4
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                legend=dict(orientation='h', y=-0.1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.bar(
                community_data,
                x='Comunidad',
                y='Usuario',
                title='Active VIPs by Community',
                color='Comunidad',
                color_discrete_sequence=px.colors.sequential.Plasma
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(title='Community'),
                yaxis=dict(title='Number of VIPs')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top VIPs
        st.markdown("### 🌟 Top VIPs by Deposit Amount")
        top_vips = resumen.sort_values('Monto Total', ascending=False).head(10)
        
        fig = px.bar(
            top_vips,
            x='Usuario',
            y='Monto Total',
            color='Comunidad',
            title='Top 10 VIPs by Deposit Amount',
            color_discrete_sequence=px.colors.sequential.Plasma
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(title='VIP User'),
            yaxis=dict(title='Total Deposit Amount')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("""
        <div class="warning-card">
            <h3>📊 Welcome to the VIP Analysis Dashboard!</h3>
            <p>Please upload a report file in the "Upload Report" tab to see the dashboard.</p>
        </div>
        """, unsafe_allow_html=True)

with tabs[1]:
    st.markdown("## 📁 Upload Casino Report")
    
    upload_col1, upload_col2 = st.columns([3, 2])
    
    with upload_col1:
        st.markdown("""
        <div style="background-color: #2C2C2C; padding: 20px; border-radius: 10px;">
            <h3>📤 Upload Your Report</h3>
            <p>Upload your daily casino report to analyze VIP activity and bonus usage.</p>
            <p>Supported formats: Excel (.xlsx) and CSV (.csv)</p>
        </div>
        """, unsafe_allow_html=True)
        
        archivo = st.file_uploader("", type=["csv", "xlsx"])
        
        if archivo:
            try:
                with st.spinner("Processing report..."):
                    df_reporte = pd.read_excel(archivo) if archivo.name.endswith(".xlsx") else pd.read_csv(archivo)
                    vip_list, bonos = cargar_data()
                    df_resultado, resumen = analizar_participacion(df_reporte, vip_list, bonos)
                
                st.markdown("""
                <div class="success-card">
                    <h3>✅ Analysis Complete!</h3>
                    <p>Your report has been processed successfully. View the results in the Dashboard, Data Tables, and Charts tabs.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Save results button
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=resumen.to_csv(index=False),
                    file_name=f"vip_activity_report_{datetime.date.today().strftime('%Y-%m-%d')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error processing the file: {e}")
    
    with upload_col2:
        st.markdown("""
        <div style="background-color: #2C2C2C; padding: 20px; border-radius: 10px; height: 100%;">
            <h3>📋 Report Requirements</h3>
            <p>Your report should include the following columns:</p>
            <ul>
                <li>Fecha (Date)</li>
                <li>Tiempo (Time)</li>
                <li>Al usuario (To user)</li>
                <li>Del usuario (From user)</li>
                <li>Depositar (Deposit amount)</li>
            </ul>
            <p>Make sure your data is properly formatted to ensure accurate analysis.</p>
        </div>
        """, unsafe_allow_html=True)

with tabs[2]:
    st.markdown("## 📋 Data Tables")
    
    if 'df_resultado' in locals() and 'resumen' in locals():
        data_tabs = st.tabs(["Summary", "Detailed Data", "VIP List", "Bonus Offers"])
        
        with data_tabs[0]:
            st.markdown("### 📊 Summary of VIP Activity")
            st.dataframe(
                resumen.sort_values('Monto Total', ascending=False),
                use_container_width=True,
                column_config={
                    "Usuario": st.column_config.TextColumn("VIP User"),
                    "Bono Usado": st.column_config.TextColumn("Bonus Used"),
                    "Comunidad": st.column_config.TextColumn("Community"),
                    "Monto Total": st.column_config.NumberColumn("Total Amount", format="$%.2f"),
                    "Hora de carga": st.column_config.TextColumn("Last Deposit Time"),
                    "Veces que usó el bono": st.column_config.NumberColumn("Times Bonus Used"),
                    "% del Total": st.column_config.TextColumn("% of Total")
                }
            )
            
        with data_tabs[1]:
            st.markdown("### 📝 Detailed Activity Data")
            st.dataframe(
                df_resultado,
                use_container_width=True,
                column_config={
                    "Fecha": st.column_config.TextColumn("Date"),
                    "Usuario": st.column_config.TextColumn("User"),
                    "Comunidad": st.column_config.TextColumn("Community"),
                    "Monto": st.column_config.NumberColumn("Amount", format="$%.2f"),
                    "Hora de carga": st.column_config.TextColumn("Deposit Time"),
                    "Bono Usado": st.column_config.TextColumn("Bonus Used"),
                    "Participó": st.column_config.TextColumn("Participated")
                }
            )
            
        with data_tabs[2]:
            st.markdown("### 👥 VIP List")
            vip_list, _ = cargar_data()
            st.dataframe(vip_list, use_container_width=True)
            
        with data_tabs[3]:
            st.markdown("### 🎁 Bonus Offers")
            _, bonos = cargar_data()
            st.dataframe(bonos, use_container_width=True)
    else:
        st.info("Please upload a report file to view data tables.")

with tabs[3]:
    st.markdown("## 📈 Charts and Visualizations")
    
    if 'df_resultado' in locals() and 'resumen' in locals():
        chart_tabs = st.tabs(["Bonus Usage", "Hourly Activity", "Community Comparison"])
        
        with chart_tabs[0]:
            st.markdown("### 🎁 Bonus Usage Analysis")
            
            # Prepare data
            bonus_data = resumen[resumen['Bono Usado'] != 'No'].copy()
            bonus_counts = bonus_data.groupby('Bono Usado').agg({
                'Monto Total': 'sum',
                'Usuario': 'nunique',
                'Veces que usó el bono': 'sum'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    bonus_counts, 
                    values='Monto Total', 
                    names='Bono Usado',
                    title='Deposit Amount by Bonus Type',
                    color_discrete_sequence=px.colors.sequential.Plasma
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white')
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                fig = px.bar(
                    bonus_counts,
                    x='Bono Usado',
                    y='Veces que usó el bono',
                    title='Number of Times Each Bonus Was Used',
                    color='Bono Usado',
                    color_discrete_sequence=px.colors.sequential.Plasma
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    xaxis=dict(title='Bonus Type'),
                    yaxis=dict(title='Usage Count')
                )
                st.plotly_chart(fig, use_container_width=True)
            
        with chart_tabs[1]:
            st.markdown("### ⏰ Hourly Activity Analysis")
            
            # Prepare hourly data
            df_resultado['Hour'] = pd.to_datetime(df_resultado['Hora de carga']).dt.hour
            hourly_data = df_resultado.groupby('Hour').agg({
                'Monto': 'sum',
                'Usuario': 'nunique'
            }).reset_index()
            
            # Fill missing hours
            all_hours = pd.DataFrame({'Hour': range(0, 24)})
            hourly_data = pd.merge(all_hours, hourly_data, on='Hour', how='left').fillna(0)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=hourly_data['Hour'],
                y=hourly_data['Monto'],
                mode='lines+markers',
                name='Deposit Amount',
                line=dict(color='#FFD700', width=3),
                marker=dict(size=8, color='#FFD700')
            ))
            
            fig.add_trace(go.Bar(
                x=hourly_data['Hour'],
                y=hourly_data['Usuario'],
                name='Active VIPs',
                marker_color='rgba(75, 192, 192, 0.7)'
            ))
            
            fig.update_layout(
                title='Hourly Activity Distribution',
                xaxis=dict(
                    title='Hour of Day',
                    tickmode='linear',
                    tick0=0,
                    dtick=1
                ),
                yaxis=dict(title='Deposit Amount'),
                yaxis2=dict(
                    title='Number of VIPs',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.01, y=0.99),
                hovermode='x unified',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with chart_tabs[2]:
            st.markdown("### 🏆 Community Comparison")
            
            # Prepare community data
            community_metrics = df_resultado.groupby('Comunidad').agg({
                'Monto': ['sum', 'mean', 'median', 'count'],
                'Usuario': 'nunique'
            }).reset_index()
            
            community_metrics.columns = ['Comunidad', 'Total Deposit', 'Average Deposit', 'Median Deposit', 'Transaction Count', 'Unique VIPs']
            
            # Filter out empty community
            community_metrics = community_metrics[community_metrics['Comunidad'] != '']
            
            # Create radar chart
            categories = ['Total Deposit', 'Average Deposit', 'Median Deposit', 'Transaction Count', 'Unique VIPs']
            
            fig = go.Figure()
            
            for i, community in enumerate(community_metrics['Comunidad']):
                # Normalize values for radar chart
                values = []
                for cat in categories:
                    max_val = community_metrics[cat].max()
                    val = community_metrics.loc[community_metrics['Comunidad'] == community, cat].values[0]
                    values.append(val / max_val if max_val > 0 else 0)
                
                # Add trace
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=community,
                    line_color=px.colors.sequential.Plasma[i*3]
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                title='Community Performance Comparison',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Community metrics table
            st.markdown("### 📊 Community Metrics")
            st.dataframe(
                community_metrics,
                use_container_width=True,
                column_config={
                    "Comunidad": st.column_config.TextColumn("Community"),
                    "Total Deposit": st.column_config.NumberColumn("Total Deposit", format="$%.2f"),
                    "Average Deposit": st.column_config.NumberColumn("Avg Deposit", format="$%.2f"),
                    "Median Deposit": st.column_config.NumberColumn("Median Deposit", format="$%.2f"),
                    "Transaction Count": st.column_config.NumberColumn("# Transactions"),
                    "Unique VIPs": st.column_config.NumberColumn("# Unique VIPs")
                }
            )
    else:
        st.info("Please upload a report file to view charts and visualizations.")

# --- FOOTER ---
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; color: #CCCCCC;">
        <p>VIP Analysis Dashboard v2.0 | Last updated: {}</p>
    </div>
    """.format(datetime.datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)
