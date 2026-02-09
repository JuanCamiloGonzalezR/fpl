import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(layout="wide", page_title="Planeador Financiero (Unlocked)")

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
st.sidebar.caption("Sin restricciones. Escribe el valor exacto.")

# 1. Factores Económicos
currency = st.sidebar.text_input("Moneda", value="$")
carga_prestacional = st.sidebar.number_input(
    "Carga Prestacional (Factor)", 
    min_value=1.0, 
    value=1.52, 
    step=0.01,
    format="%.2f",
    help="1.52 = 52% de sobrecosto laboral (Salud, Pensión, etc.)"
)

st.sidebar.markdown("---")

# 2. Configuración de Caja Inicial
st.sidebar.subheader("💰 Posición de Caja")
caja_inicial = st.sidebar.number_input("Saldo en Banco HOY", min_value=0, value=20000000, step=100000)
dias_pago_proveedor = st.sidebar.number_input("Días Crédito Proveedores", min_value=0, value=30, step=1)

st.sidebar.markdown("---")

# 3. Costos HQ
st.sidebar.subheader("🏢 Costos HQ & Planta")

# Nómina Admin
col_hq1, col_hq2 = st.sidebar.columns(2)
with col_hq1:
    salario_gerente_gen = st.number_input("Salario G. General", min_value=0, value=8000000, step=100000)
    salario_gerente_ops = st.number_input("Salario G. Ops", min_value=0, value=6000000, step=100000)
with col_hq2:
    salario_dir_prod = st.number_input("Salario Dir. Prod", min_value=0, value=5000000, step=100000)
    num_asistentes = st.number_input("Cant. Asistentes", min_value=0, value=3, step=1)

salario_asistente = st.sidebar.number_input("Salario Promedio Asistente", min_value=0, value=1800000, step=100000)

st.sidebar.markdown("**Gastos Fijos Centrales**")
arriendo_planta = st.sidebar.number_input("Arriendo Planta", min_value=0, value=4000000, step=100000)
servicios_planta = st.sidebar.number_input("Servicios Planta", min_value=0, value=1500000, step=50000)
otros_gastos = st.sidebar.number_input("Otros Gastos Admin", min_value=0, value=1000000, step=50000)

nomina_admin_total = (salario_gerente_gen + salario_gerente_ops + salario_dir_prod + (num_asistentes * salario_asistente)) * carga_prestacional
gastos_fijos_hq = arriendo_planta + servicios_planta + otros_gastos
total_corporate_cost = nomina_admin_total + gastos_fijos_hq

st.sidebar.metric("Gasto Fijo Mensual HQ", f"{currency}{total_corporate_cost:,.0f}")

# --- LÓGICA PRINCIPAL ---

st.title("📊 Simulador Financiero (Modo Libre)")

results = []

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Tienda Cedritos", "📍 Tienda Villas", "🛒 Tienda Virtual", "🤝 Canal B2B", "📅 Proyección Anual"])

def render_unit_inputs(key_suffix, title, default_rent, default_rev, default_margin, default_days_receivable, sunday_op_default):
    with st.container():
        st.subheader(f"Unidad: {title}")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            # CAMBIO: Number Input en vez de Slider para libertad total
            revenue = st.number_input(f"Ventas Mes ({title})", min_value=0, value=default_rev, step=100000, key=f"rev_{key_suffix}")
            margin_pct = st.number_input(f"Margen Bruto % (0.5 = 50%)", min_value=0.0, max_value=1.0, value=default_margin, step=0.01, key=f"mar_{key_suffix}")
        
        with c2:
            dias_cartera = st.number_input(f"Días Cobro ({title})", min_value=0, value=default_days_receivable, step=1, key=f"dias_{key_suffix}")
            
        with c3:
            rent = st.number_input(f"Arriendo ({title})", min_value=0, value=default_rent, step=100000, key=f"rent_{key_suffix}")
            utilities = st.number_input(f"Servicios/Ads ({title})", min_value=0, value=500000, step=10000, key=f"util_{key_suffix}")
            
        with c4:
            headcount = st.number_input(f"Empleados ({title})", min_value=0, value=2, step=1, key=f"hc_{key_suffix}")
            role_salary = st.number_input(f"Salario Base ({title})", min_value=0, value=1300000, step=50000, key=f"sal_{key_suffix}")
            sunday_op = st.checkbox("Domingo a Domingo", value=sunday_op_default, key=f"sun_{key_suffix}")
            multiplier = 1.2 if sunday_op else 1.0
            
        # --- CÁLCULOS P&L ---
        cogs = revenue * (1 - margin_pct) 
        gross_profit = revenue - cogs
        labor_cost = headcount * role_salary * carga_prestacional * multiplier
        opex = rent + utilities + labor_cost
        net_profit = gross_profit - opex
        
        return {
            "Unidad": title,
            "Ingresos": revenue,
            "COGS": cogs,
            "Utilidad Bruta": gross_profit,
            "Gastos Operativos": opex,
            "Utilidad Operativa": net_profit,
            "Tipo": "B2B" if "B2B" in title else "DTC"
        }

# --- RENDERIZAR UNIDADES ---

with tab1:
    cedritos = render_unit_inputs("ced", "Tienda Cedritos", 3000000, 15000000, 0.55, 0, True)
    results.append(cedritos)

with tab2:
    villas = render_unit_inputs("vil", "Tienda Villas", 2500000, 12000000, 0.55, 0, True)
    results.append(villas)

with tab3:
    virtual = render_unit_inputs("virt", "Tienda Virtual", 1000000, 8000000, 0.50, 5, False)
    results.append(virtual)

with tab4:
    b2b = render_unit_inputs("b2b", "Canal B2B", 0, 20000000, 0.40, 45, False)
    results.append(b2b)

# --- PROCESAMIENTO DE DATOS ---
df_units = pd.DataFrame(results)

# --- TAB 5: LA VISIÓN DE FUTURO (YEARLY CASH MAP) ---
with tab5:
    st.header("🔮 Mapa de Caja: Próximos 12 Meses")
    
    # Toggle para la lógica B2B
    st.markdown("##### Configuración de Proyección")
    b2b_lumpy = st.checkbox("Simular 'Efecto Serrucho' B2B (Entra pago cada 2 meses)", value=True)
    
    # 1. Separar Ingresos DTC vs B2B
    dtc_monthly_rev = df_units[df_units["Tipo"] == "DTC"]["Ingresos"].sum()
    dtc_monthly_cogs = df_units[df_units["Tipo"] == "DTC"]["COGS"].sum()
    
    b2b_monthly_rev_avg = df_units[df_units["Tipo"] == "B2B"]["Ingresos"].sum()
    b2b_monthly_cogs_avg = df_units[df_units["Tipo"] == "B2B"]["COGS"].sum()
    
    total_monthly_opex = df_units["Gastos Operativos"].sum() + total_corporate_cost
    
    # 2. Construir la Proyección de 12 Meses
    months = list(range(1, 13))
    cash_data = []
    
    current_balance = caja_inicial
    
    for m in months:
        # Lógica B2B
        if b2b_lumpy:
            # Meses pares entra doble, meses impares 0
            if m % 2 == 0:
                b2b_cash_in = b2b_monthly_rev_avg * 2
            else:
                b2b_cash_in = 0
        else:
            # Lógica Plana (Promedio)
            b2b_cash_in = b2b_monthly_rev_avg
            
        # Ingreso Total Caja
        total_cash_in = dtc_monthly_rev + b2b_cash_in
        
        # Egresos (Salidas de Caja)
        # Asumimos que pagamos COGS todos los meses
        total_cash_out = total_monthly_opex + dtc_monthly_cogs + b2b_monthly_cogs_avg
        
        net_period = total_cash_in - total_cash_out
        current_balance += net_period
        
        cash_data.append({
            "Mes": f"Mes {m}",
            "Ingreso DTC": dtc_monthly_rev,
            "Ingreso B2B": b2b_cash_in,
            "Total Ingresos": total_cash_in,
            "Total Egresos": total_cash_out,
            "Flujo Neto": net_period,
            "Saldo en Banco": current_balance
        })
        
    df_cash = pd.DataFrame(cash_data)
    
    # 3. Visualización
    col_kpi1, col_kpi2 = st.columns(2)
    min_balance = df_cash["Saldo en Banco"].min()
    final_balance = df_cash["Saldo en Banco"].iloc[-1]
    
    with col_kpi1:
        st.metric("Saldo Final (Mes 12)", f"{currency}{final_balance:,.0f}", 
                 delta="Crecimiento de Caja" if final_balance > caja_inicial else "Destrucción de Caja")
        
    with col_kpi2:
        st.metric("Punto Mínimo de Caja (Valle de la Muerte)", f"{currency}{min_balance:,.0f}",
                 delta_color="off" if min_balance > 0 else "inverse")
        if min_balance < 0:
            st.error(f"⚠️ PELIGRO: Te quedas sin efectivo. Necesitas inyectar capital o crédito.")
        else:
            st.success("✅ Tu caja aguanta la operación todo el año.")

    # Gráfica Combinada
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_cash["Mes"],
        y=df_cash["Flujo Neto"],
        name="Flujo Neto Mensual",
        marker_color=np.where(df_cash["Flujo Neto"] < 0, '#ef5350', '#66bb6a')
    ))
    
    fig.add_trace(go.Scatter(
        x=df_cash["Mes"],
        y=df_cash["Saldo en Banco"],
        name="Saldo Acumulado en Banco",
        mode='lines+markers',
        line=dict(color='#2c3e50', width=4),
        yaxis="y2"
    ))
    
    fig.update_layout(
        title="Mapa de Calor: Flujo Neto vs Saldo en Banco",
        yaxis=dict(title="Flujo Mensual"),
        yaxis2=dict(title="Saldo en Banco", overlaying="y", side="right"),
        legend=dict(x=0, y=1.1, orientation="h"),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla Detalle
    with st.expander("Ver Tabla de Flujo Detallada"):
        numeric_cols = df_cash.select_dtypes(include=['number']).columns
        format_dict = {col: f"{currency}{{:.0f}}" for col in numeric_cols}
        st.dataframe(df_cash.style.format(format_dict))

# --- SCORECARD P&L ---
st.markdown("---")
st.caption("Resumen Rápido P&L (Promedio Mensual Contable)")
cols = st.columns(4)
monthly_profit = df_units["Utilidad Operativa"].sum() - total_corporate_cost
cols[0].metric("Ventas Totales (Avg)", f"{currency}{df_units['Ingresos'].sum():,.0f}")
cols[1].metric("Gastos Totales", f"{currency}{(df_units['Gastos Operativos'].sum() + total_corporate_cost):,.0f}")
cols[2].metric("Utilidad Neta (Avg)", f"{currency}{monthly_profit:,.0f}")
