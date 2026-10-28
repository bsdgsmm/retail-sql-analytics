SELECT
    product_id,
    product_name,
    list_price,
    unit_cost,
    round((list_price - unit_cost) / list_price * 100, 1) AS margin_pct
FROM products
WHERE list_price >= 100
ORDER BY list_price DESC, product_id;

SELECT
    order_id,
    customer_id,
    order_date,
    promo_code
FROM orders
WHERE order_date BETWEEN DATE '2025-11-20' AND DATE '2025-11-30'
  AND channel = 'mobile_app'
  AND status = 'completed'
  AND promo_code IS NOT NULL
ORDER BY order_date, order_id;

SELECT
    status,
    count(*) AS order_count,
    round(count(*) * 100.0 / sum(count(*)) OVER (), 2) AS share_pct
FROM orders
GROUP BY status
ORDER BY order_count DESC;

SELECT
    customer_id,
    count(*) AS completed_orders,
    min(order_date) AS first_order_date,
    max(order_date) AS last_order_date
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING count(*) >= 20
ORDER BY completed_orders DESC, customer_id;

SELECT
    count(*) AS order_lines,
    count(DISTINCT order_id) AS orders_with_lines,
    sum(quantity) AS units,
    round(avg(quantity), 2) AS avg_units_per_line,
    min(unit_price) AS min_unit_price,
    max(unit_price) AS max_unit_price,
    round(avg(unit_price), 2) AS avg_unit_price
FROM order_items;

SELECT
    CASE
        WHEN list_price < 25 THEN '1. Budget (< 25)'
        WHEN list_price < 75 THEN '2. Mid-range (25-74.99)'
        WHEN list_price < 200 THEN '3. Premium (75-199.99)'
        ELSE '4. Luxury (200+)'
    END AS price_tier,
    count(*) AS product_count,
    round(avg(list_price), 2) AS avg_list_price,
    round(avg((list_price - unit_cost) / list_price) * 100, 1) AS avg_margin_pct
FROM products
GROUP BY price_tier
ORDER BY price_tier;

SELECT
    coalesce(referral_source, 'unknown') AS referral_source,
    count(*) AS customers,
    count(email) AS customers_with_email,
    count(*) - count(email) AS customers_without_email
FROM customers
GROUP BY ALL
ORDER BY customers DESC;

SELECT
    coalesce(promo_code, 'NO_PROMO') AS promo_code,
    count(*) AS orders,
    count(*) FILTER (WHERE status = 'completed') AS completed_orders,
    round(
        count(*) FILTER (WHERE status = 'cancelled') * 100.0 / nullif(count(*), 0),
        2
    ) AS cancellation_rate_pct
FROM orders
GROUP BY ALL
ORDER BY orders DESC;
