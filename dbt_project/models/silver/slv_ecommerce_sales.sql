with deduplicated as (
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
        _loaded_at,
        row_number() over (
            partition by order_id
            order by order_date desc, _loaded_at desc
        ) as row_num
    from {{ ref('br_ecommerce_raw') }}
),

cleaned as (
    select
        order_id,
        cast(order_date as date) as order_date,
        cast(order_date as timestamp) as transaction_timestamp,
        coalesce(customer_id, 'CUST-GUEST') as customer_id,
        trim(customer_name) as customer_name,
        upper(trim(country)) as country,
        product_id,
        category,
        cast(quantity as integer) as quantity,
        cast(unit_price as numeric(10, 2)) as unit_price,
        cast(round((quantity * unit_price)::numeric, 2) as numeric(10, 2)) as total_amount,
        payment_method,
        order_status,
        platform,
        'WEB' as sales_channel,
        current_timestamp as _transformed_at
    from deduplicated
    where row_num = 1
      -- Data quality filters: remove injected anomalies
      and cast(order_date as date) <= current_date
      and quantity > 0
      and unit_price > 0
      and country != 'UNKNOWN'
)

select * from cleaned
