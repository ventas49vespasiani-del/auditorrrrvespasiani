import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Vespasiani - Control de Gestión", layout="wide", page_icon="📈")

# --- ESTILO PERSONALIZADO (Contorno Azul Oscuro) ---
st.markdown("""
    <style>
    div[data-baseweb="select"] > div {
        border-color: #002D52 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #002D52 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
        # Carga de datos
        df = pd.read_excel(file_path, skiprows=1)
        df = df.dropna(subset=["Sucursal", "Mes"])

        # --- BARRA LATERAL ---
        st.sidebar.header("⚙️ Configuración")
        
        sucursales = sorted(df["Sucursal"].unique())
        sel_sucursal = st.sidebar.multiselect("Filtrar por Sucursal:", options=sucursales, default=sucursales)
        
        meses = df["Mes"].unique()
        sel_mes = st.sidebar.multiselect("Filtrar por Mes:", options=meses, default=meses)
        
        df_filt = df.query("Sucursal == @sel_sucursal & Mes == @sel_mes")

        # --- TABS ---
        tab1, tab2, tab3 = st.tabs(["📊 1. Análisis General", "👤 2. Análisis Individual", "📋 3. Datos Detallados"])

        # --- HOJA 1: ANÁLISIS GENERAL ---
        with tab1:
            st.subheader("Estado de Rentabilidad y Ventas")
            c1, c2, c3, c4 = st.columns(4)
            
            v_total = df_filt["Venta Total"].sum()
            c_total = df_filt["Costo Total"].sum()
            utilidad_total = df_filt["Utilidad"].sum()
            margen_prom = df_filt["(%) Utilidad"].mean()

            c1.metric("Venta Total", f"$ {v_total:,.0f}")
            c2.metric("Costo Total", f"$ {c_total:,.0f}")
            c3.metric("Rentabilidad ($)", f"$ {utilidad_total:,.0f}")
            c4.metric("Margen Promedio (%)", f"{margen_prom:.2f}%")

            st.markdown("---")
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**Evolución de Venta vs Rentabilidad ($)**")
                ev_mensual = df_filt.groupby("Mes").sum(numeric_only=True)[["Venta Total", "Utilidad"]].reset_index()
                fig_ev = px.line(ev_mensual, x="Mes", y=["Venta Total", "Utilidad"], markers=True, 
                                 color_discrete_map={"Venta Total": "#002D52", "Utilidad": "#0083B8"})
                st.plotly_chart(fig_ev, use_container_width=True)
            
            with col_g2:
                st.write("**Evolución de Margen de Ganancia (%)**")
                margen_mensual = df_filt.groupby("Mes").mean(numeric_only=True)[["(%) Utilidad"]].reset_index()
                fig_margen = px.area(margen_mensual, x="Mes", y="(%) Utilidad", color_discrete_sequence=["#2ECC71"])
                st.plotly_chart(fig_margen, use_container_width=True)

        # --- HOJA 2: ANÁLISIS INDIVIDUAL ---
        with tab2:
            st.subheader("Desempeño por Actividad")
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
            st.subheader("🔍 Clientes a Verificar (Márgenes Críticos)")
            criticos = df_filt[(df_filt["(%) Utilidad"] < 5) | (df_filt["(%) Utilidad"] > 80)]
            st.dataframe(criticos[["fecha", "comprobante", "cliente", "Venta Total", "Utilidad", "(%) Utilidad", "Sucursal"]], use_container_width=True)

        # --- HOJA 3: DATOS DETALLADOS ---
        with tab3:
            st.subheader("Explorador de Datos")
            busqueda = st.text_input("Buscar por cliente o comprobante:")
            
            df_final = df_filt.copy()
            if busqueda:
                df_final = df_final[df_final.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]

            st.dataframe(df_final, use_container_width=True)

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=buffer.getvalue(),
                file_name="Auditoria_Vespasiani.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error técnico: {e}")
        st.info("Verifica que el archivo 'reporte_repuestos_mostrador.xlsx' esté en el repositorio.")
