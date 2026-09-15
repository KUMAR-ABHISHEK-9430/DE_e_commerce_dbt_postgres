import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Load env variables
load_dotenv()

def get_engine():
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

def generate_static_report():
    print("[*] Connecting to PostgreSQL Gold layer...")
    engine = get_engine()

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        print("[!] matplotlib/seaborn not installed. Run: pip install matplotlib seaborn")
        return

    os.makedirs("assets", exist_ok=True)
    sns.set_theme(style="whitegrid")

    # 1. Daily Revenue Trend by Channel
    query_trend = """
        SELECT order_date, sales_channel, SUM(total_revenue) as daily_revenue
        FROM dev_schema.gold_daily_channel_performance
        GROUP BY order_date, sales_channel
        ORDER BY order_date ASC;
    """
    df_trend = pd.read_sql(query_trend, engine)
    df_trend["order_date"] = pd.to_datetime(df_trend["order_date"])

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Omnichannel E-Commerce & Retail POS Analytics (Gold Layer)", fontsize=18, fontweight="bold")

    # Plot 1: Trend
    sns.lineplot(data=df_trend, x="order_date", y="daily_revenue", hue="sales_channel", ax=axes[0, 0], palette=["#2563EB", "#10B981"])
    axes[0, 0].set_title("Revenue Over Time: Web vs In-Store POS", fontweight="bold")
    axes[0, 0].set_ylabel("Revenue ($)")
    axes[0, 0].set_xlabel("Date")

    # Plot 2: Category Revenue
    query_cat = """
        SELECT category, SUM(total_revenue) as revenue
        FROM dev_schema.dim_products
        GROUP BY category
        ORDER BY revenue DESC;
    """
    df_cat = pd.read_sql(query_cat, engine)
    sns.barplot(data=df_cat, x="revenue", y="category", ax=axes[0, 1], palette="Blues_r")
    axes[0, 1].set_title("Gross Revenue by Category", fontweight="bold")
    axes[0, 1].set_xlabel("Revenue ($)")

    # Plot 3: Customer Tier Distribution
    query_tier = """
        SELECT customer_tier, COUNT(*) as count
        FROM dev_schema.dim_customers
        GROUP BY customer_tier;
    """
    df_tier = pd.read_sql(query_tier, engine)
    axes[1, 0].pie(df_tier["count"], labels=df_tier["customer_tier"], autopct="%1.1f%%", colors=sns.color_palette("Set2"))
    axes[1, 0].set_title("Customer Segmentation Tiers", fontweight="bold")

    # Plot 4: Country Revenue
    query_country = """
        SELECT country, SUM(total_revenue) as revenue
        FROM dev_schema.gold_daily_channel_performance
        GROUP BY country
        ORDER BY revenue DESC;
    """
    df_country = pd.read_sql(query_country, engine)
    sns.barplot(data=df_country, x="country", y="revenue", ax=axes[1, 1], palette="crest")
    axes[1, 1].set_title("Regional Sales Distribution (By Country)", fontweight="bold")
    axes[1, 1].set_ylabel("Revenue ($)")

    plt.tight_layout()
    output_path = os.path.join("assets", "analytics_dashboard.png")
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"[+] Static analytics dashboard saved to: {output_path}")

if __name__ == "__main__":
    generate_static_report()
