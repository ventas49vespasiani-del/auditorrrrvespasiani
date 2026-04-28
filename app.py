import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Vespasiani - Control de Gestión", layout="wide", page_icon="📈")

# --- ESTILO PERSONALIZADO (Azul Oscuro) ---
st.markdown("""
    <style>
    /* Color de contorno para selectores */
    div[data-baseweb="select"] > div {
        border-color: #002D52 !important;
    }
    /* Estilo para los títulos de la barra lateral */
    .css-163ttbj {
        color: #002D52 !important;
    }
    /* Botones principales */
    .stButton>button {
        background-color: #002D52;
        color: white;
    }
    </style>
    """, unsafe_allow_exists=True)

# --- LOGIN ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "12345":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    return st.session_state.get("password_correct", False)

if check_password():
    file_path = "reporte_repuestos_mostrador.xlsx"

    try:
        # Carga de datos (asumiendo que la fila 1 es el título del reporte)
        df = pd.read_excel(file_path, skiprows=1)
        df = df.dropna(subset=["Sucursal", "Mes"])

        # --- BARRA LATERAL CON FILTROS ---
        st.sidebar.header("⚙️ Configuración")
        
        sucursales = sorted(df["Sucursal"].unique())
        sel_sucursal = st.sidebar.multiselect("Filtrar por Sucursal:", options=sucursales, default=sucursales)
        
        meses = df["Mes"].unique()
        sel_mes = st.sidebar.multiselect("Filtrar por Mes:", options=meses, default=meses)
        
        df_filt = df.query("Sucursal == @sel_sucursal & Mes == @sel_mes")

        # --- ORGANIZACIÓN EN 3 HOJAS (TABS) ---
        tab1, tab2, tab3 = st.tabs(["📊 1. Análisis General", "👤 2. Análisis Individual", "📋 3. Datos Detallados"])

        # --- HOJA 1: ANÁLISIS GENERAL ---
        with tab1:
            st.subheader("Estado de Rentabilidad y Ventas")
            
            # KPIs Principales
            c1, c2, c3, c4 = st.columns(4)
            v_total = df_filt["Venta Total"].sum()
            c_total = df_filt["Costo Total"].sum()
            utilidad_total = df_filt["Utilidad"].sum()
            margen_prom = df_filt["(%) Utilidad"].mean()

            c1.metric("Venta Total", f"$ {v_total:,.0f}")
            c2.metric("Costo Total", f"$ {c_total:,.0f}")
            c3.metric("Rentabilidad ($)", f"$ {utilidad_total:,.0f}", delta=f"{utilidad_total/v_total*100:.1f}% de la venta")
            c4.metric("Margen Promedio (%)", f"{margen_prom:.2f}%")

            st.markdown("---")
            
            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                st.write("**Evolución de Venta vs Rentabilidad ($)**")
                ev_mensual = df_filt.groupby("Mes").sum(numeric_only=True)[["Venta Total", "Utilidad"]].reset_index()
                fig_ev = px.line(ev_mensual, x="Mes", y=["Venta Total", "Utilidad"], markers=True, 
                                 color_discrete_map={"Venta Total": "#002D52", "Utilidad": "#0083B8"})
                st.plotly_chart(fig_ev, use_container_width=True)
            
            with col_graf2:
                st.write("**Evolución de Margen de Ganancia (%)**")
                margen_mensual = df_filt.groupby("Mes").mean(numeric_only=True)[["(%) Utilidad"]].reset_index()
                fig_margen = px.area(margen_mensual, x="Mes", y="(%) Utilidad", color_discrete_sequence=["#2ECC71"])
                st.plotly_chart(fig_margen, use_container_width=True)

        # --- HOJA 2: ANÁLISIS INDIVIDUAL ---
        with tab2:
            st.subheader("Desempeño por Actividad")
            
            # Fila 1: Vendedores y Clientes
            col_v, col_c = st.columns(2)
            
            with col_v:
                st.write("**Top Ranking de Vendedores (Corredores)**")
                vendedores = df_filt.groupby("Corredor").sum(numeric_only=True)[["Venta Total"]].sort_values("Venta Total", ascending=True).reset_index()
                fig_vend = px.bar(vendedores, y="Corredor", x="Venta Total", orientation='h', color_discrete_sequence=["#002D52"])
                st.plotly_chart(fig_vend, use_container_width=True)
            
            with col_c:
                st.write("**Top 10 Clientes por Volumen**")
                clientes = df_filt.groupby("cliente").sum(numeric_only=True)[["Venta Total"]].nlargest(10, "Venta Total").reset_index()
                fig_cli = px.bar(clientes, x="cliente", y="Venta Total", color_discrete_sequence=["#0083B8"])
                st.plotly_chart(fig_cli, use_container_width=True)

            st.markdown("---")
            
            # Fila 2: Clientes a verificar (Drill-down)
            st.subheader("🔍 Clientes a Verificar")
            st.info("Clientes con márgenes de ganancia fuera de lo común (muy altos o negativos)")
            
            # Filtro lógico para clientes a verificar: Margen < 5% o Margen > 80%
            criticos = df_filt[(df_filt["(%) Utilidad"] < 5) | (df_filt["(%) Utilidad"] > 80)]
            st.dataframe(criticos[["fecha", "comprobante", "cliente", "Venta Total", "Utilidad", "(%) Utilidad", "Sucursal"]], use_container_width=True)

        # --- HOJA 3: DATOS DETALLADOS ---
        with tab3:
            st.subheader("Base de Datos Filtrada")
            st.write("Usa esta tabla para buscar facturas específicas o exportar el reporte.")
            
            # Buscador rápido
            busqueda = st.text_input("Buscar por nombre de cliente o comprobante:")
            if busqueda:
                df_final = df_filt[df_filt.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
            else:
                df_final = df_filt

            st.dataframe(df_final, use_container_width=True)

            # Botón de Descarga
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Reporte Completo (Excel)",
                data=buffer.getvalue(),
                file_name=f"Auditoria_{sel_mes[0] if sel_mes else 'General'}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico: {e}")
        st.info("A
