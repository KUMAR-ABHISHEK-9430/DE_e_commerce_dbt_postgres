with product_sales as (
    select
        product_id,
        category,
        quantity,
        unit_price,
        total_amount,
        order_id
    from {{ ref('slv_conformed_sales') }}
),

aggregated as (
    select
        product_id,
        max(category) as category,
        min(unit_price) as min_unit_price,
        max(unit_price) as max_unit_price,
        cast(round(avg(unit_price)::numeric, 2) as numeric(10, 2)) as avg_unit_price,
        sum(quantity) as total_units_sold,
        cast(round(sum(total_amount)::numeric, 2) as numeric(10, 2)) as total_revenue,
        count(distinct order_id) as total_orders
    from product_sales
    group by product_id
)

select * from aggregated
