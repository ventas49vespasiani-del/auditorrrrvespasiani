import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Dashboard de Ventas - Azzurra", layout="wide", page_icon="📊")

# --- SISTEMA DE LOGUEO ---
def login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Acceso al Sistema de Reportes")
        col_login, _ = st.columns([1, 2])
        with col_login:
            usuario = st.text_input("Usuario")
            clave = st.text_input("Contraseña", type="password")
            if st.button("Ingresar"):
                # Puedes cambiar estas credenciales aquí
                if usuario == "admin" and clave == "cordoba2026":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        return False
    return True

# --- APLICACIÓN PRINCIPAL ---
if login():
    # Barra lateral
    st.sidebar.title("🛠️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("📊 Reporte de KPIs de Ventas - Repuestos")
    st.markdown("---")

    # Carga de archivo
    archivo_subido = st.file_uploader("Sube tu reporte de ventas (Excel o CSV)", type=["csv", "xlsx"])

    if archivo_subido:
        try:
            # CORRECCIÓN CRÍTICA: skiprows=1 salta el título "FACTURACION REPUESTOS..."
            if archivo_subido.name.endswith('.csv'):
                df = pd.read_csv(archivo_subido, skiprows=1)
            else:
                df = pd.read_excel(archivo_subido, skiprows=1)
            
            # LIMPIEZA DE COLUMNAS: Quita espacios invisibles en los nombres
            df.columns = df.columns.str.strip()

            # Verificamos que la columna fecha exista tras la limpieza
            if 'fecha' not in df.columns:
                st.error(f"❌ Error: No se encontró la columna 'fecha'. Columnas detectadas: {list(df.columns)}")
                st.stop()

            # Procesamiento de Fechas y Números
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            
            columnas_num = ["Venta Total", "Utilidad", "(%) Utilidad", "Costo Total"]
            for col in columnas_num:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Eliminar filas vacías al final del reporte
            df = df.dropna(subset=['Venta Total'])

            # --- FILTROS EN LA BARRA LATERAL ---
            st.sidebar.header("Filtros")
            sucursales = st.sidebar.multiselect("Sucursal", options=df["Sucursal"].unique(), default=df["Sucursal"].unique())
            vendedores = st.sidebar.multiselect("Corredor (Vendedor)", options=df["Corredor"].unique(), default=df["Corredor"].unique())

            # Aplicar filtros
            df_sel = df[(df["Sucursal"].isin(sucursales)) & (df["Corredor"].isin(vendedores))]

            # --- MÉTRICAS PRINCIPALES (KPIs) ---
            m1, m2, m3, m4 = st.columns(4)
            
            total_venta = df_sel["Venta Total"].sum()
            total_utilidad = df_sel["Utilidad"].sum()
            margen_prom = df_sel["(%) Utilidad"].mean()
            ops = len(df_sel)

            m1.metric("Ventas Totales", f"$ {total_venta:,.2f}")
            m2.metric("Utilidad Total", f"$ {total_utilidad:,.2f}")
            m3.metric("% Margen Prom.", f"{margen_prom:.2f}%")
            m4.metric("Operaciones", ops)

            st.markdown("---")

            # --- GRÁFICOS INTERACTIVOS ---
            c1, c2 = st.columns(2)

            with c1:
                st.subheader("Ventas por Mes")
                # Ordenamos por fecha para que el gráfico sea cronológico
                ventas_mes = df_sel.sort_values('fecha').groupby(['Año', 'Mes'])['Venta Total'].sum().reset_index()
                fig_linea = px.line(ventas_mes, x="Mes", y="Venta Total", color="Año", markers=True, template="plotly_white")
                st.plotly_chart(fig_linea, use_container_width=True)

            with c2:
                st.subheader("Distribución por Tipo de Cliente")
                fig_pie = px.pie(df_sel, values="Venta Total", names="Tipo Cliente", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)

            # --- TRABAJO SOBRE EXCEL Y EXPORTACIÓN ---
            st.subheader("📂 Herramientas de Datos")
            
            col_down, col_tab = st.columns([1, 4])
            
            with col_down:
                # Exportar a Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_sel.to_excel(writer, index=False, sheet_name='KPI_Filtrado')
                
                st.download_button(
                    label="📥 Descargar Resultado Excel",
                    data=output.getvalue(),
                    file_name="reporte_procesado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with st.expander("🔍 Ver/Editar vista previa de la tabla"):
                st.dataframe(df_sel)

        except Exception as e:
            st.error(f"Hubo un error al procesar el archivo: {e}")
    else:
        st.info("👋 Bienvenida/o. Por favor, sube el reporte de ventas para comenzar el análisis.")
