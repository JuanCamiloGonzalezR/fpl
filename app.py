import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Planeador Financiero & Caja")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .metric-container { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .profit { color: green; }
    .loss { color: red; }
    .small-text { font-size: 12px; color: #666; margin-top: -10px; margin-bottom: 20px; }
    .warning-box { background-color: #ffecd1; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800; }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL: SUPUESTOS GLOBALES ---
st.sidebar.header("⚙️ Configuración Global")

# 1. Factores Económicos
currency = st.sidebar.text_input("Moneda", value="$")
carga_prestacional = st.sidebar.slider(
    "Carga Prestacional (Labor Burden)", 
    1.0, 2.0, 1.52, 0.01,
    help="Multiplicador sobre el salario base para incluir salud, pensión, primas, etc."
)

st.sidebar.markdown("---")

# 2. Configuración de Flujo de Caja (NUEVO)
st.sidebar.subheader("⏳ Ciclo de Caja (Cash Flow)")
dias_pago_proveedor = st.sidebar.slider("Días Crédito Proveedores", 0, 90, 0, help="¿Cuántos días te dan tus proveedores para pagar los insumos? (0 = Contado)")

st.sidebar.markdown("---")

# 3. Costos HQ
st.sidebar.subheader("🏢 Costos HQ & Planta")
# Nómina
salario_gerente_gen = st.sidebar.number_input("Salario G. General", 8000000, step=500000)
salario_gerente_ops = st.sidebar.number_input("Salario G. Ops", 6000000, step=500000)
salario_dir_prod = st.sidebar.number_input("Salario Dir. Producción", 5000000, step=500000)
num_asistentes = st.sidebar.number_input("Cant. Asistentes Prod.", 3)
salario_asistente = st.sidebar.number_input("Salario Asistente", 1800000, step=100000)
# Fijos
arriendo_planta = st.sidebar.number_input("Arriendo Planta", 4000000, step=500000)
servicios_planta = st.sidebar.number_input("Servicios Planta", 1500000, step=100000)
otros_gastos = st.sidebar.number_input("Otros Gastos Admin", 1000000, step=100000)

nomina_admin_total = (salario_gerente_gen + salario_gerente_ops + salario_dir_prod + (num_asistentes * salario_asistente)) * carga_prestacional
gastos_fijos_hq = arriendo_planta + servicios_planta + otros_gastos
total_corporate_cost = nomina_admin_total + gastos_fijos_hq

st.sidebar.metric("Gasto Fijo Mensual HQ", f"{currency}{total_corporate_cost:,.0f}")

# --- LÓGICA PRINCIPAL ---

st.title("📊 Simulador P&L + Necesidad de Caja")
st.markdown("Ahora incluimos el **Costo de Venta (COGS)** y el impacto del **Flujo de Caja** por tiempos de pago.")

results = []

tab1, tab2, tab3, tab4 = st.tabs(["📍 Tienda Cedritos", "📍 Tienda Villas", "🛒 Tienda Virtual", "🤝 Canal B2B"])

def render_unit_inputs(key_suffix, title, default_rent, default_rev, default_margin, default_days_receivable, sunday_op_default):
    st.subheader(f"Unit: {title}")
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("##### 💰 Ventas & Margen")
        revenue = st.slider(f"Ventas Mes ({title})", 0, default_rev*3, default_rev, 500000, key=f"rev_{key_suffix}")
        margin_pct = st.slider(f"Margen Bruto % ({title})", 0.1, 0.9, default_margin, 0.05, key=f"mar_{key_suffix}", help="Si vendes a 100 y te cuesta 50, tu margen es 50%.")
    
    with c2:
        st.markdown("##### ⏳ Flujo de Caja")
        dias_cartera = st.number_input(f"Días Cobro Clientes ({title})", value=default_days_receivable, step=15, key=f"dias_{key_suffix}", help="0 = Efectivo inmediato. 45 = Pagan a 45 días.")
        
    with c3:
        st.markdown("##### 🏗️ Costos Fijos")
        rent = st.number_input(f"Arriendo ({title})", value=default_rent, step=100000, key=f"rent_{key_suffix}")
        utilities = st.number_input(f"Servicios/Ads ({title})", value=500000, step=50000, key=f"util_{key_suffix}")
        
    with c4:
        st.markdown("##### 👥 Nómina")
        headcount = st.number_input(f"Empleados ({title})", value=2, step=1, key=f"hc_{key_suffix}")
        role_salary = st.number_input(f"Salario Base ({title})", value=1300000, step=50000, key=f"sal_{key_suffix}")
        sunday_op = st.checkbox("Domingo a Domingo", value=sunday_op_default, key=f"sun_{key_suffix}")
        multiplier = 1.2 if sunday_op else 1.0
        
    # --- CÁLCULOS P&L ---
    cogs = revenue * (1 - margin_pct) # Costo de la mercancía
    gross_profit = revenue - cogs     # Utilidad Bruta
    
    labor_cost = headcount * role_salary * carga_prestacional * multiplier
    opex = rent + utilities + labor_cost
    
    net_profit = gross_profit - opex
    
    # --- CÁLCULOS DE CAJA (Working Capital) ---
    # Dinero atrapado en cuentas por cobrar (Lo que vendiste y no te han pagado)
    ar_cash_trap = (revenue / 30) * dias_cartera 
    
    # Dinero financiado por proveedores (Lo que compraste y no has pagado)
    ap_financing = (cogs / 30) * dias_pago_proveedor
    
    # Necesidad Neta de Capital de Trabajo para esta unidad
    working_capital_need = ar_cash_trap - ap_financing

    return {
        "Unidad": title,
        "Ingresos": revenue,
        "COGS (Costo Venta)": cogs,
        "Utilidad Bruta": gross_profit,
        "Gastos Operativos": opex,
        "Utilidad Operativa": net_profit,
        "Necesidad Caja": working_capital_need
    }

# --- RENDERIZAR UNIDADES ---
# Nota: B2B tiene margen más bajo (ej. 40%) y días de cobro altos (45). Tiendas margen alto (55%) y cobro 0.

with tab1:
    cedritos = render_unit_inputs("ced", "Tienda Cedritos", 3000000, 15000000, 0.55, 0, True)
    results.append(cedritos)

with tab2:
    villas = render_unit_inputs("vil", "Tienda Villas", 2500000, 12000000, 0.55, 0, True)
    results.append(villas)

with tab3:
    virtual = render_unit_inputs("virt", "Tienda Virtual", 1000000, 8000000, 0.50, 5, False) # 5 días asumiendo pasarela de pagos
    results.append(virtual)

with tab4:
    b2b = render_unit_inputs("b2b", "Canal B2B", 0, 20000000, 0.40, 45, False)
    results.append(b2b)

# --- CONSOLIDADO ---
df = pd.DataFrame(results)
st.markdown("---")

# Totales P&L
total_revenue = df["Ingresos"].sum()
total_cogs = df["COGS (Costo Venta)"].sum()
total_gross = total_revenue - total_cogs
total_opex_units = df["Gastos Operativos"].sum()
net_profit_final = total_gross - total_opex_units - total_corporate_cost

# Totales Caja
total_working_capital = df["Necesidad Caja"].sum()

# --- SCORECARD ---
st.header("🏁 Resultados Estratégicos")

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric("Ventas Totales", f"{currency}{total_revenue:,.0f}")
    st.markdown("**Salud de Ventas**")

with kpi2:
    st.metric("Utilidad Neta (P&L)", f"{currency}{net_profit_final:,.0f}", 
              delta_color="normal" if net_profit_final > 0 else "inverse", delta="Ganancia Contable")
    st.markdown(f"Margen Neto: {((net_profit_final/total_revenue)*100) if total_revenue else 0:.1f}%")

with kpi3:
    # Esta es la métrica clave de caja
    st.metric("Capital de Trabajo Requerido", f"{currency}{total_working_capital:,.0f}", delta="Dinero Congelado", delta_color="off")
    st.markdown("**⚠️ Dinero que necesitas tener en el banco para financiar la operación (Cartera - Proveedores).**")

# --- ANÁLISIS ---

col_chart, col_details = st.columns([2, 1])

with col_chart:
    st.subheader("Cascada de Rentabilidad Real")
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "total", "relative", "relative", "total"],
        x = ["Ventas", "Costo Producto (COGS)", "Utilidad Bruta", "Gastos Tiendas", "Gastos HQ", "Utilidad Neta"],
        y = [total_revenue, -total_cogs, total_gross, -total_opex_units, -total_corporate_cost, net_profit_final],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#ef5350"}},
        increasing = {"marker":{"color":"#66bb6a"}},
        totals = {"marker":{"color":"#42a5f5"}}
    ))
    st.plotly_chart(fig, use_container_width=True)

with col_details:
    st.markdown("### 💡 Análisis de Caja")
    if total_working_capital > 0:
        st.warning(f"""
        **Alerta de Liquidez:**
        Para sostener estas ventas, necesitas tener **{currency}{total_working_capital:,.0f}** en capital de trabajo.
        
        Esto sucede porque B2B paga a 45 días, pero tú pagas nómina y proveedores antes.
        """)
        st.markdown("**Sugerencias:**")
        st.markdown("- Negociar días de crédito con proveedores (Slider lateral).")
        st.markdown("- Factorar facturas B2B.")
    else:
        st.success("Tu ciclo de caja es saludable. Cobras más rápido de lo que pagas.")

# --- TABLA DETALLE ---
with st.expander("Ver Detalle Numérico por Unidad"):
    st.dataframe(df.style.format(f"{currency}{{:.0f}}"))
