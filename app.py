import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Strategic Financial Planner")

# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .metric-container { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .profit { color: green; }
    .loss { color: red; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: GLOBAL ASSUMPTIONS ---
st.sidebar.header("🏢 HQ & Global Assumptions")

# 1. Economic Factors
currency = st.sidebar.text_input("Currency Symbol", value="$")
# Vital for Colombia: Prestaciones usually add ~52% to base salary
labor_burden = st.sidebar.slider(
    "Labor Burden Multiplier (Prestaciones)", 
    min_value=1.0, 
    max_value=2.0, 
    value=1.52, 
    step=0.01,
    help="1.52 means for every $1 in salary, the company pays $1.52 (Tax, Health, Pension)."
)

st.sidebar.markdown("---")

# 2. Corporate Overhead (The Cost of doing business)
st.sidebar.subheader("Corporate Overhead")
acct_cost = st.sidebar.number_input("Accountant/Legal (Monthly)", value=2000000, step=100000)
admin_count = st.sidebar.number_input("HQ Admin Headcount", value=1, step=1)
admin_salary = st.sidebar.number_input("HQ Admin Base Salary", value=3000000, step=100000)

total_corporate_cost = acct_cost + (admin_count * admin_salary * labor_burden)
st.sidebar.metric("Total HQ Monthly Burn", f"{currency}{total_corporate_cost:,.0f}")

st.sidebar.markdown("---")
st.sidebar.info("Adjust the tabs on the main screen to configure each business unit.")

# --- MAIN APP LOGIC ---

st.title("📊 Strategic Scenario Planner")
st.markdown("Adjust the inputs below to simulate the Monthly and Yearly P&L for the entire operation.")

# Container for the Business Units
# We use a dictionary to store the results of each unit to aggregate later
results = []

# Create Tabs for clarity
tab1, tab2, tab3, tab4 = st.tabs(["📍 Tienda Cedritos", "📍 Tienda Villas", "🛒 Tienda Virtual", "🤝 B2B"])

def render_unit_inputs(key_suffix, title, default_rent, default_rev, sunday_op_default):
    """Helper function to render inputs for a standard business unit"""
    st.subheader(f"{title} Assumptions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💰 Revenue**")
        revenue = st.slider(f"Monthly Revenue ({title})", 
                            min_value=0, 
                            max_value=default_rev*3, 
                            value=default_rev, 
                            step=500000, 
                            key=f"rev_{key_suffix}")
    
    with col2:
        st.markdown("**🏗️ Fixed Costs**")
        rent = st.number_input(f"Rent ({title})", value=default_rent, step=100000, key=f"rent_{key_suffix}")
        utilities = st.number_input(f"Utilities/Ads ({title})", value=500000, step=50000, key=f"util_{key_suffix}")
        
    with col3:
        st.markdown("**👥 Staffing**")
        headcount = st.number_input(f"Headcount ({title})", value=2, step=1, key=f"hc_{key_suffix}")
        role_salary = st.number_input(f"Avg Base Salary ({title})", value=1300000, step=50000, key=f"sal_{key_suffix}")
        
        # Sunday Operation Logic
        sunday_op = st.checkbox("Sunday-to-Sunday Operation?", value=sunday_op_default, key=f"sun_{key_suffix}")
        sunday_multiplier = 1.2 if sunday_op else 1.0 # Adds 20% to labor cost if Sunday ops are active
        
    # Calculation for this unit
    total_labor = headcount * role_salary * labor_burden * sunday_multiplier
    total_expenses = rent + utilities + total_labor
    net_profit = revenue - total_expenses
    
    # Return data dictionary
    return {
        "Unit": title,
        "Revenue": revenue,
        "Rent": rent,
        "Utilities": utilities,
        "Labor": total_labor,
        "Total Expenses": total_expenses,
        "Net Profit": net_profit
    }

# --- RENDER TABS ---

with tab1:
    cedritos = render_unit_inputs("ced", "Tienda Cedritos", default_rent=3000000, default_rev=15000000, sunday_op_default=True)
    results.append(cedritos)

with tab2:
    villas = render_unit_inputs("vil", "Tienda Villas", default_rent=2500000, default_rev=12000000, sunday_op_default=True)
    results.append(villas)

with tab3:
    # Virtual often has higher "Utilities" due to Ads, so we default higher there
    virtual = render_unit_inputs("virt", "Tienda Virtual", default_rent=1000000, default_rev=8000000, sunday_op_default=False)
    results.append(virtual)

with tab4:
    # B2B usually has 0 Rent (shared) and No Sunday Ops
    b2b = render_unit_inputs("b2b", "B2B Channel", default_rent=0, default_rev=20000000, sunday_op_default=False)
    results.append(b2b)

# --- AGGREGATION & DISPLAY ---

st.markdown("---")

# 1. Data Processing
df = pd.DataFrame(results)
total_revenue = df["Revenue"].sum()
total_unit_expenses = df["Total Expenses"].sum()
gross_profit = total_revenue - total_unit_expenses
net_profit_final = gross_profit - total_corporate_cost

# 2. Scorecard (Top Level Metrics)
st.header("🏁 Consolidated Results")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(label="Total Monthly Revenue", value=f"{currency}{total_revenue:,.0f}")
with m2:
    st.metric(label="Op. Expenses (Units)", value=f"{currency}{total_unit_expenses:,.0f}", delta="-")
with m3:
    st.metric(label="HQ Overhead", value=f"{currency}{total_corporate_cost:,.0f}", delta="-")
with m4:
    st.metric(label="💰 NET PROFIT (Monthly)", 
              value=f"{currency}{net_profit_final:,.0f}", 
              delta_color="normal" if net_profit_final >= 0 else "inverse",
              delta=f"Yearly: {currency}{net_profit_final*12:,.0f}")

# 3. Visualizations
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Profitability by Business Unit")
    # Bar chart of Revenue vs Expenses per unit
    fig_bar = go.Figure(data=[
        go.Bar(name='Revenue', x=df['Unit'], y=df['Revenue'], marker_color='#2ecc71'),
        go.Bar(name='Total Cost', x=df['Unit'], y=df['Total Expenses'], marker_color='#e74c3c')
    ])
    fig_bar.update_layout(barmode='group', height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.subheader("Waterfall P&L Breakdown")
    # Waterfall chart showing how we get from Revenue to Net Profit
    fig_waterfall = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["Total Revenue", "Unit Fixed Costs", "Unit Labor", "HQ Overhead", "Net Profit"],
        textposition = "outside",
        y = [
            total_revenue, 
            -(df['Rent'].sum() + df['Utilities'].sum()), 
            -df['Labor'].sum(), 
            -total_corporate_cost, 
            net_profit_final
        ],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_waterfall.update_layout(height=400)
    st.plotly_chart(fig_waterfall, use_container_width=True)

# 4. Detailed Table
with st.expander("🔎 View Detailed Data Table"):
    # Add a row for HQ
    df_display = df.copy()
    df_display.loc[len(df_display)] = ["HEADQUARTERS", 0, 0, acct_cost, (admin_count * admin_salary * labor_burden), total_corporate_cost, -total_corporate_cost]
    st.dataframe(df_display.style.format(f"{currency}{{:.0f}}"))