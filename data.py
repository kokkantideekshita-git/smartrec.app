"""
SMARTREC - "Your shopping, made smarter."
=========================================
data.py
-------
This file is the DATA LAYER of SMARTREC. It does four simple jobs:

1.  Holds the product catalogue (the products SMARTREC can recommend).
2.  Generates a realistic historical dataset (customer <-> product behaviour).
3.  Cleans that dataset (missing values + duplicate rows).
4.  Reads and writes the permanent CSV storage files:
        products.csv       - the product catalogue
        history.csv        - historical training data for the ML model
        customers.csv      - every SMARTREC customer profile (permanent)
        interactions.csv   - per-customer, per-product behaviour counters
        cart.csv           - what each customer currently has in their cart
        deleted_customer_ids.csv - reserved IDs after customer deletion

Everything is stored as CSV so it is easy to open, inspect and understand
- which is exactly what we want for a first-year college project.
"""

import os
import zlib
from datetime import date

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. FOLDER / FILE SETTINGS
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PRODUCTS_FILE = os.path.join(BASE_DIR, "products.csv")
HISTORY_FILE = os.path.join(BASE_DIR, "history.csv")
CUSTOMERS_FILE = os.path.join(BASE_DIR, "customers.csv")
CART_FILE = os.path.join(BASE_DIR, "cart.csv")
INTERACTIONS_FILE = os.path.join(BASE_DIR, "interactions.csv")
DELETED_CUSTOMER_IDS_FILE = os.path.join(BASE_DIR, "deleted_customer_ids.csv")

PRODUCT_CATEGORIES = [
    "Electronics",
    "Gaming",
    "Fashion",
    "Books",
    "Home",
    "Accessories",
]

# ---------------------------------------------------------------------------
# ADMIN LOGIN
# ---------------------------------------------------------------------------
# There is exactly one admin account, and the login is a plain username +
# password check. No database, no tokens, no extra libraries - that keeps the
# whole thing easy to explain in a viva.
#
# The defaults below are only the starting values. Set these two environment
# variables before starting the app to use your own admin password:
#
#     SMARTREC_ADMIN_USER   (default: admin)
#     SMARTREC_ADMIN_PASS   (default: admin123)
#
ADMIN_USERNAME = os.environ.get("SMARTREC_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("SMARTREC_ADMIN_PASS", "admin123")

# New products created from the Admin Panel get an id like PRD-1001, PRD-1002.
ADMIN_PRODUCT_ID_PREFIX = "PRD-"

CUSTOMER_ID_PREFIX = "SMR-"
CUSTOMER_ID_START = 1001          # first customer id will be SMR-1001


# ---------------------------------------------------------------------------
# 2. THE PRODUCT CATALOGUE
# ---------------------------------------------------------------------------
# Every product has:
#   Product_ID       -> unique code such as P-1001
#   Product_Name     -> name shown on the product card
#   Product_Category -> one of PRODUCT_CATEGORIES
#   Product_Price    -> price in Rupees (INR)
#   Product_Image    -> an emoji used to draw the product cover
#   Hue              -> a number used to give the cover a gradient colour
# ---------------------------------------------------------------------------

PRODUCT_CATALOG = [
    # ---------------- ELECTRONICS ----------------
    ("P-1001", "Wireless Noise Cancelling Headphones", "Electronics", 2499, "🎧", 258),
    ("P-1002", "Bluetooth Pocket Speaker", "Electronics", 1299, "🔊", 268),
    ("P-1003", "Smart Watch with AMOLED Display", "Electronics", 3499, "⌚", 276),
    ("P-1004", "4K Action Camera", "Electronics", 8999, "📷", 284),
    ("P-1005", "Sports Earbuds with Charging Case", "Electronics", 1799, "🎵", 258),
    ("P-1006", "Portable SSD 1TB", "Electronics", 5999, "💾", 268),
    ("P-1007", "65W GaN Fast Charger", "Electronics", 1499, "🔌", 276),
    ("P-1008", "LED Desk Lamp with Wireless Charging", "Electronics", 2199, "💡", 284),
    ("P-1009", "Bluetooth Party Speaker", "Electronics", 7499, "🎶", 258),
    ("P-1010", "Smart LED Bulb Pack of 4", "Electronics", 999, "💡", 268),

    # ---------------- GAMING ----------------
    ("P-2001", "RGB Wireless Gaming Mouse", "Gaming", 1499, "🖱️", 292),
    ("P-2002", "Mechanical Keyboard with Blue Switches", "Gaming", 2799, "⌨️", 258),
    ("P-2003", "7.1 Surround Gaming Headset", "Gaming", 2299, "🎮", 268),
    ("P-2004", "Extended RGB Mouse Pad", "Gaming", 899, "🟪", 276),
    ("P-2005", "Logitech-Style Racing Wheel", "Gaming", 8999, "🏎️", 284),
    ("P-2006", "Wireless Game Controller", "Gaming", 1999, "🕹️", 292),
    ("P-2007", "Ergonomic Gaming Chair", "Gaming", 12499, "🪑", 258),
    ("P-2008", '27" 165Hz Gaming Monitor', "Gaming", 15999, "🖥️", 268),
    ("P-2009", "Stream Microphone with Boom Arm", "Gaming", 3499, "🎙️", 276),
    ("P-2010", "USB Gaming Mouse with Macro Keys", "Gaming", 1199, "🎯", 284),

    # ---------------- FASHION ----------------
    ("P-3001", "Lightweight Running Shoes", "Fashion", 2499, "👟", 292),
    ("P-3002", "Denim Jacket - Unisex", "Fashion", 2799, "🧥", 258),
    ("P-3003", "Premium Cotton T-Shirt", "Fashion", 699, "👕", 268),
    ("P-3004", "Waterproof Day Backpack", "Fashion", 1599, "🎒", 276),
    ("P-3005", "Polarized UV Sunglasses", "Fashion", 1099, "🕶️", 284),
    ("P-3006", "Winter Fleece Hoodie", "Fashion", 1399, "🧶", 292),
    ("P-3007", "Formal Leather Slim Belt", "Fashion", 899, "👔", 258),
    ("P-3008", "Smart Analog Watch - Classic", "Fashion", 3299, "⌚", 268),

    # ---------------- BOOKS ----------------
    ("P-4001", "Python Crash Course - 2nd Edition", "Books", 599, "🐍", 258),
    ("P-4002", "Machine Learning Basics for Beginners", "Books", 749, "🤖", 268),
    ("P-4003", "The Pragmatic Programmer", "Books", 899, "💻", 276),
    ("P-4004", "Data Structures with Python", "Books", 649, "📊", 284),
    ("P-4005", "Science Fiction Anthology 2025", "Books", 499, "🚀", 292),
    ("P-4006", "Deep Learning Explained Visually", "Books", 999, "🧠", 258),
    ("P-4007", "Effective Marketing for Small Business", "Books", 549, "📈", 268),

    # ---------------- HOME ----------------
    ("P-5001", "Ceramic Dinner Set - 16 Pieces", "Home", 3499, "🍽️", 276),
    ("P-5002", "Digital Air Fryer 5.5L", "Home", 4999, "🍟", 284),
    ("P-5003", "Cotton Bed Sheet Set - King Size", "Home", 1799, "🛏️", 292),
    ("P-5004", "Modern Minimal Table Lamp", "Home", 1399, "🏮", 258),
    ("P-5005", "Vacuum Insulated Water Flask 1L", "Home", 899, "🥤", 268),
    ("P-5006", "Anti-Skid Yoga Mat with Carry Strap", "Home", 1199, "🧘", 276),
    ("P-5007", "Electric Kettle 1.7L", "Home", 1299, "🫖", 284),
    ("P-5008", "Scented Soy Candle Set of 4", "Home", 799, "🕯️", 292),

    # ---------------- ACCESSORIES ----------------
    ("P-6001", "Slim Laptop Backpack 15.6 inch", "Accessories", 1899, "💼", 258),
    ("P-6002", "Silent Wireless Mouse", "Accessories", 899, "🖱️", 268),
    ("P-6003", "Shock Proof Phone Case", "Accessories", 599, "📱", 276),
    ("P-6004", "20000mAh Power Bank", "Accessories", 1499, "🔋", 284),
    ("P-6005", "USB-C Braided Charging Cable 2m", "Accessories", 349, "🔗", 292),
    ("P-6006", "Laptop Cooling Stand", "Accessories", 1699, "💻", 258),
    ("P-6007", "Travel Organiser Pouch Set", "Accessories", 749, "🧳", 268),
    ("P-6008", "Bluetooth Car Speaker", "Accessories", 1999, "🚗", 276),
]

PRODUCT_COLUMNS = [
    "Product_ID",
    "Product_Name",
    "Product_Category",
    "Product_Price",
    "Product_Image",
    "Hue",
    # --- shopping-app details (added for the product page) ---
    "Brand",
    "MRP",
    "Rating",
    "Reviews",
    "Description",
    "Highlights",
    "Colours",
    "Sizes",
    "Warranty",
    "Delivery_Days",
    "Stock",
]

# Word lists used to build believable shopping-app details for every product.
# They are combined deterministically from the product id, so a product always
# gets the same brand / colours / description every time the app runs.
BRANDS_BY_CATEGORY = {
    "Electronics": ["SoundWave", "NovaTech", "Vertex", "PulseGear"],
    "Gaming": ["RazerCore", "GameForge", "PixelArena", "ShadowByte"],
    "Fashion": ["UrbanThread", "LoomWear", "SundayFit", "Nimbus"],
    "Books": ["PageTurner", "Inkwell", "ChapterOne", "LeafPress"],
    "Home": ["CozyNest", "Hearthly", "LivingCurve", "Nestora"],
    "Accessories": ["CarryWell", "DailyKit", "Orbit", "ZipLine"],
}

COLOUR_OPTIONS = {
    "Electronics": ["Midnight Black", "Pearl White", "Deep Navy", "Graphite Grey"],
    "Gaming": ["Carbon Black", "Electric Blue", "Neon Green", "Stealth Grey"],
    "Fashion": ["Classic Black", "Sand Beige", "Olive Green", "Wine Red"],
    "Books": ["Hardcover", "Paperback", "Spiral Bound", "Boxed Set"],
    "Home": ["Warm Ivory", "Charcoal", "Sage Green", "Rust Brown"],
    "Accessories": ["Jet Black", "Tan Leather", "Navy Blue", "Rose Gold"],
}

SIZE_OPTIONS = {
    "Electronics": ["Standard", "Pro", "Max"],
    "Gaming": ["Low Latency", "Balanced", "Competitive"],
    "Fashion": ["S", "M", "L", "XL"],
    "Books": ["Single Volume", "2-Volume Set", "Boxed Set"],
    "Home": ["Small", "Medium", "Large"],
    "Accessories": ["Compact", "Regular", "Oversized"],
}

DELIVERY_DAYS = [2, 3, 4, 5, 6]
WARRANTY_BY_CATEGORY = {
    "Electronics": "1 Year Manufacturer Warranty",
    "Gaming": "1 Year Manufacturer Warranty",
    "Fashion": "6 Months Brand Warranty",
    "Books": "No Warranty (Damaged Copies Not Returnable)",
    "Home": "1 Year Manufacturer Warranty",
    "Accessories": "6 Months Brand Warranty",
}


NUMERIC_PRODUCT_COLUMNS = [
    "Product_Price", "Hue", "MRP", "Rating", "Reviews", "Delivery_Days", "Stock"
]


def enrich_catalogue(products):
    """
    Add the extra shopping-app details to every product.

    Everything is derived from the product id with a fixed seed, so a product
    always gets exactly the same brand, colours, sizes, rating and description.

    IMPORTANT: a value that is already filled in is NEVER changed. That is what
    lets an admin type their own description in the Admin Panel and have it stay
    there, even after the app is restarted.
    """

    for column in PRODUCT_COLUMNS:
        if column not in products.columns:
            # text columns must start as text, otherwise pandas refuses strings later
            products[column] = np.nan if column in NUMERIC_PRODUCT_COLUMNS else ""

    def is_blank(value):
        """True when a cell has no real value yet (so we should fill it in)."""
        if value is None:
            return True
        if isinstance(value, float) and pd.isna(value):
            return True
        return str(value).strip() == ""

    for position, (_, row) in enumerate(products.iterrows()):
        category = row["Product_Category"]
        price = float(row["Product_Price"])
        name = row["Product_Name"]

        # zlib.crc32 is stable across runs, unlike the built-in hash()
        seed_value = zlib.crc32(str(row["Product_ID"]).encode("utf-8"))
        random_number = np.random.default_rng(seed_value + position)

        brands = BRANDS_BY_CATEGORY.get(category, ["SmartRec"])
        colours = COLOUR_OPTIONS.get(category, ["Black"])
        sizes = SIZE_OPTIONS.get(category, ["Standard"])
        warranty = WARRANTY_BY_CATEGORY.get(category, "1 Year Warranty")
        delivery = int(DELIVERY_DAYS[seed_value % len(DELIVERY_DAYS)])

        # a believable discount between 5% and 45%
        discount = int(random_number.integers(5, 46))
        mrp = int(round(price / (1 - discount / 100) / 10) * 10)

        # rating stays between 3.6 and 4.9, reviews between 40 and 9000
        rating = round(float(random_number.uniform(3.6, 4.9)), 1)
        reviews = int(random_number.integers(40, 9000))

        highlights = [
            f"{brands[seed_value % len(brands)]} {category.lower()} favourite",
            f"{discount}% off today — ₹{mrp:,} reduced to ₹{int(price):,}",
            f"{delivery}-day free delivery with cash on delivery",
            warranty,
            f"Customer rating {rating} out of 5 from {reviews:,} reviews",
        ]

        description = (
            f"{name} from {brands[seed_value % len(brands)]} is one of the most "
            f"reviewed products in the SMARTREC {category.lower()} catalogue. "
            f"It sits at ₹{int(price):,} after a {discount}% discount, is covered by a "
            f"{warranty.lower()} and reaches you in about {delivery} days. "
            f"Customers who viewed similar {category.lower()} products in the "
            f"historical data often ended up buying one, which is why the SMARTREC "
            f"model scores it for you."
        )

        # only fill a field when it is still blank - never overwrite real data
        defaults = {
            "Brand": brands[seed_value % len(brands)],
            "MRP": mrp,
            "Rating": rating,
            "Reviews": reviews,
            "Description": description,
            "Highlights": " | ".join(highlights),
            "Colours": " | ".join(colours),
            "Sizes": " | ".join(sizes),
            "Warranty": warranty,
            "Delivery_Days": delivery,
            "Stock": int(random_number.integers(0, 60)),
        }
        for column, value in defaults.items():
            if is_blank(products.at[products.index[position], column]):
                products.at[products.index[position], column] = value

    return products[PRODUCT_COLUMNS]


def build_product_catalogue():
    """Return the product catalogue as a pandas DataFrame."""
    rows = [
        {
            "Product_ID": product_id,
            "Product_Name": name,
            "Product_Category": category,
            "Product_Price": price,
            "Product_Image": image,
            "Hue": hue,
        }
        for (product_id, name, category, price, image, hue) in PRODUCT_CATALOG
    ]
    return enrich_catalogue(pd.DataFrame(rows))


# ---------------------------------------------------------------------------
# 3. HISTORICAL DATASET GENERATION
# ---------------------------------------------------------------------------
# SMARTREC needs historical data to learn from. In a real company this data
# would come from real server logs. For this project we create a *realistic*
# dataset with genuine relationships between the columns:
#
#   * products in popular categories get more views
#   * a customer who views a lot also tends to add to cart
#   * a product inside the customer's budget is bought more often
#   * a customer who has bought before is more likely to buy again
#   * repeat buyers of a category strongly prefer that category
#
# The "Purchased" column is our ML TARGET (1 = purchased, 0 = not purchased).
# ---------------------------------------------------------------------------


def _sigmoid(value):
    """Small helper that turns any number into a value between 0 and 1."""
    return 1.0 / (1.0 + np.exp(-value))


def generate_history(number_of_customers=900, random_seed=42):
    """
    Create a realistic customer <-> product interaction history.

    Returns a pandas DataFrame with the columns required by the model:
        Customer_ID, Product_ID, Product_Category, Product_Price,
        Views, Cart_Adds, Purchases, Previous_Purchases, Purchased
    """
    rng = np.random.default_rng(random_seed)
    catalogue = build_product_catalogue()

    # How popular is every product? (used so famous products get more views)
    product_popularity = rng.gamma(shape=2.0, scale=6.0, size=len(catalogue))
    product_popularity = (product_popularity / product_popularity.max()).round(3)

    # Hidden "quality" of every product. This value never reaches the model -
    # the model can only discover it through the historical purchase rates.
    # It is what makes collaborative filtering actually possible.
    product_quality = rng.beta(2.0, 2.0, size=len(catalogue)).round(3)

    history_rows = []

    for customer_number in range(number_of_customers):
        customer_id = f"OLD-{customer_number + 1:05d}"

        # --- what this customer selected on the SMARTREC sign-up form -------
        declared_categories = list(
            rng.choice(PRODUCT_CATEGORIES, size=int(rng.integers(1, 4)), replace=False)
        )

        # --- this customer's taste: how much they like every category -------
        category_affinity = rng.dirichlet(np.ones(len(PRODUCT_CATEGORIES)) * 0.8)
        declared_boost = np.array(
            [2.5 if name in declared_categories else 0.0 for name in PRODUCT_CATEGORIES]
        )
        category_affinity = category_affinity + declared_boost
        category_affinity = category_affinity / category_affinity.sum()

        favourite_category_index = int(np.argmax(category_affinity))

        # --- budget of this customer --------------------------------------
        min_budget = int(rng.choice([500, 1000, 2000, 3000]))
        max_budget = int(min_budget + rng.choice([3000, 5000, 9000, 15000, 25000]))

        # How many products this customer browsed in total
        rows_for_this_customer = int(rng.integers(8, 26))

        # How many products were *recommended* to this customer before they
        # browsed anything. A brand new customer has no views yet, so the model
        # must also learn what happens with customers that only saw a
        # recommendation. This is what makes cold-start work properly.
        recommended_products = int(rng.integers(3, 9))

        previous_purchases = 0

        for position in range(rows_for_this_customer + recommended_products):
            # the first few products are recommendation impressions (no views yet)
            is_recommendation = position < recommended_products

            # 60% of the time the customer browses inside their favourite
            # category, the rest of the time they explore other categories.
            if rng.random() < 0.6:
                category_index = favourite_category_index
            else:
                category_index = int(rng.integers(0, len(PRODUCT_CATEGORIES)))

            category_name = PRODUCT_CATEGORIES[category_index]
            products_in_category = catalogue[
                catalogue["Product_Category"] == category_name
            ]
            product = products_in_category.iloc[int(rng.integers(0, len(products_in_category)))]

            product_price = float(product["Product_Price"])
            # how popular is this exact product?
            product_row_number = catalogue.index[
                catalogue["Product_ID"] == product["Product_ID"]
            ][0]
            popularity = float(product_popularity[product_row_number])
            quality = float(product_quality[product_row_number])

            # ---------------- VIEWS -----------------------------------------
            # More views when: the product is popular, the category matches the
            # customer's taste, and the price feels affordable.
            price_fits_budget = min_budget <= product_price <= max_budget
            price_comfort = 1.0 if price_fits_budget else 0.45

            if is_recommendation:
                # only a recommendation was shown - the customer has not opened
                # the product page yet
                views = 0
            else:
                view_score = (
                    1.1 * popularity
                    + 1.4 * category_affinity[category_index]
                    + 0.5 * price_comfort
                    + rng.normal(0, 0.55)
                )
                views = int(np.clip(round(view_score * 6), 0, 90))

            # ---------------- CART ADDS -------------------------------------
            # A cart add needs attention, a comfortable price and history.
            cart_probability = _sigmoid(
                -1.4
                + 0.65 * np.log1p(views)
                + 0.9 * price_comfort
                + 0.75 * category_affinity[category_index]
                + 0.55 * previous_purchases
                + 0.85 * quality
                + rng.normal(0, 0.7)
            )
            cart_adds = int(rng.random() < cart_probability) * int(
                np.clip(round(rng.poisson(1.4) + 1), 1, 4)
            )
            if views == 0:
                cart_adds = 0

            # ---------------- PURCHASES -------------------------------------
            purchase_score = (
                -4.25
                + 1.05 * np.log1p(cart_adds)
                + 0.75 * price_comfort
                + 0.55 * category_affinity[category_index]
                + 0.30 * previous_purchases
                + 0.22 * np.log1p(views)
                + 1.00 * quality
                + rng.normal(0, 0.7)
            )
            # a customer who only saw a recommendation needs a stronger reason
            # to buy than a customer who actually opened the product page
            if is_recommendation:
                purchase_score += 0.90 + 0.45 * popularity

            purchases = int(rng.random() < _sigmoid(purchase_score))
            if purchases and cart_adds == 0 and not is_recommendation:
                cart_adds = 1          # buying from a product page goes via the cart

            history_rows.append(
                {
                    "Customer_ID": customer_id,
                    "Product_ID": product["Product_ID"],
                    "Product_Category": category_name,
                    "Product_Price": product_price,
                    "Views": views,
                    "Cart_Adds": cart_adds,
                    "Purchases": purchases,
                    "Previous_Purchases": previous_purchases,
                    "Purchased": 1 if purchases > 0 else 0,
                    "Event_Order": position,
                    "Preferred_Category_Match": int(category_name in declared_categories),
                    "Declared_Categories": "|".join(declared_categories),
                    "Min_Budget": min_budget,
                    "Max_Budget": max_budget,
                }
            )

            # a purchase increases the customer's purchase history
            if purchases:
                previous_purchases += 1

    history = pd.DataFrame(history_rows)

    # --- Add a few realistic data problems so cleaning has something to do ---
    history.loc[rng.choice(history.index, size=int(len(history) * 0.012), replace=False), "Views"] = np.nan
    history.loc[rng.choice(history.index, size=int(len(history) * 0.008), replace=False), "Cart_Adds"] = np.nan
    history.loc[rng.choice(history.index, size=int(len(history) * 0.005), replace=False), "Product_Category"] = np.nan
    history = pd.concat([history, history.sample(frac=0.012, random_state=1)], ignore_index=True)

    return history


# ---------------------------------------------------------------------------
# 4. DATA CLEANING
# ---------------------------------------------------------------------------


def clean_history(raw_history):
    """
    Clean the historical data and return (clean_dataframe, cleaning_report).

    Steps:
      1. Report the original shape.
      2. Drop completely empty rows.
      3. Remove duplicate customer-product records.
      4. Fill missing numbers with the median (a safe, typical choice).
      5. Fill missing categories with the most common category.
      6. Make sure the numbers are whole numbers again.
    """
    report = {}
    data = raw_history.copy()

    report["rows_loaded"] = len(data)
    report["missing_before"] = int(data.isna().sum().sum())

    # 1. empty rows
    data = data.dropna(how="all")

    # 2. duplicates: the same customer looking at the same product twice in the
    #    raw log should be merged into one record with the best values.
    duplicate_rows = int(data.duplicated(subset=["Customer_ID", "Product_ID"]).sum())
    data = data.sort_values(["Customer_ID", "Product_ID"])
    data = data.groupby(["Customer_ID", "Product_ID"], as_index=False).agg(
        {
            "Product_Category": "first",
            "Product_Price": "max",
            "Views": "max",
            "Cart_Adds": "max",
            "Purchases": "max",
            "Previous_Purchases": "last",
            "Event_Order": "max",
            "Preferred_Category_Match": "max",
            "Declared_Categories": "last",
            "Min_Budget": "last",
            "Max_Budget": "last",
        }
    )
    report["duplicate_rows_removed"] = duplicate_rows

    # 3. missing numbers -> median
    for column in ["Product_Price", "Views", "Cart_Adds", "Purchases", "Previous_Purchases"]:
        median_value = data[column].median()
        if pd.isna(median_value):
            median_value = 0
        data[column] = data[column].fillna(median_value)

    # 4. missing category -> most common category
    most_common_category = data["Product_Category"].mode()
    most_common_category = (
        most_common_category[0] if len(most_common_category) > 0 else PRODUCT_CATEGORIES[0]
    )
    data["Product_Category"] = data["Product_Category"].fillna(most_common_category)

    # 5. whole numbers only
    for column in ["Product_Price", "Views", "Cart_Adds", "Purchases", "Previous_Purchases"]:
        data[column] = data[column].clip(lower=0).round().astype(int)

    # 6. rebuild the target column from the purchase count
    data["Purchased"] = (data["Purchases"] > 0).astype(int)

    report["rows_after"] = len(data)
    report["missing_after"] = int(data.isna().sum().sum())
    report["purchased_rows"] = int(data["Purchased"].sum())
    report["not_purchased_rows"] = int((data["Purchased"] == 0).sum())
    report["customers"] = int(data["Customer_ID"].nunique())
    report["products"] = int(data["Product_ID"].nunique())

    return data.reset_index(drop=True), report


# ---------------------------------------------------------------------------
# 5. CSV HELPERS (safe loading + saving)
# ---------------------------------------------------------------------------


def read_csv_or_empty(file_path, columns):
    """Read a CSV file. If the file is missing or broken, return an empty one."""
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame(columns=columns)


def write_csv(dataframe, file_path):
    """Save a DataFrame to CSV. Creates the file if it does not exist yet."""
    dataframe.to_csv(file_path, index=False)


# ---------------------------------------------------------------------------
# 6. FIRST-TIME SETUP
# ---------------------------------------------------------------------------


def initialise_storage():
    """
    Create every CSV file the first time the app runs.
    Existing files are never overwritten, so customer data stays permanent.
    """
    created = []

    # ---- products.csv -----------------------------------------------------
    if not os.path.exists(PRODUCTS_FILE):
        catalogue = build_product_catalogue()
        write_csv(catalogue, PRODUCTS_FILE)
        created.append("products.csv")
    else:
        # an older products.csv may not have the shopping-app columns yet
        existing = read_csv_or_empty(PRODUCTS_FILE, PRODUCT_COLUMNS)
        if len(existing) > 0:
            missing = [
                column for column in PRODUCT_COLUMNS if column not in existing.columns
            ]
            if missing:
                write_csv(enrich_catalogue(existing), PRODUCTS_FILE)

    # ---- history.csv (training data for the ML model) ---------------------
    if not os.path.exists(HISTORY_FILE):
        write_csv(generate_history(), HISTORY_FILE)
        created.append("history.csv")

    # ---- customers.csv ----------------------------------------------------
    if not os.path.exists(CUSTOMERS_FILE):
        write_csv(pd.DataFrame(columns=CUSTOMER_COLUMNS), CUSTOMERS_FILE)
        created.append("customers.csv")

    # ---- interactions.csv -------------------------------------------------
    if not os.path.exists(INTERACTIONS_FILE):
        write_csv(pd.DataFrame(columns=INTERACTION_COLUMNS), INTERACTIONS_FILE)
        created.append("interactions.csv")

    # ---- cart.csv (what each customer has in their shopping cart) ---------
    if not os.path.exists(CART_FILE):
        write_csv(pd.DataFrame(columns=CART_COLUMNS), CART_FILE)
        created.append("cart.csv")

    return created


CUSTOMER_COLUMNS = [
    "Customer_ID",
    "Name",
    "Contact",
    "Categories",
    "Min_Budget",
    "Max_Budget",
    "Views",
    "Cart_Adds",
    "Purchases",
    "Previous_Purchases",
    "Total_Spend",
    "Created_On",
    "Last_Seen",
]

INTERACTION_COLUMNS = [
    "Customer_ID",
    "Product_ID",
    "Product_Price",
    "Views",
    "Cart_Adds",
    "Purchases",
    "Last_Action",
]

# The shopping cart. One row = one product sitting in one customer's cart.
CART_COLUMNS = [
    "Customer_ID",
    "Product_ID",
    "Quantity",
    "Unit_Price",
    "Colour",
    "Size",
    "Added_On",
]


# ---------------------------------------------------------------------------
# 7. PRODUCT HELPERS
# ---------------------------------------------------------------------------


def load_products():
    """Load products.csv, fill in any missing shopping details, and return it."""
    products = read_csv_or_empty(PRODUCTS_FILE, PRODUCT_COLUMNS)
    if len(products) == 0:
        return build_product_catalogue()
    products["Product_Price"] = pd.to_numeric(products["Product_Price"], errors="coerce").fillna(0)
    products["Hue"] = pd.to_numeric(products["Hue"], errors="coerce").fillna(258)
    # an old products.csv will not have the details columns yet
    return enrich_catalogue(products)


def find_product(product_id):
    """Return one product row (as a dictionary) or None if the id is unknown."""
    products = load_products()
    match = products[products["Product_ID"] == product_id]
    if len(match) == 0:
        return None
    row = match.iloc[0].to_dict()
    row["Product_Price"] = float(row["Product_Price"])
    for column in ("MRP", "Rating", "Delivery_Days", "Stock", "Reviews"):
        try:
            row[column] = float(row[column])
        except (TypeError, ValueError):
            row[column] = 0.0
    return row


def split_options(value):
    """Turn a stored 'Red | Blue | Green' string into a clean Python list."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def category_statistics(history):
    """
    Simple statistics about every category, learned from the history.
    Used to draw the charts on the AI Insights page.
    """
    if len(history) == 0:
        return pd.DataFrame(
            columns=["Product_Category", "Views", "Cart_Adds", "Purchases", "Purchase_Rate"]
        )

    stats = (
        history.groupby("Product_Category")
        .agg(
            Views=("Views", "sum"),
            Cart_Adds=("Cart_Adds", "sum"),
            Purchases=("Purchases", "sum"),
        )
        .reset_index()
    )
    stats["Purchase_Rate"] = stats["Purchases"] / (stats["Views"] + stats["Cart_Adds"] + 1)
    return stats


# ---------------------------------------------------------------------------
# 8. CUSTOMER HELPERS  (this is the heart of "permanent customers")
# ---------------------------------------------------------------------------


def load_customers():
    """Load every customer profile that SMARTREC has ever created."""
    customers = read_csv_or_empty(CUSTOMERS_FILE, CUSTOMER_COLUMNS)
    if len(customers) == 0:
        return pd.DataFrame(columns=CUSTOMER_COLUMNS)

    for column in ["Min_Budget", "Max_Budget", "Views", "Cart_Adds", "Purchases",
                   "Previous_Purchases", "Total_Spend"]:
        customers[column] = pd.to_numeric(customers[column], errors="coerce").fillna(0)

    return customers


def load_interactions():
    """Load the behaviour table (one row per customer + product)."""
    interactions = read_csv_or_empty(INTERACTIONS_FILE, INTERACTION_COLUMNS)
    if len(interactions) == 0:
        return pd.DataFrame(columns=INTERACTION_COLUMNS)

    for column in ["Views", "Cart_Adds", "Purchases"]:
        interactions[column] = pd.to_numeric(interactions[column], errors="coerce").fillna(0)

    if "Product_Price" not in interactions.columns:
        interactions["Product_Price"] = 0.0
    interactions["Product_Price"] = pd.to_numeric(
        interactions["Product_Price"], errors="coerce"
    ).fillna(0.0)

    return interactions


def generate_unique_customer_id():
    """
    Create the next free SMARTREC customer id.

    Rules:
      * ids look like  SMR-1001, SMR-1002, SMR-1003 ...
      * active customer IDs and deleted ID reservations are both checked
      * an id is NEVER reused, so two customers can never share one
      * a returning customer never receives a new id
    """
    customers = load_customers()
    highest_number = CUSTOMER_ID_START - 1

    deleted_ids = read_csv_or_empty(
        DELETED_CUSTOMER_IDS_FILE, ["Customer_ID"]
    )
    allocated_ids = set(customers["Customer_ID"].astype(str))
    if len(deleted_ids) > 0:
        allocated_ids.update(deleted_ids["Customer_ID"].astype(str))

    if allocated_ids:
        for existing_id in allocated_ids:
            normalized_id = existing_id.strip().upper()
            if normalized_id.startswith(CUSTOMER_ID_PREFIX):
                digits = normalized_id[len(CUSTOMER_ID_PREFIX):]
                if digits.isdigit():
                    highest_number = max(highest_number, int(digits))

    new_number = highest_number + 1

    # extra safety loop - keep checking until we really find a free id
    used_ids = {customer_id.strip().upper() for customer_id in allocated_ids}
    while f"{CUSTOMER_ID_PREFIX}{new_number}" in used_ids:
        new_number += 1

    return f"{CUSTOMER_ID_PREFIX}{new_number}"


def save_new_customer(name, contact, categories, min_budget, max_budget):
    """
    Save a brand-new customer permanently and return their new profile row.
    """
    customer_id = generate_unique_customer_id()

    new_customer = {
        "Customer_ID": customer_id,
        "Name": name,
        "Contact": contact,
        "Categories": "|".join(categories),
        "Min_Budget": int(min_budget),
        "Max_Budget": int(max_budget),
        "Views": 0,
        "Cart_Adds": 0,
        "Purchases": 0,
        "Previous_Purchases": 0,
        "Total_Spend": 0,
        "Created_On": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "Last_Seen": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    }

    customers = load_customers()
    customers = pd.concat([customers, pd.DataFrame([new_customer])], ignore_index=True)
    write_csv(customers, CUSTOMERS_FILE)

    return new_customer


def find_customer(customer_id):
    """Find one customer by their SMARTREC id. Returns None if not found."""
    customers = load_customers()
    if len(customers) == 0:
        return None

    wanted = str(customer_id).strip().upper()
    match = customers[customers["Customer_ID"].astype(str).str.upper() == wanted]
    if len(match) == 0:
        return None

    return match.iloc[0].to_dict()


def delete_customer(customer_id):
    """Delete a customer profile and its cart and interaction records."""
    wanted = str(customer_id).strip().upper()
    customers = load_customers()
    matching = customers["Customer_ID"].astype(str).str.strip().str.upper() == wanted
    if not matching.any():
        return False

    deleted_ids = read_csv_or_empty(
        DELETED_CUSTOMER_IDS_FILE, ["Customer_ID"]
    )
    known_deleted = set(
        deleted_ids["Customer_ID"].astype(str).str.strip().str.upper()
    )
    if wanted not in known_deleted:
        deleted_ids = pd.concat(
            [deleted_ids, pd.DataFrame([{"Customer_ID": wanted}])],
            ignore_index=True,
        )
        write_csv(deleted_ids, DELETED_CUSTOMER_IDS_FILE)

    write_csv(customers.loc[~matching].reset_index(drop=True), CUSTOMERS_FILE)

    interactions = load_interactions()
    if len(interactions) > 0:
        keep_interactions = (
            interactions["Customer_ID"].astype(str).str.strip().str.upper() != wanted
        )
        write_csv(
            interactions.loc[keep_interactions].reset_index(drop=True),
            INTERACTIONS_FILE,
        )

    cart = load_cart()
    if len(cart) > 0:
        keep_cart = cart["Customer_ID"].astype(str).str.strip().str.upper() != wanted
        write_csv(cart.loc[keep_cart].reset_index(drop=True), CART_FILE)

    return True


def get_customer_interactions(customer_id):
    """
    All behaviour rows that belong to one customer.

    The product name, category and price are added from products.csv so the
    rest of the app does not have to look them up again.
    """
    interactions = load_interactions()
    if len(interactions) == 0:
        interactions = pd.DataFrame(columns=INTERACTION_COLUMNS + ["Product_Name", "Product_Category"])
        return interactions

    catalogue = load_products()[["Product_ID", "Product_Name", "Product_Category", "Product_Price"]]
    interactions = interactions.merge(catalogue, on="Product_ID", how="left", suffixes=("", "_catalogue"))

    # if the stored price is missing, take the price from the catalogue
    if "Product_Price_catalogue" in interactions.columns:
        interactions["Product_Price"] = interactions["Product_Price"].fillna(
            interactions["Product_Price_catalogue"]
        )
        interactions = interactions.drop(columns=["Product_Price_catalogue"])

    interactions["Product_Category"] = interactions["Product_Category"].fillna("Unknown")

    customer_rows = interactions[interactions["Customer_ID"] == customer_id]
    return customer_rows.reset_index(drop=True)


def customer_purchased_product_ids(customer_id):
    """Which products has this customer already bought? (never recommend them)"""
    interactions = get_customer_interactions(customer_id)
    if len(interactions) == 0:
        return set()
    bought = interactions[interactions["Purchases"] > 0]
    return set(bought["Product_ID"])


def record_interaction(customer_id, product_id, action, price=0, quantity=1):
    """
    Record one customer action and update the permanent customer data.

    action = "view"    -> Views      += 1
    action = "cart"    -> Cart_Adds  += 1
    action = "purchase"-> Purchases  += quantity, Total_Spend += price * quantity

    Buying three units of a product is three real purchases, so a purchase
    event carries how many units were bought. Views and cart adds are clicks,
    so they always count as one.

    Both interactions.csv (per product) and customers.csv (totals) are updated
    and saved, so the information survives an application restart.
    """
    action_column = {
        "view": "Views",
        "cart": "Cart_Adds",
        "purchase": "Purchases",
    }[action]

    units = int(quantity) if action == "purchase" else 1
    units = max(units, 1)
    today = pd.Timestamp.now()

    # ---------------- interactions.csv ------------------------------------
    interactions = load_interactions()
    matching = interactions[
        (interactions["Customer_ID"] == customer_id)
        & (interactions["Product_ID"] == product_id)
    ]

    if len(matching) > 0:
        position = matching.index[0]
        interactions.at[position, action_column] = (
            interactions.at[position, action_column] + units
        )
        interactions.at[position, "Last_Action"] = today.strftime("%Y-%m-%d %H:%M")
    else:
        new_row = {
            "Customer_ID": customer_id,
            "Product_ID": product_id,
            "Product_Price": float(price),
            "Views": 1 if action == "view" else 0,
            "Cart_Adds": 1 if action == "cart" else 0,
            "Purchases": units if action == "purchase" else 0,
            "Last_Action": today.strftime("%Y-%m-%d %H:%M"),
        }
        interactions = pd.concat([interactions, pd.DataFrame([new_row])], ignore_index=True)

    write_csv(interactions, INTERACTIONS_FILE)

    # ---------------- customers.csv ----------------------------------------
    customers = load_customers()
    position = customers.index[
        customers["Customer_ID"].astype(str).str.upper() == str(customer_id).upper()
    ]
    if len(position) > 0:
        position = position[0]
        customers.at[position, "Views"] = customers.at[position, "Views"] + (1 if action == "view" else 0)
        customers.at[position, "Cart_Adds"] = customers.at[position, "Cart_Adds"] + (1 if action == "cart" else 0)

        if action == "purchase":
            # every unit bought is a real purchase for the loyalty totals
            customers.at[position, "Purchases"] = customers.at[position, "Purchases"] + units
            # purchases already made now become "previous purchases"
            customers.at[position, "Previous_Purchases"] = (
                customers.at[position, "Previous_Purchases"] + units
            )
            customers.at[position, "Total_Spend"] = (
                customers.at[position, "Total_Spend"] + float(price) * units
            )

        customers.at[position, "Last_Seen"] = today.strftime("%Y-%m-%d %H:%M")
        write_csv(customers, CUSTOMERS_FILE)
        return customers.loc[position].to_dict()

    return None


def parse_categories(category_string):
    """Turn 'Electronics|Gaming' back into ['Electronics', 'Gaming']."""
    if not isinstance(category_string, str) or category_string.strip() == "":
        return []
    return [part.strip() for part in category_string.split("|") if part.strip()]


# ---------------------------------------------------------------------------
# 10. THE SHOPPING CART
# ---------------------------------------------------------------------------
# The cart is a real, permanent list of products (cart.csv). Adding a product
# to the cart also records the behaviour event, so the machine learning model
# learns from it exactly like every other shopping app.
# ---------------------------------------------------------------------------


def load_cart():
    """Read cart.csv and return it as a DataFrame with the right columns."""
    return read_csv_or_empty(CART_FILE, CART_COLUMNS)


def customer_cart(customer_id):
    """Every cart line belonging to one customer (newest first)."""
    cart = load_cart()
    if len(cart) == 0:
        return cart
    lines = cart[cart["Customer_ID"].astype(str).str.upper() == str(customer_id).upper()]
    lines = lines.copy()
    lines["Quantity"] = pd.to_numeric(lines["Quantity"], errors="coerce").fillna(1).astype(int)
    lines["Unit_Price"] = pd.to_numeric(lines["Unit_Price"], errors="coerce").fillna(0.0)
    return lines.sort_values("Added_On", ascending=False)


def cart_count(customer_id):
    """Total number of units in the cart (used for the badge on the nav button)."""
    lines = customer_cart(customer_id)
    if len(lines) == 0:
        return 0
    return int(lines["Quantity"].sum())


def add_to_cart(customer_id, product_id, quantity=1, colour="", size=""):
    """
    Put a product in the cart.

    Adding the same product again increases the quantity instead of creating a
    duplicate row. Returns the new total quantity of that product in the cart.
    """
    product = find_product(product_id)
    if product is None:
        return 0

    quantity = max(1, int(quantity))
    today = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    cart = load_cart()

    matching = cart[
        (cart["Customer_ID"].astype(str).str.upper() == str(customer_id).upper())
        & (cart["Product_ID"] == product_id)
    ]

    if len(matching) > 0:
        position = matching.index[0]
        current = pd.to_numeric(
            cart.at[position, "Quantity"], errors="coerce"
        )
        cart.at[position, "Quantity"] = int((0 if pd.isna(current) else current) + quantity)
        cart.at[position, "Unit_Price"] = product["Product_Price"]
        if colour:
            cart.at[position, "Colour"] = colour
        if size:
            cart.at[position, "Size"] = size
    else:
        new_row = {
            "Customer_ID": customer_id,
            "Product_ID": product_id,
            "Quantity": quantity,
            "Unit_Price": product["Product_Price"],
            "Colour": colour or (split_options(product.get("Colours"))[0:1] or [""])[0],
            "Size": size or (split_options(product.get("Sizes"))[0:1] or [""])[0],
            "Added_On": today,
        }
        cart = pd.concat([cart, pd.DataFrame([new_row])], ignore_index=True)

    write_csv(cart, CART_FILE)
    row = cart[cart["Product_ID"] == product_id].iloc[-1]
    return int(row["Quantity"])


def update_cart_quantity(customer_id, product_id, quantity):
    """Set a new quantity. A quantity of 0 or less removes the line."""
    quantity = int(quantity)
    cart = load_cart()
    matching = cart[
        (cart["Customer_ID"].astype(str).str.upper() == str(customer_id).upper())
        & (cart["Product_ID"] == product_id)
    ]
    if len(matching) == 0:
        return 0

    if quantity <= 0:
        remove_from_cart(customer_id, product_id)
        return 0

    position = matching.index[0]
    cart.at[position, "Quantity"] = quantity
    write_csv(cart, CART_FILE)
    return quantity


def remove_from_cart(customer_id, product_id):
    """Take one product out of the cart."""
    cart = load_cart()
    keep = ~(
        (cart["Customer_ID"].astype(str).str.upper() == str(customer_id).upper())
        & (cart["Product_ID"] == product_id)
    )
    write_csv(cart[keep].reset_index(drop=True), CART_FILE)


def clear_cart(customer_id):
    """Empty the whole cart of one customer."""
    cart = load_cart()
    keep = cart["Customer_ID"].astype(str).str.upper() != str(customer_id).upper()
    write_csv(cart[keep].reset_index(drop=True), CART_FILE)


def cart_details(customer_id):
    """
    The cart joined with the product catalogue, ready for the cart page.

    Returns a DataFrame with one row per product plus a real line total.
    """
    lines = customer_cart(customer_id)
    if len(lines) == 0:
        return lines

    products = load_products()
    merged = lines.merge(
        products[["Product_ID", "Product_Name", "Product_Category", "Product_Image", "Hue"]],
        on="Product_ID",
        how="left",
    )
    merged["Product_Name"] = merged["Product_Name"].fillna("Unknown product")
    merged["Product_Category"] = merged["Product_Category"].fillna("General")
    merged["Line_Total"] = merged["Unit_Price"] * merged["Quantity"]
    return merged.reset_index(drop=True)


def cart_totals(customer_id):
    """Real money numbers for the cart summary panel."""
    lines = cart_details(customer_id)
    if len(lines) == 0:
        return {"items": 0, "units": 0, "subtotal": 0.0, "delivery": 0.0, "savings": 0.0, "total": 0.0}

    units = int(lines["Quantity"].sum())
    subtotal = float(lines["Line_Total"].sum())

    # a small, believable delivery rule: free above ₹999, else ₹49
    delivery = 0.0 if subtotal >= 999 or subtotal == 0 else 49.0

    # savings = (MRP - selling price) x quantity, using the real catalogue
    savings = 0.0
    for _, line in lines.iterrows():
        product = find_product(line["Product_ID"])
        if product and product["MRP"] > product["Product_Price"]:
            savings += (product["MRP"] - product["Product_Price"]) * int(line["Quantity"])

    return {
        "items": int(len(lines)),
        "units": units,
        "subtotal": subtotal,
        "delivery": delivery,
        "savings": savings,
        "total": subtotal + delivery,
    }
# ---------------------------------------------------------------------------
# 11. THE ADMIN PANEL - ADDING AND EDITING PRODUCTS
# ---------------------------------------------------------------------------
# The admin is the only person who can change the product catalogue. These four
# small functions are all the admin system needs:
#
#   check_admin_login()  - is this really the admin?
#   generate_product_id()- make the next free PRD-1001 style id
#   add_product()        - save a brand new product
#   update_product()     - change an existing product
#
# Both add and update write straight back to products.csv, so the change is
# permanent. They never touch history.csv or interactions.csv, so customer
# behaviour recorded for a Product ID is never lost.
# ---------------------------------------------------------------------------


def check_admin_login(username, password):
    """
    Return True only when the username and password both match.

    This is deliberately the simplest possible check. It is fine for a college
    demonstration, but a real website would need proper hashed passwords.
    """
    return str(username).strip() == ADMIN_USERNAME and str(password) == ADMIN_PASSWORD


def generate_product_id(products=None):
    """
    Return the next free product id: PRD-1001, PRD-1002, PRD-1003 ...

    We start at 1001 and keep going until we find an id that is not in the
    catalogue yet, so an id can never be used twice.
    """
    if products is None:
        products = load_products()

    existing_ids = set(products["Product_ID"].astype(str))

    number = 1001
    while f"{ADMIN_PRODUCT_ID_PREFIX}{number}" in existing_ids:
        number += 1

    return f"{ADMIN_PRODUCT_ID_PREFIX}{number}"


def _clean_text(value):
    """Trim a text box value and turn it into a plain string."""
    if value is None:
        return ""
    return str(value).strip()


def validate_product(name, category, price, image, description):
    """
    Check what the admin typed. Returns an error message, or "" when it is fine.
    """
    if not _clean_text(name):
        return "Please enter a product name."

    if len(_clean_text(name)) < 3:
        return "The product name must be at least 3 characters long."

    if _clean_text(category) not in PRODUCT_CATEGORIES:
        return "Please choose a category from the list."

    try:
        price_value = float(_clean_text(price))
    except (TypeError, ValueError):
        return "Please enter the price as a number, for example 2499."

    if price_value <= 0:
        return "The price must be more than zero."

    if price_value > 10000000:
        return "That price looks too high. Please enter a normal price."

    image_text = _clean_text(image)
    if image_text:
        if not image_text.lower().startswith(("http://", "https://")):
            return "The image must be a web address starting with http:// or https://."
        if len(image_text) > 500:
            return "That image address is too long."

    if not _clean_text(description):
        return "Please enter a short description."

    if len(_clean_text(description)) > 1000:
        return "Please keep the description under 1000 characters."

    return ""


def add_product(name, category, price, image="", description=""):
    """
    Save a brand new product to products.csv.

    Returns (product_id, error_message). On success the error message is "" and
    the new product_id is the id that was created. The product is written to the
    catalogue immediately, so the recommendation system can score it straight
    away - it is never hardcoded anywhere in the app.
    """
    error = validate_product(name, category, price, image, description)
    if error:
        return None, error

    products = load_products()

# do not allow the same name twice, otherwise the catalogue gets confusing
    same_name = (
        products["Product_Name"].astype(str).str.strip().str.lower()
        == _clean_text(name).lower()
    )
    if same_name.any():
        return None, "A product with that name already exists. Use Edit Product instead."

    new_id = generate_product_id(products)

    # an emoji is used when the admin leaves the image box empty, so the card
    # still shows a picture instead of a blank space
    image_text = _clean_text(image) or "🆕"

    new_row = {
        "Product_ID": new_id,
        "Product_Name": _clean_text(name),
        "Product_Category": _clean_text(category),
        "Product_Price": float(_clean_text(price)),
        "Product_Image": image_text,
        # a stable colour for the card, derived from the new id
        "Hue": zlib.crc32(new_id.encode("utf-8")) % 360,
        "Brand": "",
        "MRP": "",
        "Rating": "",
        "Reviews": "",
        "Description": _clean_text(description),
        "Highlights": "",
        "Colours": "",
        "Sizes": "",
        "Warranty": "",
        "Delivery_Days": "",
        "Stock": "",
    }

    products = pd.concat([products, pd.DataFrame([new_row])], ignore_index=True)

    # fill in the blanks (brand, colours, sizes, warranty, ...) exactly once
    write_csv(enrich_catalogue(products), PRODUCTS_FILE)
    return new_id, ""


def update_product(product_id, name, category, price, image="", description=""):
    """
    Save changes to an existing product.

    The Product ID is deliberately NOT a parameter - it can never be changed,
    because the recommendation system and every interaction row use it as the
    permanent key. Returns (True, message) or (False, error_message).
    """
    products = load_products()

    position = products.index[products["Product_ID"] == product_id]
    if len(position) == 0:
        return False, f"Product {product_id} was not found."
    position = position[0]

    error = validate_product(name, category, price, image, description)
    if error:
        return False, error

    price_value = float(_clean_text(price))
    old_price = float(products.at[position, "Product_Price"])

    # The CSV was read as whole numbers, so Product_Price starts out as an int
    # column. Turn it into a float column first, otherwise saving a price with
    # paise (1234.50) would fail because it does not fit in an int column.
    products["Product_Price"] = products["Product_Price"].astype(float)
    products["MRP"] = products["MRP"].astype(float)

    products.at[position, "Product_Name"] = _clean_text(name)
    products.at[position, "Product_Category"] = _clean_text(category)
    products.at[position, "Product_Price"] = price_value

    image_text = _clean_text(image)
    if image_text:
        products.at[position, "Product_Image"] = image_text

    products.at[position, "Description"] = _clean_text(description)

    # the price moved, so the "was" price has to move with it
    if price_value != old_price:
        mrp = float(products.at[position, "MRP"] or 0)
        if mrp <= price_value:
            # keep a believable 10% to 45% discount above the new price
            products.at[position, "MRP"] = round(price_value * 1.3, 2)

    write_csv(enrich_catalogue(products), PRODUCTS_FILE)
    return True, f"{product_id} was updated."


# ---------------------------------------------------------------------------
# 8. MARKETPLACE PRICES ("WHERE TO BUY")
# ---------------------------------------------------------------------------
# One row = one product offered on one shopping platform. Nothing here is ever
# invented: prices and URLs only appear because an admin (or the seed file)
# put a real listing into the CSV. The page sorts the rows by price.


MARKETPLACE_FILE = os.path.join(BASE_DIR, "marketplace_prices.csv")

# Product_ID | Platform | Price | Product_URL | Checked_On
MARKETPLACE_COLUMNS = [
    "Product_ID",
    "Platform",
    "Price",
    "Product_URL",
    "Checked_On",
]

# the only platforms SMARTREC knows about - anything else is refused
MARKETPLACE_PLATFORMS = ["Amazon", "Flipkart", "Croma"]


def load_marketplace():
    """Every marketplace listing in the file (empty DataFrame if none yet)."""
    return read_csv_or_empty(MARKETPLACE_FILE, MARKETPLACE_COLUMNS)


def save_marketplace(marketplace):
    """Save the whole marketplace table back to the CSV file."""
    write_csv(marketplace, MARKETPLACE_FILE)


def marketplace_for(product_id):
    """
    The listings for one product, sorted from the cheapest to the dearest.
    The cheapest row is always first, which is what the "Where to Buy" box
    shows as the BEST PRICE.
    """
    marketplace = load_marketplace()
    if len(marketplace) == 0:
        return pd.DataFrame(columns=MARKETPLACE_COLUMNS)

    rows = marketplace[marketplace["Product_ID"] == product_id].copy()
    rows["Price"] = rows["Price"].astype(float)
    return rows.sort_values("Price").reset_index(drop=True)


def validate_marketplace(product_id, platform, price, url):
    """Check the admin's marketplace entry. Returns "" when it is fine."""
    if product_id not in list(load_products()["Product_ID"]):
        return "That product does not exist in the catalogue."

    if platform not in MARKETPLACE_PLATFORMS:
        return "Please choose a platform from the list."

    try:
        price_value = float(_clean_text(price))
    except (TypeError, ValueError):
        return "Please enter the price as a number, for example 2399."

    if price_value <= 0:
        return "The price must be more than zero."

    url_text = _clean_text(url)
    if not url_text.lower().startswith(("http://", "https://")):
        return "Please enter the product URL starting with http:// or https://."

    return ""


def add_marketplace(product_id, platform, price, url):
    """
    Save one product-platform listing. If that platform already has a row for
    the product, it just updates the price and the URL (there is only ever one
    row per product + platform). Returns (True, message) or (False, error).
    """
    error = validate_marketplace(product_id, platform, price, url)
    if error:
        return False, error

    marketplace = load_marketplace()
    price_value = float(_clean_text(price))
    url_text = _clean_text(url)

    matching = (marketplace.get("Product_ID") == product_id) & (
        marketplace.get("Platform") == platform
    )

    new_row = {
        "Product_ID": product_id,
        "Platform": platform,
        "Price": price_value,
        "Product_URL": url_text,
        "Checked_On": date.today().isoformat(),
    }

    if marketplace is not None and len(marketplace) > 0 and matching.any():
        marketplace.loc[matching, "Price"] = price_value
        marketplace.loc[matching, "Product_URL"] = url_text
        marketplace.loc[matching, "Checked_On"] = date.today().isoformat()
        save_marketplace(marketplace)
        return True, f"{platform} listing for {product_id} was updated."
    else:
        marketplace = pd.concat(
            [marketplace, pd.DataFrame([new_row])], ignore_index=True
        )
        save_marketplace(marketplace)
        return True, f"{platform} listing for {product_id} was saved."


def remove_marketplace(product_id, platform):
    """Delete the listing for one product + platform. Returns (ok, message)."""
    marketplace = load_marketplace()
    if len(marketplace) == 0:
        return False, "There are no marketplace listings to remove."

    matching = (marketplace["Product_ID"] == product_id) & (
        marketplace["Platform"] == platform
    )
    if not matching.any():
        return False, f"No {platform} listing exists for {product_id}."

    marketplace = marketplace[~matching]
    save_marketplace(marketplace)
    return True, f"The {platform} listing for {product_id} was removed."
