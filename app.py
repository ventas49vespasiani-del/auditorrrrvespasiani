import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Auditoría Vespasiani - Repuestos", layout="wide")

# --- SISTEMA DE AUTENTICACIÓN ---
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
    elif not st.session_state["password_correct"]:
        st.error("Usuario o contraseña incorrectos")
        return False
    return True

if check_password():
    st.title("📊 Auditoría de Repuestos Mostrador - Vespasiani")

    # CARGA AUTOMÁTICA DEL ARCHIVO
    file_path = "reporte_repuestos_mostrador.xlsx - MOSTRADOR.csv"
    
    try:
        # Se omite la primera fila que suele ser el título del reporte en tu CSV
        df = pd.read_csv(file_path, skiprows=1)
        
        # Limpieza básica
        df = df.dropna(subset=["Sucursal", "Mes"])
        
        # --- SIDEBAR / FILTROS ---
        st.sidebar.header("Filtros de Auditoría")
        
        sucursales = sorted(df["Sucursal"].unique())
        sucursal_sel = st.sidebar.multiselect("Sucursal:", options=sucursales, default=sucursales)
        
        meses = df["Mes"].unique()
        mes_sel = st.sidebar.multiselect("Mes:", options=meses, default=meses)

        df_selection = df.query("Sucursal == @sucursal_sel & Mes == @mes_sel")

        # --- KPIs ---
        col1, col2, col3 = st.columns(3)
        total_venta = df_selection["Venta Total"].sum()
        utilidad_prom = df_selection["(%) Utilidad"].mean()
        ops = len(df_selection)

        col1.metric("Venta Total", f"$ {total_venta:,.2f}")
        col2.metric("Utilidad Prom.", f"{utilidad_prom:.2f}%")
        col3.metric("Operaciones", ops)

        st.markdown("---")

        # --- GRÁFICOS ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Ventas por Mes")
            v_mes = df_selection.groupby("Mes").sum(numeric_only=True)[["Venta Total"]].reset_index()
            fig_bar = px.bar(v_mes, x="Mes", y="Venta Total", color_discrete_sequence=["#0083B8"])
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with c2:
            st.subheader("Ventas por Corredor")
            v_corr = df_selection.groupby("Corredor").sum(numeric_only=True)[["Venta Total"]].reset_index()
            fig_pie = px.pie(v_corr, values="Venta Total", names="Corredor", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- TABLA ---
        st.subheader("Detalle de Auditoría")
        st.dataframe(df_selection, use_container_width=True)

        # --- EXPORTAR ---
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_selection.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Descargar Auditoría (Excel)",
            data=buffer.getvalue(),
            file_name="auditoria_vespasiani.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except FileNotFoundError:
        st.warning(f"Esperando el archivo: {file_path}")
    except Exception as e:
        st.error(f"Error técnico: {e}")
