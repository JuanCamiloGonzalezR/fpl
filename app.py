import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Planeador Financiero Estratégico")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .metric-container { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .profit { color: green; }
    .loss { color: red; }
    .small-text { font-size: 12px; color: #666; margin-top: -15px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL: COSTOS GLOBALES ---
st.sidebar.header("🏢 Costos Globales y Administrativos")

# 1. Factores Económicos
currency = st.sidebar.text_input("Símbolo de Moneda", value="$")
carga_prestacional = st.sidebar.slider(
    "Factor Prestacional (Carga Laboral)", 
    min_value=1.0, 
    max_value=2.0, 
    value=1.52, 
    step=0.01,
    help="1.52 significa que por cada $1 de salario, la empresa paga $1.52 (Salud, Pensión, Parafiscales)."
)

st.sidebar.markdown("---")

# 2. Nómina Administrativa y Producción
st.sidebar.subheader("Nómina Estratégica")
salario_gerente_gen = st.sidebar.number_input("Salario Gerente General", value=8000000, step=500000)
salario_gerente_ops = st.sidebar.number_input("Salario Gerente Operaciones", value=6000000, step=500000)
salario_dir_prod = st.sidebar.number_input("Salario Director Producción", value=5000000, step=500000)

st.sidebar.subheader("Equipo de Producción")
num_asistentes = st.sidebar.number_input("Cant. Asistentes Producción", value=3, step=1)
salario_asistente = st.sidebar.number_input("Salario Promedio Asistente", value=1800000, step=100000)

# 3. Costos Fijos Centrales
st.sidebar.subheader("Gastos Fijos Centrales")
arriendo_planta = st.sidebar.number_input("Arriendo Planta/Oficina", value=4000000, step=500000)
servicios_planta = st.sidebar.number_input("Servicios Planta", value=1500000, step=100000)
otros_gastos = st.sidebar.number_input("Otros Gastos Administrativos", value=1000000, step=100000)

# CÁLCULO TOTAL GASTOS CENTRALES
# Nómina cargada con factor prestacional
nomina_admin_total = (salario_gerente_gen + salario_gerente_ops + salario_dir_prod + (num_asistentes * salario_asistente)) * carga_prestacional
gastos_fijos_total = arriendo_planta + servicios_planta + otros_gastos
total_corporate_cost = nomina_admin_total + gastos_fijos_total

st.sidebar.metric("Gasto Mensual HQ (Burn Rate)", f"{currency}{total_corporate_cost:,.0f}")
st.sidebar.markdown("---")

# --- LÓGICA PRINCIPAL ---

st.title("📊 Simulador Financiero Estratégico")
st.markdown("Ajusta los controles para visualizar el P&L (Ganancias y Pérdidas) Mensual y Anual.")

# Contenedor de resultados
results = []

# Pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📍 Tienda Cedritos", "📍 Tienda Villas", "🛒 Tienda Virtual", "🤝 Canal B2B"])

def render_unit_inputs(key_suffix, title, default_rent, default_rev, sunday_op_default):
    st.subheader(f"Supuestos para {title}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💰 Ingresos**")
        revenue = st.slider(f"Ventas Mensuales ({title})", 
                            min_value=0, 
                            max_value=default_rev*3, 
                            value=default_rev, 
                            step=500000, 
                            key=f"rev_{key_suffix}")
    
    with col2:
        st.markdown("**🏗️ Costos Fijos**")
        rent = st.number_input(f"Arriendo Local ({title})", value=default_rent, step=100000, key=f"rent_{key_suffix}")
        utilities = st.number_input(f"Servicios/Publicidad ({title})", value=500000, step=50000, key=f"util_{key_suffix}")
        
    with col3:
        st.markdown("**👥 Personal Operativo**")
        headcount = st.number_input(f"Cantidad Empleados ({title})", value=2, step=1, key=f"hc_{key_suffix}")
        role_salary = st.number_input(f"Salario Base Promedio ({title})", value=1300000, step=50000, key=f"sal_{key_suffix}")
        
        sunday_op = st.checkbox("¿Operación Domingo a Domingo?", value=sunday_op_default, key=f"sun_{key_suffix}")
        sunday_multiplier = 1.2 if sunday_op else 1.0 
        
    # Cálculos
    total_labor = headcount * role_salary * carga_prestacional * sunday_multiplier
    total_expenses = rent + utilities + total_labor
    net_profit = revenue - total_expenses
    
    return {
        "Unidad de Negocio": title,
        "Ingresos": revenue,
        "Arriendo": rent,
        "Servicios/Ads": utilities,
        "Nómina": total_labor,
        "Total Gastos": total_expenses,
        "Utilidad Operativa": net_profit
    }

# --- RENDERIZAR PESTAÑAS ---
with tab1:
    cedritos = render_unit_inputs("ced", "Tienda Cedritos", 3000000, 15000000, True)
    results.append(cedritos)

with tab2:
    villas = render_unit_inputs("vil", "Tienda Villas", 2500000, 12000000, True)
    results.append(villas)

with tab3:
    virtual = render_unit_inputs("virt", "Tienda Virtual", 1000000, 8000000, False)
    results.append(virtual)

with tab4:
    b2b = render_unit_inputs("b2b", "Canal B2B", 0, 20000000, False)
    results.append(b2b)

# --- CONSOLIDACIÓN ---

st.markdown("---")
df = pd.DataFrame(results)

# Totales
total_revenue = df["Ingresos"].sum()
total_unit_expenses = df["Total Gastos"].sum()
gross_profit = total_revenue - total_unit_expenses
net_profit_final = gross_profit - total_corporate_cost

# --- SCORECARD (METRICAS CON CONTEXTO) ---
st.header("🏁 Resultados Consolidados")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(label="Ingresos Totales (Mes)", value=f"{currency}{total_revenue:,.0f}")
    st.markdown("<p class='small-text'>Suma total de ventas proyectadas de todas las unidades.</p>", unsafe_allow_html=True)

with m2:
    st.metric(label="Gastos Operativos (Tiendas)", value=f"{currency}{total_unit_expenses:,.0f}", delta="-")
    st.markdown("<p class='small-text'>Costo directo de operar los puntos (Arriendo + Nómina Local).</p>", unsafe_allow_html=True)

with m3:
    st.metric(label="Gastos Administrativos (HQ)", value=f"{currency}{total_corporate_cost:,.0f}", delta="-")
    st.markdown("<p class='small-text'>Costo de estructura central, gerencia y planta de producción.</p>", unsafe_allow_html=True)

with m4:
    st.metric(label="💰 UTILIDAD NETA (Mes)", 
              value=f"{currency}{net_profit_final:,.0f}", 
              delta_color="normal" if net_profit_final >= 0 else "inverse",
              delta=f"Proyección Año: {currency}{net_profit_final*12:,.0f}")
    st.markdown("<p class='small-text'>Dinero libre después de pagar absolutamente todo.</p>", unsafe_allow_html=True)

# --- VISUALIZACIÓN ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Rentabilidad por Unidad")
    fig_bar = go.Figure(data=[
        go.Bar(name='Ingresos', x=df['Unidad de Negocio'], y=df['Ingresos'], marker_color='#2ecc71'),
        go.Bar(name='Gastos Directos', x=df['Unidad de Negocio'], y=df['Total Gastos'], marker_color='#e74c3c')
    ])
    fig_bar.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.subheader("Cascada de Costos (Waterfall)")
    fig_waterfall = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["Ventas Totales", "Costos Fijos Puntos", "Nómina Puntos", "Gastos HQ/Planta", "Utilidad Neta"],
        textposition = "outside",
        y = [
            total_revenue, 
            -(df['Arriendo'].sum() + df['Servicios/Ads'].sum()), 
            -df['Nómina'].sum(), 
            -total_corporate_cost, 
            net_profit_final
        ],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_waterfall.update_layout(height=400)
    st.plotly_chart(fig_waterfall, use_container_width=True)

# --- TABLA DETALLADA (FIXED ERROR) ---
with st.expander("🔎 Ver Tabla de Datos Detallada"):
    df_display = df.copy()
    # Agregar fila de HQ manualmente para visualización
    df_display.loc[len(df_display)] = ["ADMINISTRACIÓN CENTRAL", 0, arriendo_planta, servicios_planta + otros_gastos, nomina_admin_total, total_corporate_cost, -total_corporate_cost]
    
    # FIX: Aplicar formato solo a columnas numéricas
    numeric_cols = df_display.select_dtypes(include=['number']).columns
    format_dict = {col: f"{currency}{{:.0f}}" for col in numeric_cols}
    
    st.dataframe(df_display.style.format(format_dict))
