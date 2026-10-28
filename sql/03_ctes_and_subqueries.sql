WITH order_totals AS (
    SELECT
        o.order_id,
        o.channel,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS order_value,
        sum(oi.quantity) AS units
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.order_id, o.channel
)
SELECT
    channel,
    count(*) AS completed_orders,
    round(avg(order_value), 2) AS avg_order_value,
    round(median(order_value), 2) AS median_order_value,
    round(max(order_value), 2) AS largest_order_value,
    round(avg(units), 2) AS avg_units_per_order
FROM order_totals
GROUP BY channel
ORDER BY avg_order_value DESC;

WITH product_revenue AS (
    SELECT
        oi.product_id,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY oi.product_id
)
SELECT
    p.product_name,
    round(pr.net_revenue, 2) AS net_revenue,
    round(pr.net_revenue / (SELECT avg(net_revenue) FROM product_revenue), 2) AS revenue_vs_average
FROM product_revenue AS pr
INNER JOIN products AS p ON p.product_id = pr.product_id
WHERE pr.net_revenue > (SELECT avg(net_revenue) FROM product_revenue)
ORDER BY pr.net_revenue DESC;

SELECT
    c.category_name,
    p.product_name,
    p.list_price,
    round((
        SELECT avg(peer.list_price)
        FROM products AS peer
        WHERE peer.category_id = p.category_id
    ), 2) AS category_avg_price
FROM products AS p
INNER JOIN categories AS c ON c.category_id = p.category_id
WHERE p.list_price > (
    SELECT avg(peer.list_price)
    FROM products AS peer
    WHERE peer.category_id = p.category_id
)
ORDER BY c.category_name, p.list_price DESC;

SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.region,
    (
        SELECT max(o.order_date)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id
          AND o.status = 'completed'
    ) AS last_completed_order
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'completed'
      AND o.order_date < DATE '2025-01-01'
)
AND NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'completed'
      AND o.order_date >= DATE '2025-01-01'
)
ORDER BY last_completed_order, c.customer_id;

SELECT
    o.order_id,
    o.order_date,
    o.channel,
    count(*) AS order_lines
FROM orders AS o
INNER JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.status = 'completed'
  AND o.order_id IN (
      SELECT oi_new.order_id
      FROM order_items AS oi_new
      INNER JOIN products AS p ON p.product_id = oi_new.product_id
      WHERE p.launch_date >= DATE '2025-01-01'
  )
GROUP BY o.order_id, o.order_date, o.channel
ORDER BY o.order_date, o.order_id
LIMIT 15;

WITH first_orders AS (
    SELECT
        customer_id,
        min(order_date) AS first_order_date
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
customer_revenue AS (
    SELECT
        o.customer_id,
        count(DISTINCT o.order_id) AS completed_orders,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id
)
SELECT
    year(f.first_order_date) || '-Q' || quarter(f.first_order_date) AS acquisition_quarter,
    count(*) AS new_customers,
    round(avg(r.completed_orders), 2) AS avg_orders_per_customer,
    round(avg(r.net_revenue), 2) AS avg_revenue_per_customer,
    round(sum(r.net_revenue), 2) AS cohort_revenue
FROM first_orders AS f
INNER JOIN customer_revenue AS r ON r.customer_id = f.customer_id
GROUP BY acquisition_quarter
ORDER BY acquisition_quarter;

WITH RECURSIVE month_calendar AS (
    SELECT DATE '2024-01-01' AS month_start
    UNION ALL
    SELECT CAST(month_start + INTERVAL 1 MONTH AS DATE)
    FROM month_calendar
    WHERE month_start < DATE '2025-12-01'
),
smart_watch_sales AS (
    SELECT
        date_trunc('month', o.order_date)::DATE AS month_start,
        sum(oi.quantity) AS units,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    INNER JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.status = 'completed'
      AND p.product_name = 'Smart Watch'
    GROUP BY month_start
)
SELECT
    m.month_start,
    coalesce(s.units, 0) AS units_sold,
    round(coalesce(s.net_revenue, 0), 2) AS net_revenue
FROM month_calendar AS m
LEFT JOIN smart_watch_sales AS s ON s.month_start = m.month_start
ORDER BY m.month_start;
