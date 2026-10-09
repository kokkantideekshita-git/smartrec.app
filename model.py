"""
SMARTREC - "Your shopping, made smarter."
=========================================
model.py
--------
This is the MACHINE LEARNING part of SMARTREC.

The idea in one picture:

    customer data + product data
            |
            v
    FEATURE ENGINEERING      (turn the raw numbers into useful columns)
            |
            v
    LOGISTIC REGRESSION      (learns from the historical data)
            |
            v
    PURCHASE PROBABILITY     (predict_proba -> 0.78 means 78% chance)
            |
            v
    RANKED TOP 5

Why Logistic Regression?
    1. It is easy to explain.
    2. It gives a real PROBABILITY for every product (predict_proba()).
    3. It is fast and does not need a GPU.

IMPORTANT: nothing in this file is hardcoded. Every number you see in the
app is calculated from the historical CSV data by the trained model.
"""

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import data as data_layer

# ---------------------------------------------------------------------------
# THE FEATURES USED BY THE MODEL
# ---------------------------------------------------------------------------
# Numeric features (numbers) and the one categorical feature (product category).
# ---------------------------------------------------------------------------

NUMERIC_FEATURES = [
    "Views",                     # how many times this customer saw the product
    "Cart_Adds",                 # how many times it went into the cart
    "View_To_Cart_Rate",         # cart adds divided by views (real buying intent)
    "Previous_Purchases",        # how many products this customer bought before
    "Product_Price",             # price of the product
    "Price_To_Max_Budget",       # price compared with the customer's budget
    "Budget_Fit",                # 1 if the price sits inside the budget
    "Customer_Total_Views",      # overall browsing behaviour of the customer
    "Customer_Total_Cart_Adds",
    "Customer_Total_Purchases",  # buying power / experience of the customer
    "Customer_Avg_Price",        # average price this customer usually looks at
    "Category_Preference",       # how much this customer likes this category
    "Preferred_Category_Match",  # category chosen on the sign-up form
    "Product_Popularity",        # how often everyone looks at this product
    "Product_Purchase_Rate",     # how often this product gets bought (history)
    "Category_Purchase_Rate",    # how often this category gets bought (history)
    "Price_vs_Category_Avg",     # is this product cheap or costly for its category
]

CATEGORICAL_FEATURES = ["Product_Category"]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


# ---------------------------------------------------------------------------
# SMALL HELPER: "leave one out" sums
# ---------------------------------------------------------------------------
# When we build features for a row we must not use that row's own answer.
# Otherwise the model would cheat (it would learn that a purchase means a
# purchase).  The helper below subtracts the row's own value from the group
# total, which is a simple and well known way to avoid that.
# ---------------------------------------------------------------------------


def _leave_one_out_sum(dataframe, value_column, group_column, own_column):
    group_total = dataframe.groupby(group_column)[value_column].transform("sum")
    return (group_total - dataframe[own_column]).clip(lower=0)


def _before_this_event(dataframe, value_column, group_column, own_column):
    """
    "What had this customer already done BEFORE this interaction?"

    The rows are sorted by Event_Order (the order the events really happened),
    then a running total is built. Subtracting the row's own value gives the
    total the customer had before this event.

    This is also what makes cold start work: for the very first event of a
    customer the value is 0, exactly like a brand new SMARTREC customer.
    """
    running_total = dataframe.groupby(group_column)[value_column].cumsum()
    return (running_total - dataframe[own_column]).clip(lower=0)


def _leave_one_out_mean(dataframe, value_column, group_column, own_value_column, own_count=True):
    """Average value of the group without this row's own value."""
    total = _leave_one_out_sum(dataframe, value_column, group_column, own_value_column)
    if own_count:
        counts = dataframe.groupby(group_column)[value_column].transform("count") - 1
    else:
        counts = dataframe.groupby(group_column)[value_column].transform("count")
    counts = counts.clip(lower=1)
    return total / counts


# ---------------------------------------------------------------------------
# STEP 1 + 2 : FEATURE ENGINEERING FOR THE HISTORICAL DATA
# ---------------------------------------------------------------------------


def build_training_features(history):
    """
    Take the cleaned history and create every feature column.

    These "before this event" features make sure the model learns real
    patterns instead of memorising the answer column.
    """
    # the order of the events matters, so keep the real chronology
    features = history.sort_values(["Customer_ID", "Event_Order"]).reset_index(drop=True)

    # remember whether this row was a purchase (used only to hide it later)
    features["_own_purchased"] = (features["Purchases"] > 0).astype(int)

    # ---- what the customer had already done BEFORE this interaction -------
    features["Customer_Total_Views"] = _before_this_event(
        features, "Views", "Customer_ID", "Views"
    )
    features["Customer_Total_Cart_Adds"] = _before_this_event(
        features, "Cart_Adds", "Customer_ID", "Cart_Adds"
    )
    features["Customer_Total_Purchases"] = _before_this_event(
        features, "_own_purchased", "Customer_ID", "_own_purchased"
    )

    # average price this customer usually browses (price of rows they viewed)
    features["_viewed_price"] = features["Product_Price"] * (features["Views"] > 0).astype(int)
    features["_viewed_flag"] = (features["Views"] > 0).astype(int)
    viewed_total = _before_this_event(features, "_viewed_price", "Customer_ID", "_viewed_price")
    viewed_count = _before_this_event(features, "_viewed_flag", "Customer_ID", "_viewed_flag")
    features["Customer_Avg_Price"] = np.where(
        viewed_count > 0,
        viewed_total / np.where(viewed_count == 0, 1, viewed_count),
        0.0,
    )

    # ---- how much this customer likes each category (before this event) ----
    features["_category_count"] = 1
    features["Customer_Interactions"] = _before_this_event(
        features, "_category_count", "Customer_ID", "_category_count"
    )
    features["_category_same"] = features.groupby(
        ["Customer_ID", "Product_Category"]
    ).cumcount()
    features["Category_Preference"] = np.where(
        features["Customer_Interactions"] > 0,
        features["_category_same"] / features["Customer_Interactions"].replace(0, 1),
        0.0,
    )
    features["Category_Preference"] = features["Category_Preference"].clip(0, 1)

    # ---- product level statistics (without this row) ---------------------
    features["Product_Popularity"] = _leave_one_out_mean(
        features, "Views", "Product_ID", "Views"
    ).fillna(0)

    # (the helper already divides by "group size - 1", which is exactly the
    #  leave-one-out purchase rate)
    features["Product_Purchase_Rate"] = _leave_one_out_mean(
        features, "_own_purchased", "Product_ID", "_own_purchased"
    ).fillna(0)

    features["Category_Purchase_Rate"] = _leave_one_out_mean(
        features, "_own_purchased", "Product_Category", "_own_purchased"
    ).fillna(0)

    category_average_price = _leave_one_out_mean(
        features, "Product_Price", "Product_Category", "Product_Price"
    ).fillna(features["Product_Price"].median())
    features["Price_vs_Category_Avg"] = (
        features["Product_Price"] / category_average_price.replace(0, np.nan)
    ).fillna(1.0)

    # ---- simple ratios and budget features -------------------------------
    features["View_To_Cart_Rate"] = features["Cart_Adds"] / (features["Views"] + 1)
    features["Price_To_Max_Budget"] = features["Product_Price"] / (
        features["Max_Budget"].replace(0, np.nan)
    ).fillna(1.0)
    features["Budget_Fit"] = (
        (features["Product_Price"] >= features["Min_Budget"])
        & (features["Product_Price"] <= features["Max_Budget"])
    ).astype(int)

    features = features.drop(
        columns=["_own_purchased", "_viewed_price", "_viewed_flag", "_category_count", "_category_same"]
    )
    return features


# ---------------------------------------------------------------------------
# STEP 3 : PRODUCT / CATEGORY STATISTICS FROM THE HISTORY
# ---------------------------------------------------------------------------
# These statistics are learned from the historical data and used both as model
# features and to build honest "Why this product?" explanations.
# ---------------------------------------------------------------------------


def learn_product_statistics(history):
    """Average popularity and purchase rate of every product and category."""
    product_stats = (
        history.groupby("Product_ID")
        .agg(
            Avg_Views=("Views", "mean"),
            Avg_Cart_Adds=("Cart_Adds", "mean"),
            Purchase_Rate=("Purchased", "mean"),
            Times_Viewed=("Views", "sum"),
        )
        .reset_index()
    )

    category_stats = (
        history.groupby("Product_Category")
        .agg(
            Avg_Views=("Views", "mean"),
            Purchase_Rate=("Purchased", "mean"),
            Avg_Price=("Product_Price", "mean"),
        )
        .reset_index()
    )

    return product_stats, category_stats


# ---------------------------------------------------------------------------
# STEP 4 : BUILD THE CANDIDATE ROWS FOR A REAL CUSTOMER
# ---------------------------------------------------------------------------
# For a live customer we combine:
#   customer profile  (budget, preferred categories)
#   customer behaviour (views, cart adds, purchases, history)
#   product information (price, category, popularity from the history)
# ---------------------------------------------------------------------------


def build_customer_candidates(customer, customer_interactions, products, product_stats, category_stats):
    """
    Create one row of features for EVERY product this customer could buy.

    Products the customer already bought are removed - recommending something
    they already own makes no sense.
    """
    bought_ids = set(
        customer_interactions.loc[
            customer_interactions["Purchases"] > 0, "Product_ID"
        ].tolist()
    )

    candidates = products[~products["Product_ID"].isin(bought_ids)].copy()
    if len(candidates) == 0:
        return pd.DataFrame(columns=ALL_FEATURES + ["Product_ID"])

    customer_id = customer["Customer_ID"]
    min_budget = float(customer.get("Min_Budget", 0) or 0)
    max_budget = float(customer.get("Max_Budget", 10000) or 10000)
    if max_budget <= 0:
        max_budget = 10000

    preferred_categories = data_layer.parse_categories(customer.get("Categories", ""))

    # ---------- what has this customer already done with each product? -----
    views_by_product = dict(zip(customer_interactions["Product_ID"], customer_interactions["Views"]))
    cart_by_product = dict(zip(customer_interactions["Product_ID"], customer_interactions["Cart_Adds"]))

    customer_views = float(customer.get("Views", 0) or 0)
    customer_cart_adds = float(customer.get("Cart_Adds", 0) or 0)
    customer_purchases = float(customer.get("Purchases", 0) or 0)
    previous_purchases = float(customer.get("Previous_Purchases", customer_purchases) or 0)

    # average price the customer is used to (from what they actually browsed)
    browsed_prices = []
    for _, row in customer_interactions.iterrows():
        browsed_prices.extend([row["Product_Price"]] * int(row["Views"]))

    if browsed_prices:
        customer_avg_price = float(np.mean(browsed_prices))
    else:
        # A customer with no browsing history yet: use the real average price
        # of the categories they selected on the registration form.
        preferred = data_layer.parse_categories(customer.get("Categories", ""))
        relevant = products[products["Product_Category"].isin(preferred)]
        if len(relevant) == 0:
            relevant = products
        customer_avg_price = float(relevant["Product_Price"].mean())

    # how much of their behaviour belongs to each category
    category_totals = (
        customer_interactions.groupby("Product_Category")["Views"].sum().to_dict()
        if len(customer_interactions) > 0
        else {}
    )
    overall_views = max(sum(category_totals.values()), 1)

    rows = []
    for _, product in candidates.iterrows():
        product_id = product["Product_ID"]
        views = float(views_by_product.get(product_id, 0))
        cart_adds = float(cart_by_product.get(product_id, 0))

        stats = product_stats[product_stats["Product_ID"] == product_id]
        if len(stats) > 0:
            product_popularity = float(stats.iloc[0]["Avg_Views"])
            product_purchase_rate = float(stats.iloc[0]["Purchase_Rate"])
        else:
            product_popularity = 0.0
            product_purchase_rate = 0.0

        category_row = category_stats[category_stats["Product_Category"] == product["Product_Category"]]
        if len(category_row) > 0:
            category_purchase_rate = float(category_row.iloc[0]["Purchase_Rate"])
            category_avg_price = float(category_row.iloc[0]["Avg_Price"])
        else:
            category_purchase_rate = 0.0
            category_avg_price = float(product["Product_Price"])

        price = float(product["Product_Price"])

        # how much this customer likes this category (from their own browsing)
        own_category_views = float(category_totals.get(product["Product_Category"], 0))
        category_preference = own_category_views / overall_views

        # a brand-new customer still gets a small preference for the categories
        # they selected on the registration form
        if product["Product_Category"] in preferred_categories:
            category_preference = min(1.0, category_preference + 0.25)

        rows.append(
            {
                "Customer_ID": customer_id,
                "Product_ID": product_id,
                "Product_Category": product["Product_Category"],
                "Product_Price": price,
                "Views": views,
                "Cart_Adds": cart_adds,
                "View_To_Cart_Rate": cart_adds / (views + 1),
                "Previous_Purchases": previous_purchases,
                "Price_To_Max_Budget": price / max_budget,
                "Budget_Fit": int(min_budget <= price <= max_budget),
                "Customer_Total_Views": customer_views,
                "Customer_Total_Cart_Adds": customer_cart_adds,
                "Customer_Total_Purchases": customer_purchases,
                "Customer_Avg_Price": customer_avg_price,
                "Category_Preference": category_preference,
                "Preferred_Category_Match": int(product["Product_Category"] in preferred_categories),
                "Product_Popularity": product_popularity,
                "Product_Purchase_Rate": product_purchase_rate,
                "Category_Purchase_Rate": category_purchase_rate,
                "Price_vs_Category_Avg": price / category_avg_price if category_avg_price else 1.0,
                "Min_Budget": min_budget,
                "Max_Budget": max_budget,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# STEP 5 : TRAIN THE MODEL
# ---------------------------------------------------------------------------


def train_smartrec_model():
    """
    Train the Logistic Regression model on the historical data.

    Returns a "bundle" dictionary that contains the trained model, the
    evaluation metrics and everything needed to score real customers.
    """
    # --- load + clean the historical data ---------------------------------
    raw_history = data_layer.read_csv_or_empty(data_layer.HISTORY_FILE, None)
    history, cleaning_report = data_layer.clean_history(raw_history)

    # --- feature engineering ----------------------------------------------
    training_features = build_training_features(history)

    X = training_features[ALL_FEATURES]
    y = training_features["Purchased"].astype(int)

    # --- train / test split -----------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- pipeline: scale numbers, one-hot encode the category --------------
    # drop="first" removes the first category column on purpose. Without it the
    # model would have duplicated information (the classic "dummy trap") and the
    # coefficients would become meaningless.
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            (
                "category",
                OneHotEncoder(handle_unknown="ignore", drop="first"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    classifier = LogisticRegression(
        max_iter=5000,
        class_weight="balanced",
        C=0.08,              # a little regularisation keeps the weights honest
        solver="lbfgs",
    )

    model = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])
    model.fit(X_train, y_train)

    # --- evaluation on the test set (real numbers, never hardcoded) -------
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probabilities),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "train_accuracy": accuracy_score(y_train, model.predict(X_train)),
    }

    confusion = confusion_matrix(y_test, predictions)
    false_positive_rate, true_positive_rate, _ = roc_curve(y_test, probabilities)

    # --- feature importance = the model's own coefficients ----------------
    encoded_names = model.named_steps["preprocessor"].get_feature_names_out()
    coefficients = model.named_steps["classifier"].coef_[0]
    importance = (
        pd.DataFrame(
            {
                "Feature": [name.replace("numeric__", "").replace("category__", "") for name in encoded_names],
                "Coefficient": coefficients,
            }
        )
        .assign(Importance=lambda frame: frame["Coefficient"].abs())
        .sort_values("Importance", ascending=False)
        .reset_index(drop=True)
    )

    product_stats, category_stats = learn_product_statistics(history)

    return {
        "model": model,
        "metrics": metrics,
        "confusion_matrix": confusion,
        "roc_curve": (false_positive_rate, true_positive_rate),
        "feature_importance": importance,
        "cleaning_report": cleaning_report,
        "history": history,
        "product_stats": product_stats,
        "category_stats": category_stats,
        "trained_on": pd.Timestamp.now().strftime("%d %b %Y, %I:%M %p"),
    }


# ---------------------------------------------------------------------------
# STEP 6 : PREDICT AND RANK
# ---------------------------------------------------------------------------


def score_products(bundle, customer, customer_interactions):
    """
    Calculate the real purchase probability for every available product and
    rank them from best to worst.

    Returns a DataFrame with the product details + the ML probability.
    """
    products = data_layer.load_products()

    candidates = build_customer_candidates(
        customer,
        customer_interactions,
        products,
        bundle["product_stats"],
        bundle["category_stats"],
    )

    if len(candidates) == 0:
        return pd.DataFrame()

    # ---- the actual ML prediction ----------------------------------------
    model_features = candidates[ALL_FEATURES]
    probabilities = bundle["model"].predict_proba(model_features)[:, 1]
    candidates["Purchase_Probability"] = probabilities

    # add the product details we want to show
    candidates = candidates.merge(
        products[["Product_ID", "Product_Name", "Product_Image", "Hue"]],
        on="Product_ID",
        how="left",
    )

    # ---- rank: highest probability first ---------------------------------
    ranked = candidates.sort_values(
        by=["Purchase_Probability", "Product_Popularity"],
        ascending=[False, False],
    ).reset_index(drop=True)
    ranked["Rank"] = ranked.index + 1

    return ranked


def top_recommendations(ranked, number=5):
    """The Top N products of the ranked list."""
    return ranked.head(number).copy()


# ---------------------------------------------------------------------------
# STEP 7 : HONEST "WHY THIS PRODUCT?" EXPLANATIONS
# ---------------------------------------------------------------------------
# Every reason below is only shown when the stored data really supports it.
# Nothing is invented.
# ---------------------------------------------------------------------------


def build_reasons(product_row, customer, customer_interactions, bundle):
    """Return a list of real reasons for one recommended product."""
    reasons = []
    product_category = product_row["Product_Category"]
    price = float(product_row["Product_Price"])
    product_id = product_row["Product_ID"]

    preferred_categories = data_layer.parse_categories(customer.get("Categories", ""))
    min_budget = float(customer.get("Min_Budget", 0) or 0)
    max_budget = float(customer.get("Max_Budget", 0) or 0)

    # 1. preferred category chosen at registration
    if product_category in preferred_categories:
        reasons.append(f"Matches your preferred category — you selected {product_category} at sign-up")

    # 2. category the customer actually browses
    if len(customer_interactions) > 0:
        category_views = customer_interactions[
            customer_interactions["Product_Category"] == product_category
        ]["Views"].sum()
        if category_views > 0:
            reasons.append(
                f"You have viewed {int(category_views)} {product_category.lower()} product(s) before"
            )

        # 3. previous purchases in the same category
        bought = customer_interactions[
            (customer_interactions["Product_Category"] == product_category)
            & (customer_interactions["Purchases"] > 0)
        ]
        if len(bought) > 0:
            reasons.append(
                f"Similar to your previous purchases — you already bought {len(bought)} "
                f"{product_category.lower()} product(s)"
            )

        # 4. this exact product is already in the customer's history
        own_row = customer_interactions[customer_interactions["Product_ID"] == product_id]
        if len(own_row) > 0:
            row = own_row.iloc[0]
            if row["Purchases"] > 0:
                pass  # purchased products are never recommended
            elif row["Cart_Adds"] > 0:
                reasons.append("You added this to your cart earlier but have not bought it yet")
            elif row["Views"] > 0:
                reasons.append(f"You viewed this product {int(row['Views'])} time(s) already")

        # 5. similar price to what the customer usually looks at
        # (computed from the prices this customer really interacted with)
        average_price = 0.0
        if len(customer_interactions) > 0 and "Product_Price" in customer_interactions.columns:
            seen_prices = pd.to_numeric(
                customer_interactions["Product_Price"], errors="coerce"
            ).dropna()
            if len(seen_prices) > 0:
                average_price = float(seen_prices.mean())
        if average_price > 0 and 0.7 <= price / average_price <= 1.4:
            reasons.append(
                f"Similar price to what you usually browse (your average item is ₹{average_price:,.0f})"
            )

    else:
        reasons.append("First recommendation - picked from the categories you selected")

    # 6. budget fit (always check the real budget numbers)
    if min_budget <= price <= max_budget:
        reasons.append(f"Fits your preferred price range (₹{min_budget:,.0f} - ₹{max_budget:,.0f})")
    elif price < min_budget and min_budget > 0:
        reasons.append(f"Priced below your usual range at ₹{price:,.0f} - good value")

    # 7. popularity learned from the historical data
    popularity = float(product_row.get("Product_Popularity", 0) or 0)
    if popularity >= bundle["product_stats"]["Avg_Views"].median():
        reasons.append(
            f"Popular on SMARTREC - customers view this product about {popularity:.0f} times"
        )

    # 8. how often it gets bought, straight from the history
    purchase_rate = float(product_row.get("Product_Purchase_Rate", 0) or 0)
    if purchase_rate >= bundle["history"]["Purchased"].mean():
        reasons.append(
            f"{purchase_rate * 100:.0f}% of past interactions with this product ended in a purchase"
        )

    if len(reasons) == 0:
        reasons.append("Recommended by the SMARTREC model from overall customer behaviour")

    return reasons


# ---------------------------------------------------------------------------
# STEP 8 : SMALL SUMMARIES USED BY THE DASHBOARD
# ---------------------------------------------------------------------------


def behaviour_summary(customer):
    """A short summary of one customer's stored behaviour (real CSV numbers)."""
    views = float(customer.get("Views", 0) or 0)
    cart_adds = float(customer.get("Cart_Adds", 0) or 0)
    purchases = float(customer.get("Purchases", 0) or 0)

    conversion = (purchases / cart_adds * 100) if cart_adds > 0 else 0.0

    return {
        "views": int(views),
        "cart_adds": int(cart_adds),
        "purchases": int(purchases),
        "total_spend": float(customer.get("Total_Spend", 0) or 0),
        "cart_conversion": round(conversion, 1),
    }