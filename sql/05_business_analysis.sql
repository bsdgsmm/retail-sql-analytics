WITH completed_lines AS (
    SELECT
        o.order_id,
        o.customer_id,
        oi.quantity,
        oi.quantity * oi.unit_price AS gross_sales,
        oi.quantity * oi.unit_price * oi.discount_pct AS discount_amount,
        oi.quantity * oi.unit_price * (1 - oi.discount_pct) AS net_revenue,
        oi.quantity * p.unit_cost AS cost_of_goods
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    INNER JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.status = 'completed'
),
kpis AS (
    SELECT
        (SELECT count(*) FROM orders) AS orders_placed,
        count(DISTINCT order_id) AS completed_orders,
        count(DISTINCT customer_id) AS active_customers,
        sum(quantity) AS units_sold,
        round(sum(gross_sales), 2) AS gross_sales,
        round(sum(discount_amount), 2) AS discounts,
        round(sum(net_revenue), 2) AS net_revenue,
        round(sum(net_revenue - cost_of_goods), 2) AS gross_profit,
        round(sum(net_revenue - cost_of_goods) * 100 / sum(net_revenue), 1) AS gross_margin_pct,
        round(sum(net_revenue) / count(DISTINCT order_id), 2) AS average_order_value,
        round(sum(quantity) / count(DISTINCT order_id), 2) AS units_per_order,
        round(sum(net_revenue) / count(DISTINCT customer_id), 2) AS revenue_per_customer
    FROM completed_lines
)
UNPIVOT (SELECT COLUMNS(*)::DECIMAL(14, 2) FROM kpis)
ON COLUMNS(*)
INTO NAME metric VALUE value;

SELECT
    p.product_name,
    c.category_name,
    sum(oi.quantity) AS units_sold,
    count(DISTINCT o.order_id) AS orders,
    round(sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS net_revenue,
    round(
        sum(oi.quantity * (oi.unit_price * (1 - oi.discount_pct) - p.unit_cost)) * 100
        / sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)),
        1
    ) AS gross_margin_pct
FROM order_items AS oi
INNER JOIN orders AS o ON o.order_id = oi.order_id
INNER JOIN products AS p ON p.product_id = oi.product_id
INNER JOIN categories AS c ON c.category_id = p.category_id
WHERE o.status = 'completed'
GROUP BY p.product_name, c.category_name
ORDER BY net_revenue DESC
LIMIT 10;

WITH category_lines AS (
    SELECT
        c.category_name,
        o.status,
        oi.quantity * oi.unit_price * (1 - oi.discount_pct) AS net_value,
        oi.quantity * p.unit_cost AS cost_of_goods
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    INNER JOIN products AS p ON p.product_id = oi.product_id
    INNER JOIN categories AS c ON c.category_id = p.category_id
)
SELECT
    category_name,
    round(sum(net_value) FILTER (WHERE status = 'completed'), 2) AS net_revenue,
    round(
        sum(net_value) FILTER (WHERE status = 'completed') * 100
        / sum(sum(net_value) FILTER (WHERE status = 'completed')) OVER (),
        1
    ) AS revenue_share_pct,
    round(
        sum(net_value - cost_of_goods) FILTER (WHERE status = 'completed') * 100
        / sum(net_value) FILTER (WHERE status = 'completed'),
        1
    ) AS gross_margin_pct,
    round(
        sum(net_value) FILTER (WHERE status = 'returned') * 100
        / sum(net_value) FILTER (WHERE status IN ('completed', 'returned')),
        1
    ) AS returned_value_pct
FROM category_lines
GROUP BY category_name
ORDER BY net_revenue DESC;

WITH monthly AS (
    SELECT
        date_trunc('month', o.order_date)::DATE AS month_start,
        count(DISTINCT o.order_id) AS completed_orders,
        count(DISTINCT o.customer_id) AS active_customers,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY month_start
)
SELECT
    strftime(month_start, '%Y-%m') AS month,
    completed_orders,
    active_customers,
    round(net_revenue, 2) AS net_revenue,
    round(net_revenue / completed_orders, 2) AS average_order_value,
    round((net_revenue / lag(net_revenue) OVER (ORDER BY month_start) - 1) * 100, 1) AS mom_growth_pct
FROM monthly
ORDER BY month_start;

WITH customer_activity AS (
    SELECT
        o.customer_id,
        count(DISTINCT o.order_id) AS completed_orders,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue,
        min(o.order_date) AS first_order_date,
        max(o.order_date) AS last_order_date
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id
)
SELECT
    ca.customer_id,
    cu.first_name || ' ' || cu.last_name AS customer_name,
    cu.region,
    ca.completed_orders,
    round(ca.net_revenue, 2) AS net_revenue,
    round(ca.net_revenue / ca.completed_orders, 2) AS average_order_value,
    ca.first_order_date,
    ca.last_order_date
FROM customer_activity AS ca
INNER JOIN customers AS cu ON cu.customer_id = ca.customer_id
ORDER BY ca.completed_orders DESC, ca.net_revenue DESC
LIMIT 10;

WITH customer_orders AS (
    SELECT
        customer_id,
        count(*) AS completed_orders
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    (SELECT count(*) FROM customers) AS registered_customers,
    count(*) AS purchasing_customers,
    count(*) FILTER (WHERE completed_orders = 1) AS one_time_customers,
    count(*) FILTER (WHERE completed_orders >= 2) AS repeat_customers,
    round(count(*) FILTER (WHERE completed_orders >= 2) * 100.0 / count(*), 1) AS repeat_customer_rate_pct,
    round(avg(completed_orders), 2) AS avg_orders_per_purchasing_customer
FROM customer_orders;

WITH customers_by_year AS (
    SELECT DISTINCT
        customer_id,
        year(order_date) AS order_year
    FROM orders
    WHERE status = 'completed'
)
SELECT
    count(*) FILTER (WHERE order_year = 2024) AS customers_2024,
    count(*) FILTER (
        WHERE order_year = 2024
          AND customer_id IN (SELECT customer_id FROM customers_by_year WHERE order_year = 2025)
    ) AS retained_in_2025,
    round(retained_in_2025 * 100.0 / customers_2024, 1) AS retention_rate_pct,
    count(*) FILTER (
        WHERE order_year = 2025
          AND customer_id NOT IN (SELECT customer_id FROM customers_by_year WHERE order_year = 2024)
    ) AS new_customers_2025
FROM customers_by_year;

WITH product_revenue AS (
    SELECT
        oi.product_id,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY oi.product_id
),
cumulative AS (
    SELECT
        product_id,
        net_revenue,
        row_number() OVER (ORDER BY net_revenue DESC, product_id) AS revenue_rank,
        count(*) OVER () AS product_count,
        sum(net_revenue) OVER (ORDER BY net_revenue DESC, product_id) / sum(net_revenue) OVER () AS cumulative_share
    FROM product_revenue
)
SELECT
    max(product_count) AS products_sold,
    min(revenue_rank) FILTER (WHERE cumulative_share >= 0.8) AS products_for_80_pct_revenue,
    round(products_for_80_pct_revenue * 100.0 / products_sold, 1) AS share_of_catalog_pct,
    round(
        sum(net_revenue) FILTER (WHERE revenue_rank <= ceil(product_count * 0.2)) * 100 / sum(net_revenue),
        1
    ) AS top_20_pct_products_revenue_share
FROM cumulative;

WITH order_values AS (
    SELECT
        o.order_id,
        o.customer_id,
        year(o.order_date) AS order_year,
        sum(oi.quantity * oi.unit_price) AS gross_sales,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.order_id, o.customer_id, order_year
),
yearly AS (
    SELECT
        order_year,
        count(*) AS completed_orders,
        count(DISTINCT customer_id) AS active_customers,
        sum(net_revenue) AS net_revenue,
        sum(gross_sales - net_revenue) AS discounts,
        sum(net_revenue) / count(*) AS average_order_value
    FROM order_values
    GROUP BY order_year
)
SELECT
    metric,
    value_2024::DECIMAL(14, 2) AS value_2024,
    value_2025::DECIMAL(14, 2) AS value_2025,
    round((value_2025 / value_2024 - 1) * 100, 1) AS change_pct
FROM (
    SELECT
        unnest(['net_revenue', 'completed_orders', 'active_customers', 'average_order_value', 'discounts']) AS metric,
        unnest([
            max(net_revenue) FILTER (WHERE order_year = 2024),
            max(completed_orders) FILTER (WHERE order_year = 2024),
            max(active_customers) FILTER (WHERE order_year = 2024),
            max(average_order_value) FILTER (WHERE order_year = 2024),
            max(discounts) FILTER (WHERE order_year = 2024)
        ]) AS value_2024,
        unnest([
            max(net_revenue) FILTER (WHERE order_year = 2025),
            max(completed_orders) FILTER (WHERE order_year = 2025),
            max(active_customers) FILTER (WHERE order_year = 2025),
            max(average_order_value) FILTER (WHERE order_year = 2025),
            max(discounts) FILTER (WHERE order_year = 2025)
        ]) AS value_2025
    FROM yearly
);

WITH quarterly AS (
    SELECT
        year(o.order_date) AS order_year,
        quarter(o.order_date) AS order_quarter,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY order_year, order_quarter
)
SELECT
    order_year || '-Q' || order_quarter AS quarter,
    round(net_revenue, 2) AS net_revenue,
    round((net_revenue / lag(net_revenue) OVER (ORDER BY order_year, order_quarter) - 1) * 100, 1) AS qoq_growth_pct,
    round(
        (net_revenue / lag(net_revenue) OVER (PARTITION BY order_quarter ORDER BY order_year) - 1) * 100,
        1
    ) AS yoy_growth_pct
FROM quarterly
ORDER BY order_year, order_quarter;

WITH order_values AS (
    SELECT
        o.order_id,
        coalesce(o.promo_code, 'NO_PROMO') AS promo_code,
        sum(oi.quantity * oi.unit_price) AS gross_sales,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.order_id, o.promo_code
)
SELECT
    promo_code,
    count(*) AS completed_orders,
    round(avg(gross_sales), 2) AS avg_gross_basket,
    round(avg(net_revenue), 2) AS average_order_value,
    round(sum(gross_sales - net_revenue), 2) AS discount_cost,
    round(sum(net_revenue) * 100 / sum(sum(net_revenue)) OVER (), 1) AS revenue_share_pct
FROM order_values
GROUP BY promo_code
ORDER BY completed_orders DESC;

SELECT
    o.status,
    count(DISTINCT o.order_id) AS orders,
    round(sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS order_value,
    round(
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) * 100
        / sum(sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct))) OVER (),
        1
    ) AS share_of_placed_value_pct
FROM orders AS o
INNER JOIN order_items AS oi ON oi.order_id = o.order_id
GROUP BY o.status
ORDER BY order_value DESC;
