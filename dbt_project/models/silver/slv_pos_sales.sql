with deduplicated as (
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
        _loaded_at,
        row_number() over (
            partition by receipt_no
            order by sale_datetime desc, _loaded_at desc
        ) as row_num
    from {{ ref('br_pos_raw') }}
),

cleaned as (
    select
        receipt_no as order_id,
        cast(sale_datetime as timestamp) as transaction_timestamp,
        cast(sale_datetime as date) as order_date,
        coalesce(loyalty_card_no, 'WALK-IN') as customer_id,
        'In-Store Customer' as customer_name,
        upper(trim(country)) as country,
        item_code as product_id,
        department as category,
        cast(qty as integer) as quantity,
        cast(item_price as numeric(10, 2)) as unit_price,
        cast(round((qty * item_price)::numeric, 2) as numeric(10, 2)) as total_amount,
        case
            when tender_type = 'Card' then 'Credit Card'
            else tender_type
        end as payment_method,
        'Completed' as order_status,
        'Physical POS' as platform,
        store_location,
        register_no,
        cashier_id,
        'POS' as sales_channel,
        current_timestamp as _transformed_at
    from deduplicated
    where row_num = 1
      -- Data quality filters: remove injected anomalies
      and cast(sale_datetime as timestamp) <= current_timestamp
      and qty > 0
      and item_price > 0
      and country != 'XX'
)

select * from cleaned
