import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Omnichannel Retail Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# Database Connection Helper
@st.cache_resource
def get_db_engine():
    user = os.getenv("POSTGRES_USER", "abhishek")
    password = os.getenv("POSTGRES_PASSWORD", "pass@123")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", "5433"))
    db = os.getenv("POSTGRES_DB", "e_comm")
    
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=db,
    )
    return create_engine(url)


# Data Fetchers
@st.cache_data(ttl=60)
def load_daily_kpis():
    engine = get_db_engine()
    query = """
        SELECT
            order_date,
            sales_channel,
            country,
            total_orders,
            total_unique_customers,
            total_units_sold,
            total_revenue,
            avg_order_value
        FROM dev_schema.gold_daily_channel_performance
        ORDER BY order_date ASC;
    """
    return pd.read_sql(query, engine)


@st.cache_data(ttl=60)
def load_customer_tiers():
    engine = get_db_engine()
    query = """
        SELECT
            customer_tier,
            preferred_channel,
            COUNT(*) AS customer_count,
            SUM(lifetime_spend) AS total_spend,
            ROUND(AVG(lifetime_spend), 2) AS avg_spend
        FROM dev_schema.dim_customers
        GROUP BY customer_tier, preferred_channel;
    """
    return pd.read_sql(query, engine)


@st.cache_data(ttl=60)
def load_product_performance():
    engine = get_db_engine()
    query = """
        SELECT
            product_id,
            category,
            avg_unit_price,
            total_units_sold,
            total_revenue,
            total_orders
        FROM dev_schema.dim_products
        ORDER BY total_revenue DESC;
    """
    return pd.read_sql(query, engine)


# App Header
st.title("🛒 Omnichannel E-Commerce & POS Analytics Dashboard")
st.markdown("Direct BI layer connected to PostgreSQL **Gold Layer** transformed by **dbt Core**.")

try:
    df_daily = load_daily_kpis()
    df_customers = load_customer_tiers()
    df_products = load_product_performance()
except Exception as e:
    st.error(f"Failed to connect to PostgreSQL. Is the database container running? Error: {e}")
    st.stop()

# Sidebar Filters
st.sidebar.header("🔍 Dashboard Filters")

channel_options = ["All"] + list(df_daily["sales_channel"].unique())
selected_channel = st.sidebar.selectbox("Sales Channel", channel_options)

countries = ["All"] + list(df_daily["country"].unique())
selected_country = st.sidebar.selectbox("Country", countries)

# Filter daily dataframe
filtered_daily = df_daily.copy()
if selected_channel != "All":
    filtered_daily = filtered_daily[filtered_daily["sales_channel"] == selected_channel]
if selected_country != "All":
    filtered_daily = filtered_daily[filtered_daily["country"] == selected_country]

# Executive KPI Metrics Row
st.markdown("### 📊 Executive KPIs")
col1, col2, col3, col4 = st.columns(4)

total_revenue = filtered_daily["total_revenue"].sum()
total_orders = filtered_daily["total_orders"].sum()
total_units = filtered_daily["total_units_sold"].sum()
aov = total_revenue / total_orders if total_orders > 0 else 0

with col1:
    st.metric("Total Revenue", f"${total_revenue:,.2f}")
with col2:
    st.metric("Total Orders", f"{total_orders:,}")
with col3:
    st.metric("Average Order Value (AOV)", f"${aov:,.2f}")
with col4:
    st.metric("Units Sold", f"{total_units:,}")

st.markdown("---")

# Visualizations Row 1: Trends & Channel Comparison
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("📈 Revenue Over Time (By Channel)")
    fig_trend = px.line(
        filtered_daily,
        x="order_date",
        y="total_revenue",
        color="sales_channel",
        labels={"total_revenue": "Revenue ($)", "order_date": "Order Date", "sales_channel": "Channel"},
        color_discrete_map={"WEB": "#2563EB", "POS": "#10B981"},
        markers=True
    )
    fig_trend.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_trend, use_container_width=True)

with row1_col2:
    st.subheader("🛍️ Revenue by Product Category")
    cat_summary = df_products.groupby("category", as_index=False).agg({
        "total_revenue": "sum",
        "total_units_sold": "sum"
    }).sort_values(by="total_revenue", ascending=False)

    fig_cat = px.bar(
        cat_summary,
        x="total_revenue",
        y="category",
        orientation="h",
        labels={"total_revenue": "Gross Revenue ($)", "category": "Category"},
        color="total_revenue",
        color_continuous_scale="Blues"
    )
    fig_cat.update_layout(yaxis={'categoryorder': 'total ascending'}, coloraxis_showscale=False)
    st.plotly_chart(fig_cat, use_container_width=True)

# Visualizations Row 2: Customers & Geographic Distribution
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("👥 Customer Tier Segmentation")
    tier_summary = df_customers.groupby("customer_tier", as_index=False)["customer_count"].sum()
    fig_pie = px.pie(
        tier_summary,
        names="customer_tier",
        values="customer_count",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with row2_col2:
    st.subheader("🌍 Regional Revenue Distribution")
    country_summary = df_daily.groupby("country", as_index=False)["total_revenue"].sum().sort_values(by="total_revenue", ascending=False)
    fig_geo = px.bar(
        country_summary,
        x="country",
        y="total_revenue",
        labels={"country": "Country Code", "total_revenue": "Revenue ($)"},
        color="country",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_geo.update_layout(showlegend=False)
    st.plotly_chart(fig_geo, use_container_width=True)

# Data Table Inspection
with st.expander("🔎 View Top 10 Best Selling Products (Gold Layer)"):
    st.dataframe(df_products.head(10), use_container_width=True)
