with web_sales as (
    select
        order_id,
        order_date,
        transaction_timestamp,
        customer_id,
        customer_name,
        country,
        product_id,
        category,
        quantity,
        unit_price,
        total_amount,
        payment_method,
        order_status,
        platform,
        sales_channel,
        _transformed_at
    from {{ ref('slv_ecommerce_sales') }}
),

pos_sales as (
    select
        order_id,
        order_date,
        transaction_timestamp,
        customer_id,
        customer_name,
        country,
        product_id,
        category,
        quantity,
        unit_price,
        total_amount,
        payment_method,
        order_status,
        platform,
        sales_channel,
        _transformed_at
    from {{ ref('slv_pos_sales') }}
),

unified as (
    select * from web_sales
    union all
    select * from pos_sales
)

select * from unified
