SELECT
    o.order_id,
    o.order_date,
    p.product_name,
    c.category_name,
    oi.quantity,
    oi.unit_price,
    oi.discount_pct,
    round(oi.quantity * oi.unit_price * (1 - oi.discount_pct), 2) AS net_line_revenue
FROM order_items AS oi
INNER JOIN orders AS o ON o.order_id = oi.order_id
INNER JOIN products AS p ON p.product_id = oi.product_id
INNER JOIN categories AS c ON c.category_id = p.category_id
WHERE o.status = 'completed'
ORDER BY net_line_revenue DESC, oi.order_item_id
LIMIT 10;

SELECT
    c.category_name,
    count(DISTINCT o.order_id) AS orders,
    sum(oi.quantity) AS units_sold,
    round(sum(oi.quantity * oi.unit_price), 2) AS gross_sales,
    round(sum(oi.quantity * oi.unit_price * oi.discount_pct), 2) AS discounts,
    round(sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS net_revenue,
    round(sum(oi.quantity * (oi.unit_price * (1 - oi.discount_pct) - p.unit_cost)), 2) AS gross_profit
FROM categories AS c
INNER JOIN products AS p ON p.category_id = c.category_id
INNER JOIN order_items AS oi ON oi.product_id = p.product_id
INNER JOIN orders AS o ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY c.category_name
ORDER BY net_revenue DESC;

SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.region,
    c.signup_date
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL
ORDER BY c.signup_date, c.customer_id;

SELECT
    c.region,
    count(DISTINCT c.customer_id) AS customers,
    count(DISTINCT o.customer_id) AS purchasing_customers,
    count(o.order_id) AS completed_orders,
    round(count(DISTINCT o.customer_id) * 100.0 / count(DISTINCT c.customer_id), 1) AS purchasing_customer_pct
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id
   AND o.status = 'completed'
GROUP BY c.region
ORDER BY completed_orders DESC;

SELECT
    cu.region,
    round(sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)), 2) AS net_revenue,
    count(DISTINCT o.order_id) AS completed_orders,
    round(sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) / count(DISTINCT o.order_id), 2) AS avg_order_value
FROM customers AS cu
INNER JOIN orders AS o ON o.customer_id = cu.customer_id
INNER JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY cu.region
ORDER BY net_revenue DESC;

SELECT
    channel,
    count(*) AS orders,
    count(*) FILTER (WHERE status = 'completed') AS completed,
    count(*) FILTER (WHERE status = 'cancelled') AS cancelled,
    count(*) FILTER (WHERE status = 'returned') AS returned,
    round(count(*) FILTER (WHERE status = 'returned') * 100.0 / count(*), 2) AS return_rate_pct
FROM orders
GROUP BY channel
ORDER BY orders DESC;

SELECT
    c.category_name,
    p.product_id,
    p.product_name,
    p.launch_date,
    coalesce(sum(december_sales.quantity), 0) AS units_sold_dec_2025
FROM products AS p
INNER JOIN categories AS c ON c.category_id = p.category_id
LEFT JOIN (
    SELECT oi.product_id, oi.quantity
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
      AND o.order_date >= DATE '2025-12-01'
) AS december_sales ON december_sales.product_id = p.product_id
GROUP BY c.category_name, p.product_id, p.product_name, p.launch_date
ORDER BY units_sold_dec_2025, p.product_id
LIMIT 10;
