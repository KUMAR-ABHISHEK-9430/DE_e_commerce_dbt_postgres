-- Singular Data Test:
-- Total sales amount in fct_sales must always be strictly greater than 0.
-- In dbt, if this query returns any rows, the test fails.

select
    sales_key,
    order_id,
    sales_channel,
    total_amount
from {{ ref('fct_sales') }}
where total_amount <= 0
