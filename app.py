import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Vespasiani - Control de Gestión", layout="wide", page_icon="📊")

# --- LOGIN SIMPLE ---
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
    st.title("🚀 Dashboard Avanzado de Auditoría - Vespasiani")
    
    # RUTA DEL ARCHIVO
    file_path = "reporte_repuestos_mostrador.xlsx"

    try:
        # Carga de datos
        df = pd.read_excel(file_path, skiprows=1)
        
        # Limpieza básica
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.dropna(subset=["Sucursal", "Mes"])
        
        # --- FILTROS GLOBALES (SIDEBAR) ---
        st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_uN7Wc-r7HlD8X_mI3S-O_u5q1iS1X_v-vA&s", width=200) # Opcional: Link a logo
        st.sidebar.header("Filtros Globales")
        
        sel_sucursal = st.sidebar.multiselect("Sucursales:", options=df["Sucursal"].unique(), default=df["Sucursal"].unique())
        sel_mes = st.sidebar.multiselect("Meses:", options=df["Mes"].unique(), default=df["Mes"].unique())
        
        # Filtrar DF principal
        df_filt = df.query("Sucursal == @sel_sucursal & Mes == @sel_mes")

        # --- TABS (PESTAÑAS) ---
        tab_resumen, tab_sucursales, tab_clientes, tab_rentabilidad = st.tabs([
            "🏠 Resumen General", 
            "🏢 Análisis de Sucursales", 
            "👤 Clientes y Vendedores", 
            "💰 Top Operaciones"
        ])

        # --- TAB 1: RESUMEN GENERAL ---
        with tab_resumen:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ventas Totales", f"$ {df_filt['Venta Total'].sum():,.0f}")
            col2.metric("Utilidad Total", f"$ {df_filt['Utilidad'].sum():,.0f}")
            col3.metric("% Margen Prom.", f"{df_filt['(%) Utilidad'].mean():.1f}%")
            col4.metric("Operaciones", f"{len(df_filt)}")

            st.subheader("📈 Evolución y Tendencia Mensual (Empresa)")
            # Agrupar por mes para tendencia
            df_tendencia = df_filt.groupby('Mes').sum(numeric_only=True).reset_index()
            # Ordenar meses (esto asume que tu columna Mes es texto, Plotly lo ordena alfabético o puedes usar el campo fecha)
            fig_tend = px.area(df_tendencia, x="Mes", y="Venta Total", title="Tendencia de Venta Total", markers=True)
            st.plotly_chart(fig_tend, use_container_width=True)

        # --- TAB 2: ANÁLISIS DE SUCURSALES ---
        with tab_sucursales:
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("🏆 Ranking de Sucursales")
                ranking_suc = df_filt.groupby("Sucursal").sum(numeric_only=True)[["Venta Total"]].sort_values("Venta Total", ascending=False).reset_index()
                st.plotly_chart(px.bar(ranking_suc, x="Sucursal", y="Venta Total", color="Sucursal", text_auto=True), use_container_width=True)
            
            with c2:
                st.subheader("🔄 Evolución por Sucursal")
                ev_suc = df_filt.groupby(["Mes", "Sucursal"]).sum(numeric_only=True).reset_index()
                st.plotly_chart(px.line(ev_suc, x="Mes", y="Venta Total", color="Sucursal", markers=True), use_container_width=True)

            st.markdown("---")
            st.subheader("🔍 Detalle por Sucursal (Drill-down)")
            suc_pick = st.selectbox("Toca aquí para profundizar en una sucursal:", options=sel_sucursal)
            df_drill = df_filt[df_filt["Sucursal"] == suc_pick]
            
            col_d1, col_d2 = st.columns([1, 2])
            with col_d1:
                st.write(f"**KPIs de {suc_pick}**")
                st.write(f"- Venta: $ {df_drill['Venta Total'].sum():,.0f}")
                st.write(f"- Margen: {df_drill['(%) Utilidad'].mean():.1f}%")
            with col_d2:
                st.write(f"**Vendedores en esta sucursal:**")
                st.dataframe(df_drill.groupby("Corredor").sum(numeric_only=True)[["Venta Total", "Utilidad"]])

        # --- TAB 3: CLIENTES Y VENDEDORES ---
        with tab_clientes:
            st.subheader("🔝 Top 10 Clientes con más compras")
            top_clientes = df_filt.groupby("cliente").sum(numeric_only=True)[["Venta Total"]].nlargest(10, "Venta Total").reset_index()
            st.plotly_chart(px.bar(top_clientes, y="cliente", x="Venta Total", orientation='h', color="Venta Total"), use_container_width=True)

            st.subheader("👨‍💼 Desempeño de Vendedores (Corredores)")
            fig_pie = px.pie(df_filt, values="Venta Total", names="Corredor", hole=0.5, title="Participación en Ventas")
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- TAB 4: TOP OPERACIONES ---
        with tab_rentability:
            st.subheader("💎 Ventas con Mayores Ganancias")
            st.write("Listado de las 20 facturas con más utilidad generada:")
            top_ganancias = df_filt.nlargest(20, "Utilidad")[["fecha", "comprobante", "cliente", "Venta Total", "Utilidad", "(%) Utilidad", "Sucursal"]]
            st.dataframe(top_ganancias.style.format({"Venta Total": "$ {:,.0f}", "Utilidad": "$ {:,.0f}"}), use_container_width=True)

            st.subheader("⚠️ Operaciones con Margen Negativo o Bajo")
            alertas = df_filt[df_filt["Utilidad"] < 0]
            if not alertas.empty:
                st.warning(f"Se encontraron {len(alertas)} operaciones con pérdida.")
                st.dataframe(alertas)
            else:
                st.success("No se detectaron ventas con pérdida en el periodo seleccionado.")

        # --- EXPORTACIÓN ---
        st.sidebar.markdown("---")
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filt.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Descargar Datos Filtrados", data=buffer.getvalue(), file_name="reporte_filtrado.xlsx")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        st.info("Asegúrate de que el archivo 'reporte_repuestos_mostrador.xlsx' esté en tu repositorio de GitHub.")
