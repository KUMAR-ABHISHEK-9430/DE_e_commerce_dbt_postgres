{{ config(materialized='view') }}

select
    order_id,
    order_date,
    customer_id,
    customer_name,
    country,
    product_id,
    category,
    quantity,
    unit_price,
    payment_method,
    order_status,
    platform,
    current_timestamp as _loaded_at
from {{ ref('raw_web_sales') }}