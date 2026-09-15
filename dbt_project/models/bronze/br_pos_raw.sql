{{ config(materialized='view') }}

select
    receipt_no,
    sale_datetime,
    loyalty_card_no,
    store_location,
    country,
    item_code,
    department,
    qty,
    item_price,
    tender_type,
    register_no,
    cashier_id,
    current_timestamp as _loaded_at
from {{ ref('raw_pos_sales') }}
