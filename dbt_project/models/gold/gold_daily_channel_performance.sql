with sales as (
    select * from {{ ref('fct_sales') }}
),

daily_summary as (
    select
        order_date,
        sales_channel,
        country,
        count(distinct order_id) as total_orders,
        count(distinct customer_id) as total_unique_customers,
        sum(quantity) as total_units_sold,
        cast(round(sum(total_amount)::numeric, 2) as numeric(10, 2)) as total_revenue,
        cast(round(avg(total_amount)::numeric, 2) as numeric(10, 2)) as avg_order_value
    from sales
    group by
        order_date,
        sales_channel,
        country
)

select * from daily_summary
order by
    order_date desc,
    sales_channel,
    country
