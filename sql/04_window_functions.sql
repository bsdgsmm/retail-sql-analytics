WITH product_revenue AS (
    SELECT
        c.category_name,
        p.product_name,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    INNER JOIN products AS p ON p.product_id = oi.product_id
    INNER JOIN categories AS c ON c.category_id = p.category_id
    WHERE o.status = 'completed'
    GROUP BY c.category_name, p.product_name
),
ranked_products AS (
    SELECT
        category_name,
        product_name,
        net_revenue,
        row_number() OVER (PARTITION BY category_name ORDER BY net_revenue DESC, product_name) AS rank_in_category,
        net_revenue / sum(net_revenue) OVER (PARTITION BY category_name) AS share_of_category
    FROM product_revenue
)
SELECT
    category_name,
    rank_in_category,
    product_name,
    round(net_revenue, 2) AS net_revenue,
    round(share_of_category * 100, 1) AS share_of_category_pct
FROM ranked_products
WHERE rank_in_category <= 3
ORDER BY category_name, rank_in_category;

WITH category_year_revenue AS (
    SELECT
        year(o.order_date) AS order_year,
        c.category_name,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    INNER JOIN products AS p ON p.product_id = oi.product_id
    INNER JOIN categories AS c ON c.category_id = p.category_id
    WHERE o.status = 'completed'
    GROUP BY order_year, c.category_name
),
ranked AS (
    SELECT
        order_year,
        category_name,
        net_revenue,
        rank() OVER (PARTITION BY order_year ORDER BY net_revenue DESC) AS revenue_rank
    FROM category_year_revenue
)
SELECT
    category_name,
    max(revenue_rank) FILTER (WHERE order_year = 2024) AS rank_2024,
    max(revenue_rank) FILTER (WHERE order_year = 2025) AS rank_2025,
    round(sum(net_revenue) FILTER (WHERE order_year = 2024), 2) AS revenue_2024,
    round(sum(net_revenue) FILTER (WHERE order_year = 2025), 2) AS revenue_2025,
    rank_2024 - rank_2025 AS positions_gained
FROM ranked
GROUP BY category_name
ORDER BY rank_2025;

WITH monthly_revenue AS (
    SELECT
        date_trunc('month', o.order_date)::DATE AS month_start,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY month_start
)
SELECT
    month_start,
    round(net_revenue, 2) AS net_revenue,
    round(lag(net_revenue) OVER (ORDER BY month_start), 2) AS previous_month_revenue,
    round(net_revenue - lag(net_revenue) OVER (ORDER BY month_start), 2) AS mom_change,
    round((net_revenue / lag(net_revenue) OVER (ORDER BY month_start) - 1) * 100, 1) AS mom_change_pct,
    round(lag(net_revenue, 12) OVER (ORDER BY month_start), 2) AS same_month_last_year,
    round((net_revenue / lag(net_revenue, 12) OVER (ORDER BY month_start) - 1) * 100, 1) AS yoy_change_pct
FROM monthly_revenue
ORDER BY month_start;

WITH monthly_revenue AS (
    SELECT
        date_trunc('month', o.order_date)::DATE AS month_start,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY month_start
)
SELECT
    month_start,
    round(net_revenue, 2) AS net_revenue,
    round(sum(net_revenue) OVER (PARTITION BY year(month_start) ORDER BY month_start), 2) AS year_to_date_revenue,
    round(sum(net_revenue) OVER (ORDER BY month_start), 2) AS cumulative_revenue,
    round(avg(net_revenue) OVER (ORDER BY month_start ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)
        AS moving_avg_3_months
FROM monthly_revenue
ORDER BY month_start;

WITH customer_spend AS (
    SELECT
        o.customer_id,
        count(DISTINCT o.order_id) AS completed_orders,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM orders AS o
    INNER JOIN order_items AS oi ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id
),
segmented AS (
    SELECT
        *,
        ntile(4) OVER (ORDER BY net_revenue DESC) AS spend_quartile
    FROM customer_spend
)
SELECT
    spend_quartile,
    count(*) AS customers,
    round(min(net_revenue), 2) AS min_customer_revenue,
    round(max(net_revenue), 2) AS max_customer_revenue,
    round(avg(completed_orders), 2) AS avg_orders,
    round(sum(net_revenue), 2) AS quartile_revenue,
    round(sum(net_revenue) * 100 / sum(sum(net_revenue)) OVER (), 1) AS share_of_revenue_pct
FROM segmented
GROUP BY spend_quartile
ORDER BY spend_quartile;

WITH order_gaps AS (
    SELECT
        customer_id,
        order_date,
        order_date - lag(order_date) OVER (PARTITION BY customer_id ORDER BY order_date, order_id) AS days_since_previous
    FROM orders
    WHERE status = 'completed'
)
SELECT
    count(DISTINCT customer_id) AS repeat_customers,
    count(days_since_previous) AS repeat_purchases,
    round(avg(days_since_previous), 1) AS avg_days_between_orders,
    median(days_since_previous) AS median_days_between_orders,
    round(quantile_cont(days_since_previous, 0.9), 1) AS p90_days_between_orders
FROM order_gaps
WHERE days_since_previous IS NOT NULL;

WITH customer_orders AS (
    SELECT
        o.customer_id,
        o.order_id,
        o.order_date,
        o.channel,
        row_number() OVER (PARTITION BY o.customer_id ORDER BY o.order_date, o.order_id) AS order_sequence,
        count(*) OVER (PARTITION BY o.customer_id) AS total_completed_orders
    FROM orders AS o
    WHERE o.status = 'completed'
)
SELECT
    channel AS first_order_channel,
    count(*) AS customers,
    round(avg(total_completed_orders), 2) AS avg_lifetime_orders,
    round(count(*) FILTER (WHERE total_completed_orders > 1) * 100.0 / count(*), 1) AS repeat_customer_pct
FROM customer_orders
WHERE order_sequence = 1
GROUP BY channel
ORDER BY customers DESC;

WITH product_revenue AS (
    SELECT
        p.product_name,
        sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS net_revenue
    FROM order_items AS oi
    INNER JOIN orders AS o ON o.order_id = oi.order_id
    INNER JOIN products AS p ON p.product_id = oi.product_id
    WHERE o.status = 'completed'
    GROUP BY p.product_name
)
SELECT
    dense_rank() OVER (ORDER BY net_revenue DESC) AS revenue_rank,
    product_name,
    round(net_revenue, 2) AS net_revenue,
    round(net_revenue * 100 / sum(net_revenue) OVER (), 2) AS share_pct,
    round(sum(net_revenue) OVER (ORDER BY net_revenue DESC, product_name) * 100 / sum(net_revenue) OVER (), 1)
        AS cumulative_share_pct,
    round(percent_rank() OVER (ORDER BY net_revenue) * 100, 1) AS percentile
FROM product_revenue
ORDER BY revenue_rank, product_name;
