import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Dashboard de Ventas - Repuestos", layout="wide", page_icon="📊")

# --- SISTEMA DE LOGUEO ---
def login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Acceso al Sistema")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            # Puedes cambiar estas credenciales
            if usuario == "admin" and clave == "cordoba2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
        return False
    return True

# --- APLICACIÓN PRINCIPAL ---
if login():
    st.sidebar.title("Configuración")
    st.title("📊 Reporte de KPIs de Ventas de Repuestos")
    
    # Botón de cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()

    # Carga de archivo
    archivo_subido = st.file_uploader("Sube tu archivo Excel o CSV (Reporte de Mostrador)", type=["csv", "xlsx"])

    if archivo_subido:
        # Lectura de datos (skiprows=1 porque tu archivo tiene un título en la primera fila)
        try:
            if archivo_subido.name.endswith('.csv'):
                df = pd.read_csv(archivo_subido, skiprows=1)
            else:
                df = pd.read_excel(archivo_subido, skiprows=1)
            
            # Limpieza rápida
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            df = df.dropna(subset=['Venta Total']) # Quitar filas vacías

            # --- FILTROS ---
            st.sidebar.header("Filtros de Datos")
            sucursales = st.sidebar.multiselect("Seleccionar Sucursal", options=df["Sucursal"].unique(), default=df["Sucursal"].unique())
            vendedores = st.sidebar.multiselect("Seleccionar Corredor", options=df["Corredor"].unique(), default=df["Corredor"].unique())

            # Aplicar filtros
            df_filtrado = df[(df["Sucursal"].isin(sucursales)) & (df["Corredor"].isin(vendedores))]

            # --- MÉTRICAS (KPIs) ---
            col1, col2, col3, col4 = st.columns(4)
            
            total_venta = df_filtrado["Venta Total"].sum()
            total_utilidad = df_filtrado["Utilidad"].sum()
            margen_promedio = df_filtrado["(%) Utilidad"].mean()
            cantidad_fac = len(df_filtrado)

            col1.metric("Venta Bruta", f"$ {total_venta:,.2f}")
            col2.metric("Utilidad Bruta", f"$ {total_utilidad:,.2f}")
            col3.metric("% Margen Prom.", f"{margen_promedio:.2f}%")
            col4.metric("N° Operaciones", cantidad_fac)

            st.divider()

            # --- GRÁFICOS ---
            c1, c2 = st.columns(2)

            with c1:
                st.subheader("Ventas por Mes y Año")
                # Agrupamos por Año/Mes para el gráfico
                ventas_tiempo = df_filtrado.groupby(['Año', 'Mes'])['Venta Total'].sum().reset_index()
                fig_linea = px.line(ventas_tiempo, x="Mes", y="Venta Total", color="Año", markers=True, title="Tendencia de Ventas")
                st.plotly_chart(fig_linea, use_container_width=True)

            with c2:
                st.subheader("Ventas por Tipo de Cliente")
                fig_pie = px.pie(df_filtrado, values="Venta Total", names="Tipo Cliente", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

            # --- HERRAMIENTA DE TRABAJO Y EXPORTACIÓN ---
            st.subheader("📥 Exportar Resultados")
            st.write("Puedes filtrar los datos arriba y descargar solo lo que necesitas.")
            
            # Convertir DataFrame filtrado a Excel en memoria
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name='Reporte_Filtrado')
            
            st.download_button(
                label="Descargar Excel Filtrado",
                data=output.getvalue(),
                file_name="reporte_kpi_personalizado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            with st.expander("Ver tabla completa de datos"):
                st.dataframe(df_filtrado)

        except Exception as e:
            st.error(f"Hubo un problema al leer el archivo. Asegúrate de que sea el formato correcto. Error: {e}")
    else:
        st.info("Por favor, sube el archivo Excel que exportaste del sistema de ventas.")
