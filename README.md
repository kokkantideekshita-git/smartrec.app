# ✦ SMARTREC

**Your shopping, made smarter.**

SMARTREC is a complete e-commerce recommendation web app built with Streamlit and a
real Logistic Regression machine-learning model. Every product recommendation is
scored by the model — nothing on screen is hardcoded.

A customer signs up, gets a permanent `SMR-XXXX` ID, and instantly receives a ranked
**Top 5 recommendation list** based on their interests, budget, and real shopping
behaviour (views, cart adds and purchases) that SMARTREC records on every click.

---

## ✨ What the app does

| Feature | Where | What actually happens |
|---|---|---|
| **New customer sign-up** | Home → 🆕 New Customer | Saves a profile, generates a unique `SMR-XXXX` ID, gives the customer their ID to keep |
| **Returning customer login** | Home → 👤 Existing Customer | Looks the ID up in `customers.csv`, rebuilds the saved behaviour, shows personalised greeting |
| **Top 5 recommendations** | 🛍️ Recommendations | `predict_proba()` ranks all 51 products; already-purchased products are removed |
| **Real behaviour tracking** | 🔎 View details / 🛒 Cart / 💳 Buy | Each click is written to `interactions.csv` and updates the customer's profile; View details also opens that product's full page |
| **Product detail page** | 🔎 View details on any card | Photo, price, MRP, discount, rating, stock, delivery, warranty, colour/size/quantity options, offers and highlights |
| **Where to buy / compare prices** | 🛍️ Where to buy on every product page | Real stored listings from Amazon / Flipkart / Croma, sorted cheapest → dearest, BEST PRICE tagged, BUY NOW opens the exact product page in a new tab |
| **Shopping cart** | 🛒 Cart (only after login) | Real persistent cart in `cart.csv` with quantity editing, option choices, live totals and checkout |
| **Admin customer management** | ⚙️ Admin → 👥 Customers | Admin can confirm deletion of a customer profile, cart and interaction history; deleted IDs remain reserved |
| **"Why this product?"** | Expandable on every card | Reasons are printed **only** when the stored data really supports them |
| **AI Insights dashboard** | 📊 AI Insights | Live metrics, confusion matrix, ROC curve, feature coefficients, category & price breakdowns |
| **How It Works** | 🧠 How It Works | Plain-English explanation of the whole pipeline |
| **About** | ℹ️ About | Tech stack, model type, honest limitations |
| **Light / dark theme** | 🌙 / ☀️ button in the navbar | Full palette swap, not just a background colour |
| **Browse all 51 products** | Recommendations page | Search, category filter, sort by price / popularity / rating |

The recommendation page **never shows a probability** on the cards — that would break
the point of the model. Real percentages appear only on the AI Insights page.

---

## 🚀 How to run it

You need **Python 3.10 or newer** (tested on Python 3.14).

```bash
# 1. open a terminal in this folder
cd "Default Project"

# 2. (recommended) create a virtual environment
python -m venv .venv

# 3. activate it
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 4. install the libraries
pip install -r requirements.txt

# 5. start the app
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

**The first run takes 20–60 seconds.** SMARTREC has to generate the catalogue and the
historical behaviour dataset and then train the model before the first page can render.

---

## 👤 Built by

| | |
|---|---|
| **Name** | Deekshita Kokkanti |
| **College** | VIT-CHENNAI |
| **Department** | Computer Science Core |
| **Role** | Solo Developer — data generation, ML model, storage, and the full web interface |

---

## 🧠 How the recommendation actually works

### 1. The data

SMARTREC ships with a **self-generated historical dataset** (`history.csv`), so the
project runs offline with no downloads and no manual data collection.

It is generated to look like real shopping data, not like random noise:

- **900 historical customers** with declared interests, budgets, and city/tier info
- **51 real products** across 6 categories (Electronics, Gaming, Fashion, Books, Home, Accessories)
- **Behavioural events** — impressions, views, cart adds and purchases
- **Recommendation impressions** — products *shown* to a customer with no interaction
  (this is what makes genuine cold-start prediction possible)
- **Hidden product truth** — every product has a real latent quality and popularity that
  drives whether a purchase happens, so the model has something real to learn
- **Deliberate messiness** — missing values, duplicate rows and inconsistent formatting
  that `data.clean_history()` has to fix

### 2. Cleaning

`data.clean_history()` removes duplicates (merging their counters), converts types,
fills missing values with sensible defaults, and drops rows that cannot be used. The
Insights page reports how many rows were removed — those numbers are read from the
data, not typed in.

### 3. Features (18 in total)

For every **customer × product** pair the model is given **17 numeric features + 1
categorical feature**:

- product behaviour — `Views`, `Cart_Adds`, `View_To_Cart_Rate`, `Product_Popularity`,
  `Product_Purchase_Rate`
- price context — `Product_Price`, `Price_To_Max_Budget`, `Budget_Fit`, `Price_vs_Category_Avg`
- customer behaviour *before this event* — `Previous_Purchases`,
  `Customer_Total_Views`, `Customer_Total_Cart_Adds`, `Customer_Total_Purchases`,
  `Customer_Avg_Price`
- category context — `Category_Preference`, `Preferred_Category_Match`,
  `Category_Purchase_Rate`
- categorical — `Product_Category`

Two deliberate anti-cheating rules:

1. **`Purchases` itself is never a feature.** Using it would leak the answer.
2. **Cumulative customer features are "before this event" only.** They are computed
   with a chronological `cumsum`, so a brand-new customer (all zeros) is scored
   exactly like a real first-time visitor instead of inheriting the dataset's totals.

### 4. The model

```text
ColumnTransformer(StandardScaler for numbers, OneHotEncoder(drop="first") for category)
    └── LogisticRegression(max_iter=5000, class_weight="balanced", C=0.08)
```

Predictions come from `model.predict_proba()`. The model is trained on an 80/20
chronological-style split and evaluated on data it has never seen. Expect accuracy in
the mid-70s, F1 around 0.73 and ROC-AUC around 0.82 — the exact numbers are recomputed
live on every run and displayed on the Insights page.

**Why the probabilities look low:** they are honest. Only a minority of interactions end
in a purchase, so a cold-start shopper's top product sits around **15–25%**, and rises
to roughly **35–45%** after browsing and cart activity. The Insights page plots
predicted probability against actual outcomes, and the two track each other closely —
that is real calibration, not decoration.

### 5. Personalisation

Nothing about the recommendation list is static. As you view, add to cart and buy:

- your stored counters increase and are written to disk
- your `Customer_Total_*` features increase, which moves the probability
- products you already bought are **removed** from all future recommendations
- a returning customer gets a different, better-ranked list than on day one

---

## 📁 Project structure

```text
Default Project/
├── app.py           # Streamlit app: all pages, navigation, forms, filters, charts
├── data.py          # Product catalogue, dataset generation, cleaning, CSV persistence
├── model.py         # Feature engineering, training, evaluation, ranking, explanations
├── ui.py            # Themes, CSS, animated background, SVG covers, HTML components
├── requirements.txt # Python dependencies
├── .streamlit/
│   └── config.toml  # Light theme colours and server settings
│
├── products.csv     # generated product catalogue (51 products, with shop details)
├── marketplace_prices.csv  # where-to-buy listings (product + store + price + URL + checked date)
├── history.csv      # generated historical behaviour data used for training
├── customers.csv    # customer profiles — created when you sign up
├── interactions.csv # every view / cart add / purchase
└── cart.csv         # every customer's live shopping cart
```

### Where to look first

| File | Read it for |
|---|---|
| `data.py` | how the catalogue and historical data are built, cleaned and saved |
| `model.py` | the ML pipeline, the features, the metrics and the ranking logic |
| `app.py` | the UI flow and all six pages |
| `ui.py` | every colour, gradient, animation and card in the interface |

The code is deliberately written for a beginner to read: sections are numbered with
comment banners, functions are small, and each one has a docstring saying what it does
and what it returns.

---

## 💾 How your data is stored

There is no database and no login password. Four CSV files do the job:

- **`customers.csv`** — one row per customer: name, contact, interested categories,
  budget range, totals (`Views`, `Cart_Adds`, `Purchases`, `Total_Spend`), and dates
- **`interactions.csv`** — one row per customer per product, with the price at the
  time, counters and the last action
- **`products.csv`** — the catalogue, including the shop details shown on each
  product page: `Brand`, `MRP`, `Rating`, `Reviews`, `Description`, `Highlights`,
  `Colours`, `Sizes`, `Warranty`, `Delivery_Days` and `Stock`
- **`cart.csv`** — one row per product a customer has in their cart, with `Quantity`,
  the `Unit_Price` at the time, the chosen `Colour` and `Size`
- **`marketplace_prices.csv`** — one row per product + store listing (`Product_ID`,
  `Platform`, `Price`, `Product_URL`, `Checked_On`); see the Where to buy section below

This means **your data survives a restart**. Close the terminal, run `streamlit run
app.py` again, choose 👤 Existing Customer, enter your ID, and your history and your
cart are exactly where you left them.

Customer IDs are **never reused**: `generate_unique_id()` always scans the file and
returns the next free number.

To start completely fresh, delete `customers.csv`, `interactions.csv` and `cart.csv`
and restart.

---

## 🛒 The cart

The cart is a genuine part of the app, not a demo animation:

- **Login required** — the 🛒 Cart button only appears in the navbar once you are
  signed in, and the navbar button shows your live unit count
- **Persistent** — the cart lives in `cart.csv`, so it survives sign-out and restarts
- **Real options** — colour and size chosen on the product page are stored with the line
- **Real quantity** — change the quantity in the cart; setting it to 0 removes the line
- **Real money** — subtotal, delivery, discount saved and total payable are all computed
  from the stored unit prices
- **Checkout is a real purchase** — every cart line is written to `interactions.csv` and
  `customers.csv`, so the machine learning model immediately learns from the sale

Buying three units records three purchases and three times the spend, not one — the
quantities in the cart are counted as real units throughout.

---

## 🔐 The admin panel

SMARTREC has one hidden admin area where products are added and edited by hand. It is
not part of the customer experience — no navbar button, no admin link on any page except
the home page, and no admin form ever appears for a signed-in customer.

### Getting in

Open the app and click the small **⚙️ Admin** link at the bottom of the home page.

| | |
|---|---|
| Username | `admin` |
| Password | `admin123` |

To use your own login instead of the defaults, set two environment variables before
starting the app:

```powershell
$env:SMARTREC_ADMIN_USER = "your-name"
$env:SMARTREC_ADMIN_PASS = "your-password"
streamlit run app.py
```

This is deliberately simple, first-year-project style: one username and one password
compared against a constant. It is fine for a college demo on a local machine. It is
**not** production security — there are no hashed passwords, no sessions on a server and
no rate limiting, so do not put it on the public internet.

### Adding a product

Fill in the ➕ Add Product form and press **Add product**:

| Field | Rule |
|---|---|
| Product name | Required, at least 3 characters, must not already exist in the catalogue |
| Category | One of the fixed list: Electronics, Gaming, Fashion, Books, Home, Accessories |
| Price (₹) | Required, must be a number greater than 0 |
| Product image URL | Optional, must start with `http://` or `https://` |
| Description | Required — this is the text shown on the product page, so every product has one |

SMARTREC fills in the rest for you: `Brand` comes from the category, `MRP` is set 25%
above the price, and `Rating`, `Reviews`, `Highlights`, `Colours`, `Warranty` and
`Stock` get sensible defaults, so a new product looks complete immediately.

The form is checked before anything is written. A blank name, a price of `abc`, a
duplicate name, a missing description or a bad image link is refused with a clear
message and **nothing is saved**.

Each new product gets its own permanent ID, starting at the first free number:

```
PRD-1001, PRD-1002, PRD-1003, …
```

These are separate from the shop's original `P-1001`, `P-1002`, … IDs, so an added
product never disturbs an existing one.

### Editing a product

The ✏️ Edit Product form changes the name, category, price, image URL and description of
any product, original or added.

Clicking the **✏️ Edit** button on a row opens the Edit Product tab and **smoothly
scrolls the page up to the form**, so the boxes you need are in front of you the moment
you click.

**The Product ID cannot be changed.** It is locked and displayed as 🔒 because that ID
is the key the recommendation model and every customer interaction are stored against.
Editing a product under the same ID means its ratings, its purchase history and its
customers are all kept — the product changes, its history does not.

Only the products in `products.csv` are touched. `customers.csv`, `interactions.csv`,
`cart.csv` and `history.csv` are never opened by the admin panel.

### A new product is a real product

The moment it is saved, `PRD-1001` is a full member of the app:

- it is scored by the Logistic Regression model like any other product
- it is searchable in **Browse all products**
- it has its own detail page with cover, gallery, price, offers and options
- it can be added to a cart and bought like any other product
- a purchase from it trains the model immediately

Because a brand new product has no history, its score starts low and it will not appear
in the default top-12 recommendations straight away — that is the model being honest,
not a bug. Search for its name to find it.

---

## 🛍️ Where to buy / compare prices

Every product page has a **Where to buy** panel that lists the online stores where the
product can be bought, with their prices side by side.

| Situation | What the customer sees |
|---|---|
| **Product with listings** | Stores sorted cheapest → dearest, with 🥇🥈🥉 medals and a **BEST PRICE** tag on the cheapest row |
| **BUY NOW** | Opens that store's **exact product page** in a new browser tab — never a store homepage |
| **Product with no listings** | *"Marketplace availability is currently unavailable."* — nothing is invented |

### Where the prices come from

Listings live in **`marketplace_prices.csv`**, one row per product + store:

```
Product_ID,Platform,Price,Product_URL,Checked_On
```

Only three platforms are allowed — **Amazon**, **Flipkart** and **Croma** — and anything
else is refused. Saving the same product + platform again **updates** the existing row
instead of creating a duplicate, and `Checked_On` is stamped with today's date.

These are **stored prices, not live ones**: SMARTREC never scrapes a shop and never claims
to. The panel shows when each price was last checked, and the admin can update it at any
time. The shipped seed file contains **real, web-verified listings** checked on
**6 Oct 2026** across the catalogue — for example the Sony WH-CH720N headphones
(Flipkart ₹8,986 · JBL Tune 770NC on Croma ₹5,499), boAt Airdopes 141 earbuds
(Amazon ₹799 · Flipkart ₹899), the Logitech G PRO X Superlight 2 mouse
(Amazon ₹14,495, plus G305 on Flipkart and G304 on Croma), the Sony DualSense
controller (Croma ₹6,390) and the SpinBot Astro GX2 pad (Flipkart ₹1,684).
Treat these as sample rows the admin owns — they can be corrected or removed
from the 🏷️ Marketplace prices tab.

### Managing listings (admin)

The admin panel has a **🏷️ Marketplace prices** tab:

- pick a product to see which platforms already have a listing (✓ / ✗)
- add or update a store's price and product URL, or delete a listing
- the price and URL boxes are pre-filled from the existing row, so small fixes are one
  click instead of retyping the whole listing

---

## 🎨 Interface notes

- Custom light **and** dark palettes (CSS variables swapped at runtime)
- Animated gradient background blobs and floating particles
- Generated SVG product covers — one gradient + monogram per product, so there are no
  external image files and nothing to download
- A full product detail page per item, with an image gallery, option pickers and
  colour swatches
- A persistent shopping cart with quantity editing, order summary and checkout
- Ranked Top 5 layout with a highlighted #1 card, then a searchable/filterable grid of
  the whole catalogue
- Plotly charts for the confusion matrix, ROC curve, category and price breakdowns
- Fully responsive from a phone to a large monitor

---

## ⚠️ Honest limitations

- The history is **synthetic**. It is generated to be realistic and learnable, not to be
  a real shopping history. Point the code at a real dataset and it will use that instead.
- One model, one job: Logistic Regression predicting purchase probability. It is
  deliberately simple and explainable rather than a black box.
- Predictions are only as good as the events recorded. A customer who never clicks gets
  cold-start recommendations driven by category, budget and product popularity.
- No passwords and no encryption — the CSV files are plain text, which is fine for a
  demonstration project and not fine for production.
- The app is single-process and in-memory per session; it is not built for thousands of
  concurrent users.

---

## ✅ Verified before delivery

- All six pages, sign-up, login, sign-out, wrong-ID handling and theme switching run
  with **zero exceptions**
- Customer IDs are unique across sessions and never reused
- Views, cart adds, purchases and spend persist correctly across a full restart
- Purchased products are excluded from later recommendations
- Recommendation quality measurably improves after interaction (mean Top-5 probability
  rises from ~0.20 to ~0.35)
- No probability is ever rendered on a product card
- The product page and cart page were verified in a real browser in **both** light and
  dark themes: correct image load, options, swatches, totals, no horizontal overflow
- Cart contents, quantities and checkout totals survive a restart
- Multi-unit purchases are counted as real units in `Purchases` and `Total_Spend`

### Admin panel

- A signed-in customer is refused the admin page and is offered the login instead; no
  admin widget is ever rendered on any customer page
- A wrong admin password is rejected and the panel stays closed
- The password field is masked; the admin login is not the customer ID login
- Adding a product writes one permanent row with a `PRD-` ID, and the form comes back
  empty and ready for the next one
- Blank names, `abc` prices, duplicate names, missing descriptions and non-URL image
  links are all refused and leave the catalogue untouched
- The new product is scored by the model, searchable in the browse grid, opens its own
  detail page, and can be added to the cart and bought
- Editing a product keeps its ID, writes only one row, and leaves every customer's views,
  cart adds, purchases and the cart line exactly as they were — including after a restart
- Editing with a blank name is refused and the saved product is unchanged
- The 🏷️ Marketplace prices tab lists each product's platforms (✓ / ✗), pre-fills the
  price and URL from an existing row, updates (upserts) instead of duplicating, and
  deletes on demand; invalid platforms, non-numeric prices, bad URLs and unknown product
  IDs are all refused and leave the file untouched
- Clicking a row's ✏️ Edit button switches to the Edit Product tab and scrolls the page
  up to the form; a plain tab switch or save never triggers a scroll
- Where to buy sorts stores cheapest → dearest, tags the cheapest row **BEST PRICE**, and
  opens each store's exact product page in a new tab; unlisted products show the
  *unavailable* message and never display an invented store or price
- 35 marketplace end-to-end checks and 19 data-layer regression checks pass with **zero
  failures**
- 91 end-to-end admin checks and 53 data-layer checks pass with **zero failures**
