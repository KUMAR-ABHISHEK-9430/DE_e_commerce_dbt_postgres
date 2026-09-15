with customer_orders as (
    select
        customer_id,
        customer_name,
        order_id,
        order_date,
        total_amount,
        quantity,
        sales_channel
    from {{ ref('slv_conformed_sales') }}
),

aggregated as (
    select
        customer_id,
        case
            when customer_id = 'CUST-GUEST' then 'Guest Web Shopper'
            when customer_id = 'WALK-IN' then 'Anonymous Walk-in'
            else max(customer_name)
        end as customer_name,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        count(distinct order_id) as total_orders,
        sum(quantity) as total_units_purchased,
        cast(round(sum(total_amount)::numeric, 2) as numeric(10, 2)) as lifetime_spend,
        cast(round(avg(total_amount)::numeric, 2) as numeric(10, 2)) as avg_order_value,
        case
            when count(case when sales_channel = 'WEB' then 1 end) >= count(case when sales_channel = 'POS' then 1 end)
            then 'WEB'
            else 'POS'
        end as preferred_channel,
        case
            when customer_id in ('CUST-GUEST', 'WALK-IN') then 'Anonymous'
            when count(distinct order_id) >= 5 then 'VIP / High Frequency'
            when count(distinct order_id) >= 2 then 'Repeat Customer'
            else 'One-Time Customer'
        end as customer_tier
    from customer_orders
    group by customer_id
)

select * from aggregated
