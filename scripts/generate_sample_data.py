import argparse
import csv
import math
import random
import sys
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
CUSTOMER_COUNT = 600
INACTIVE_CUSTOMER_SHARE = 0.10
MAX_CUSTOMER_ACTIVITY = 4.0
FIRST_ORDER_DATE = date(2024, 1, 1)
LAST_ORDER_DATE = date(2025, 12, 31)
BASE_DAILY_ORDERS = 5.2
ANNUAL_GROWTH = 0.14

CATEGORY_CATALOG = {
    "Electronics": [
        ("Wireless Earbuds", Decimal("129.99")),
        ("Bluetooth Speaker", Decimal("79.99")),
        ("Smart Watch", Decimal("249.99")),
        ("USB-C Charger", Decimal("24.99")),
        ("Noise Cancelling Headphones", Decimal("299.99")),
        ("Portable Power Bank", Decimal("39.99")),
        ("Mechanical Keyboard", Decimal("109.99")),
        ("4K Webcam", Decimal("89.99")),
    ],
    "Home & Kitchen": [
        ("Chef Knife", Decimal("69.99")),
        ("Nonstick Frying Pan", Decimal("44.99")),
        ("Coffee Grinder", Decimal("59.99")),
        ("Glass Food Containers", Decimal("32.99")),
        ("Electric Kettle", Decimal("49.99")),
        ("Bamboo Cutting Board", Decimal("24.99")),
        ("Air Fryer", Decimal("119.99")),
        ("Linen Table Runner", Decimal("19.99")),
    ],
    "Apparel": [
        ("Organic Cotton T-Shirt", Decimal("19.99")),
        ("Slim Fit Jeans", Decimal("59.99")),
        ("Wool Sweater", Decimal("89.99")),
        ("Rain Jacket", Decimal("129.99")),
        ("Running Shorts", Decimal("29.99")),
        ("Leather Belt", Decimal("39.99")),
        ("Hooded Sweatshirt", Decimal("49.99")),
        ("Merino Socks", Decimal("16.99")),
    ],
    "Beauty & Personal Care": [
        ("Vitamin C Serum", Decimal("28.99")),
        ("Hydrating Face Cream", Decimal("24.99")),
        ("Electric Toothbrush", Decimal("69.99")),
        ("Natural Deodorant", Decimal("11.99")),
        ("Hair Repair Mask", Decimal("18.99")),
        ("Mineral Sunscreen", Decimal("15.99")),
        ("Beard Trimmer", Decimal("49.99")),
        ("Lip Balm Set", Decimal("9.99")),
    ],
    "Sports & Outdoors": [
        ("Yoga Mat", Decimal("34.99")),
        ("Adjustable Dumbbells", Decimal("199.99")),
        ("Insulated Water Bottle", Decimal("27.99")),
        ("Trail Running Shoes", Decimal("139.99")),
        ("Camping Lantern", Decimal("36.99")),
        ("Resistance Bands", Decimal("19.99")),
        ("Hiking Backpack", Decimal("99.99")),
        ("Foam Roller", Decimal("24.99")),
    ],
    "Books": [
        ("Data Storytelling Guide", Decimal("39.99")),
        ("Mediterranean Cookbook", Decimal("32.99")),
        ("Mystery Novel", Decimal("14.99")),
        ("Personal Finance Basics", Decimal("19.99")),
        ("Gardening Handbook", Decimal("22.99")),
        ("Science Fiction Anthology", Decimal("17.99")),
        ("Travel Photography", Decimal("44.99")),
        ("Children's Picture Book", Decimal("12.99")),
    ],
    "Toys & Games": [
        ("Wooden Building Blocks", Decimal("34.99")),
        ("Strategy Board Game", Decimal("49.99")),
        ("1000 Piece Puzzle", Decimal("19.99")),
        ("Remote Control Car", Decimal("59.99")),
        ("Art Supply Kit", Decimal("29.99")),
        ("Plush Bear", Decimal("17.99")),
        ("Card Game Collection", Decimal("24.99")),
        ("Science Experiment Kit", Decimal("39.99")),
    ],
    "Grocery": [
        ("Single Origin Coffee Beans", Decimal("16.99")),
        ("Extra Virgin Olive Oil", Decimal("18.99")),
        ("Organic Green Tea", Decimal("8.99")),
        ("Dark Chocolate Bar", Decimal("4.99")),
        ("Raw Honey", Decimal("12.99")),
        ("Mixed Nuts", Decimal("14.99")),
        ("Whole Grain Pasta", Decimal("5.99")),
        ("Maple Syrup", Decimal("13.99")),
    ],
}

REGION_CITIES = {
    "Northeast": ["Boston", "New York", "Philadelphia", "Pittsburgh"],
    "Southeast": ["Atlanta", "Miami", "Charlotte", "Nashville"],
    "Midwest": ["Chicago", "Minneapolis", "Columbus", "Kansas City"],
    "Southwest": ["Phoenix", "Dallas", "Austin", "Albuquerque"],
    "West": ["Seattle", "Portland", "Denver", "San Diego"],
}
REGION_WEIGHTS = [0.24, 0.21, 0.19, 0.17, 0.19]

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Elijah", "Sophia", "James", "Isabella", "Lucas", "Mia", "Mateo",
    "Amelia", "Ethan", "Harper", "Aiden", "Evelyn", "Daniel", "Abigail", "Henry", "Emily", "Jackson", "Ella",
    "Sebastian", "Grace", "Samuel", "Chloe", "David", "Layla", "Joseph", "Nora", "Carter", "Zoe", "Owen", "Aria",
    "Wyatt", "Hannah", "Leo", "Lily", "Julian", "Maya", "Isaac", "Priya", "Omar", "Mei", "Diego", "Fatima", "Kenji",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Nguyen", "Hill", "Flores", "Green", "Patel", "Kim", "Chen",
]
REFERRAL_SOURCES = ["search", "social", "friend_referral", "email_campaign"]
REFERRAL_WEIGHTS = [0.40, 0.25, 0.20, 0.15]

MONTH_SEASONALITY = {
    1: 0.82, 2: 0.80, 3: 0.92, 4: 0.95, 5: 1.00, 6: 0.98,
    7: 0.95, 8: 1.00, 9: 0.96, 10: 1.05, 11: 1.38, 12: 1.52,
}
WEEKDAY_SEASONALITY = [0.92, 0.94, 0.96, 1.00, 1.08, 1.12, 0.98]

CHANNELS = ["web", "mobile_app", "store"]
CHANNEL_WEIGHTS = [0.48, 0.32, 0.20]
STATUSES = ["completed", "cancelled", "returned"]
STATUS_WEIGHTS = [0.90, 0.05, 0.05]
ITEMS_PER_ORDER = [1, 2, 3, 4, 5]
ITEMS_PER_ORDER_WEIGHTS = [0.42, 0.28, 0.16, 0.09, 0.05]
LOW_PRICE_THRESHOLD = 30
CENTS = Decimal("0.01")


class DataGenerationError(RuntimeError):
    pass


def to_money(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build_categories() -> list[dict]:
    return [
        {"category_id": category_id, "category_name": name}
        for category_id, name in enumerate(CATEGORY_CATALOG, start=1)
    ]


def build_products(rng: random.Random) -> list[dict]:
    products = []
    product_id = 1
    for category_id, catalog_entries in enumerate(CATEGORY_CATALOG.values(), start=1):
        for product_name, list_price in catalog_entries:
            cost_ratio = rng.uniform(0.42, 0.68)
            launch_date = FIRST_ORDER_DATE - timedelta(days=rng.randint(30, 900))
            if rng.random() < 0.12:
                launch_date = random_date(rng, date(2024, 6, 1), date(2025, 9, 30))
            products.append(
                {
                    "product_id": product_id,
                    "product_name": product_name,
                    "category_id": category_id,
                    "list_price": list_price,
                    "unit_cost": to_money(list_price * Decimal(str(round(cost_ratio, 4)))),
                    "launch_date": launch_date.isoformat(),
                }
            )
            product_id += 1
    return products


def build_customers(rng: random.Random) -> list[dict]:
    customers = []
    regions = list(REGION_CITIES)
    for customer_id in range(1, CUSTOMER_COUNT + 1):
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        region = rng.choices(regions, weights=REGION_WEIGHTS)[0]
        has_email = rng.random() > 0.06
        has_referral = rng.random() > 0.30
        customers.append(
            {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name}.{last_name}{customer_id}@example.com".lower() if has_email else None,
                "city": rng.choice(REGION_CITIES[region]),
                "region": region,
                "signup_date": random_date(rng, date(2023, 3, 1), date(2025, 11, 30)).isoformat(),
                "referral_source": rng.choices(REFERRAL_SOURCES, weights=REFERRAL_WEIGHTS)[0] if has_referral else None,
            }
        )
    return customers


def promo_code_for(rng: random.Random, order_date: date, is_first_order: bool) -> tuple[str | None, Decimal]:
    if is_first_order and rng.random() < 0.35:
        return "WELCOME10", Decimal("0.10")
    if order_date.month == 11 and order_date.day >= 20 and rng.random() < 0.55:
        return "BLACKFRIDAY20", Decimal("0.20")
    if order_date.month == 12 and order_date.day <= 24 and rng.random() < 0.30:
        return "HOLIDAY15", Decimal("0.15")
    if order_date.month in (6, 7) and rng.random() < 0.20:
        return "SUMMER10", Decimal("0.10")
    if order_date.month in (3, 4) and rng.random() < 0.15:
        return "SPRING15", Decimal("0.15")
    return None, Decimal("0.00")


def expected_daily_orders(order_date: date) -> float:
    years_elapsed = (order_date - FIRST_ORDER_DATE).days / 365.25
    trend = (1 + ANNUAL_GROWTH) ** years_elapsed
    return BASE_DAILY_ORDERS * trend * MONTH_SEASONALITY[order_date.month] * WEEKDAY_SEASONALITY[order_date.weekday()]


def poisson(rng: random.Random, mean: float) -> int:
    threshold = math.exp(-mean)
    count = 0
    product = rng.random()
    while product > threshold:
        count += 1
        product *= rng.random()
    return count


def build_orders(rng: random.Random, customers: list[dict], products: list[dict]) -> tuple[list[dict], list[dict]]:
    customer_activity = {
        customer["customer_id"]: (
            0.0
            if rng.random() < INACTIVE_CUSTOMER_SHARE
            else min(rng.lognormvariate(0, 0.8), MAX_CUSTOMER_ACTIVITY)
        )
        for customer in customers
    }
    product_popularity = {product["product_id"]: rng.lognormvariate(0, 0.8) for product in products}
    customers_by_signup = sorted(customers, key=lambda customer: customer["signup_date"])
    customers_with_orders: set[int] = set()
    orders: list[dict] = []
    order_items: list[dict] = []

    current_date = FIRST_ORDER_DATE
    while current_date <= LAST_ORDER_DATE:
        eligible_customers = [
            customer["customer_id"]
            for customer in customers_by_signup
            if customer["signup_date"] <= current_date.isoformat()
            and customer_activity[customer["customer_id"]] > 0
        ]
        available_products = [product for product in products if product["launch_date"] <= current_date.isoformat()]
        if not eligible_customers or not available_products:
            raise DataGenerationError(f"No eligible customers or products on {current_date}")
        customer_weights = [customer_activity[customer_id] for customer_id in eligible_customers]
        product_weights = [product_popularity[product["product_id"]] for product in available_products]

        for _ in range(poisson(rng, expected_daily_orders(current_date))):
            order_id = len(orders) + 1
            customer_id = rng.choices(eligible_customers, weights=customer_weights)[0]
            promo_code, discount_pct = promo_code_for(rng, current_date, customer_id not in customers_with_orders)
            customers_with_orders.add(customer_id)
            orders.append(
                {
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "order_date": current_date.isoformat(),
                    "channel": rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0],
                    "status": rng.choices(STATUSES, weights=STATUS_WEIGHTS)[0],
                    "promo_code": promo_code,
                }
            )
            item_count = rng.choices(ITEMS_PER_ORDER, weights=ITEMS_PER_ORDER_WEIGHTS)[0]
            chosen_products: dict[int, dict] = {}
            while len(chosen_products) < min(item_count, len(available_products)):
                product = rng.choices(available_products, weights=product_weights)[0]
                chosen_products[product["product_id"]] = product
            for product in chosen_products.values():
                max_quantity = 4 if product["list_price"] < LOW_PRICE_THRESHOLD else 2
                order_items.append(
                    {
                        "order_item_id": len(order_items) + 1,
                        "order_id": order_id,
                        "product_id": product["product_id"],
                        "quantity": rng.randint(1, max_quantity),
                        "unit_price": product["list_price"],
                        "discount_pct": discount_pct,
                    }
                )
        current_date += timedelta(days=1)
    return orders, order_items


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise DataGenerationError(f"No rows generated for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: "" if value is None else value for key, value in row.items()} for row in rows)


def generate_dataset(seed: int = DEFAULT_SEED) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    categories = build_categories()
    products = build_products(rng)
    customers = build_customers(rng)
    orders, order_items = build_orders(rng, customers, products)
    return {
        "categories": categories,
        "products": products,
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
    }


def write_dataset(output_dir: Path, seed: int = DEFAULT_SEED) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = generate_dataset(seed)
    for table_name, rows in dataset.items():
        write_csv(output_dir / f"{table_name}.csv", rows)
    return {table_name: len(rows) for table_name, rows in dataset.items()}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the synthetic retail sample dataset as CSV files.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Random seed (default: {DEFAULT_SEED}).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the CSV files (default: data/sample).",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        write_dataset(arguments.output_dir, arguments.seed)
    except (DataGenerationError, OSError) as error:
        print(f"Data generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
