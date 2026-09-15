with conformed_sales as (
    select * from {{ ref('slv_conformed_sales') }}
)

select
    -- Generate unique sales surrogate key
    md5(concat(order_id, '_', product_id, '_', sales_channel)) as sales_key,
    order_id,
    sales_channel,
    order_date,
    transaction_timestamp,
    customer_id,
    product_id,
    category,
    country,
    quantity,
    unit_price,
    total_amount,
    payment_method,
    order_status,
    platform
from conformed_sales
