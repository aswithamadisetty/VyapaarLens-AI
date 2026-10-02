from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import os

app = Flask(__name__)


# ============================================================
# FIELD ALIASES
# ============================================================

FIELD_ALIASES = {
    "product": [
        "product",
        "product name",
        "product_name",
        "description",
        "item",
        "item name"
    ],

    "quantity": [
        "quantity",
        "qty",
        "units sold",
        "units",
        "sales volume",
        "volume"
    ],

    "price": [
        "price",
        "unit price",
        "unit_price",
        "selling price",
        "selling_price",
        "sale price"
    ],

    "revenue": [
        "revenue",
        "sales",
        "sales amount",
        "total sales",
        "turnover"
    ],

    "cost": [
        "cost",
        "unit cost",
        "unit_cost",
        "cost price",
        "cost_price",
        "product cost"
    ],

    "inventory": [
        "inventory",
        "stock",
        "stock level",
        "stock_level",
        "available stock"
    ],

    "date": [
        "date",
        "invoice date",
        "invoice_date",
        "order date",
        "transaction date"
    ]
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def detect_fields(columns):

    mapping = {}

    normalized_columns = {
        column: normalize(column)
        for column in columns
    }

    for canonical, aliases in FIELD_ALIASES.items():

        normalized_aliases = [
            normalize(alias)
            for alias in aliases
        ]

        for column, normalized_column in normalized_columns.items():

            if normalized_column in normalized_aliases:

                mapping[canonical] = column
                break

            if any(
                alias in normalized_column
                for alias in normalized_aliases
            ):

                mapping[canonical] = column
                break

    return mapping


def load_file(path):

    extension = os.path.splitext(path)[1].lower()

    if extension == ".csv":
        return pd.read_csv(path)

    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    raise ValueError(
        "Unsupported file format. Please upload CSV or Excel."
    )


def money_fmt(value):

    if value is None:
        return "Unavailable"

    try:
        value = float(value)
    except Exception:
        return "Unavailable"

    return "₹" + format(value, ",.0f")


def safe_number(value, default=0):

    try:
        return float(value)

    except Exception:
        return default


# ============================================================
# DATA ANALYSIS
# ============================================================

def analyze(df):

    mapping = detect_fields(df.columns)

    rows = len(df)

    available = list(mapping.keys())

    work = df.copy()


    # ========================================================
    # DATA CONFIDENCE
    # ========================================================

    confidence = 40

    if "product" in mapping:
        confidence += 10

    if "quantity" in mapping:
        confidence += 15

    if "price" in mapping or "revenue" in mapping:
        confidence += 15

    if "cost" in mapping:
        confidence += 10

    if "inventory" in mapping:
        confidence += 5

    confidence = min(confidence, 100)


    # ========================================================
    # NUMERIC FIELD HELPER
    # ========================================================

    def num(field):

        if field in mapping:

            return (
                pd.to_numeric(
                    work[mapping[field]],
                    errors="coerce"
                )
                .fillna(0)
            )

        return pd.Series(
            np.zeros(len(work)),
            index=work.index
        )


    # ========================================================
    # BASIC FIELDS
    # ========================================================

    quantity = num("quantity")

    price = num("price")

    cost = num("cost")

    inventory = num("inventory")


    # ========================================================
    # REVENUE
    # ========================================================

    if "revenue" in mapping:

        revenue = num("revenue")

    elif (
        "quantity" in mapping
        and "price" in mapping
    ):

        revenue = quantity * price

    else:

        revenue = pd.Series(
            np.zeros(len(work)),
            index=work.index
        )


    # ========================================================
    # COST + PROFIT
    # ========================================================

    if (
        "cost" in mapping
        and "quantity" in mapping
    ):

        total_cost = quantity * cost

        profit = revenue - total_cost

        profit_available = True

    else:

        total_cost = pd.Series(
            np.zeros(len(work)),
            index=work.index
        )

        profit = pd.Series(
            np.zeros(len(work)),
            index=work.index
        )

        profit_available = False


    # ========================================================
    # BASE TOTALS
    # ========================================================

    base_revenue = float(
        revenue.sum()
    )

    base_cost = float(
        total_cost.sum()
    )

    if profit_available:

        base_profit = float(
            profit.sum()
        )

    else:

        base_profit = None


    # ========================================================
    # PRODUCT PERFORMANCE
    # ========================================================

    product_rows = []

    if "product" in mapping:

        temp = pd.DataFrame({

            "Product":
                work[mapping["product"]]
                .fillna("Unknown")
                .astype(str),

            "Revenue": revenue

        })

        grouped = (
            temp
            .groupby(
                "Product",
                as_index=False
            )["Revenue"]
            .sum()
            .sort_values(
                "Revenue",
                ascending=False
            )
        )

        product_rows = [

            {
                "product": row["Product"],
                "revenue": round(
                    float(row["Revenue"]),
                    2
                )
            }

            for _, row
            in grouped.head(8).iterrows()
        ]


    # ========================================================
    # REVENUE TREND
    # ========================================================

    revenue_trend = []

    if "date" in mapping:

        try:

            trend_df = pd.DataFrame({

                "Date": pd.to_datetime(
                    work[mapping["date"]],
                    errors="coerce"
                ),

                "Revenue": revenue

            })

            trend_df = (
                trend_df
                .dropna(subset=["Date"])
                .groupby("Date", as_index=False)["Revenue"]
                .sum()
                .sort_values("Date")
            )

            for _, row in trend_df.iterrows():

                revenue_trend.append({

                    "date":
                        row["Date"].strftime(
                            "%Y-%m-%d"
                        ),

                    "revenue":
                        round(
                            float(row["Revenue"]),
                            2
                        )
                })

        except Exception:

            revenue_trend = []


    # ========================================================
    # INVENTORY ANALYSIS
    # ========================================================

    inventory_info = {

        "available":
            "inventory" in mapping,

        "total":
            round(
                float(inventory.sum()),
                2
            )
            if "inventory" in mapping
            else None,

        "low_stock":
            0,

        "high_stock":
            0,

        "message":
            "Inventory data unavailable."
    }


    if "inventory" in mapping:

        # Use a simple transparent prototype rule.
        # Low stock = <= 20 units.
        # High stock = >= 100 units.

        low_stock_count = int(
            (inventory <= 20).sum()
        )

        high_stock_count = int(
            (inventory >= 100).sum()
        )

        inventory_info["low_stock"] = (
            low_stock_count
        )

        inventory_info["high_stock"] = (
            high_stock_count
        )


        if low_stock_count > 0:

            inventory_info["message"] = (
                f"{low_stock_count} product(s) have "
                "inventory at or below 20 units. "
                "Review replenishment requirements."
            )

        elif high_stock_count > 0:

            inventory_info["message"] = (
                f"{high_stock_count} product(s) have "
                "inventory of 100 units or more. "
                "Review whether excess stock is tying up capital."
            )

        else:

            inventory_info["message"] = (
                "No critical inventory threshold was detected "
                "using the prototype rules."
            )


    # ========================================================
    # WARNINGS
    # ========================================================

    warnings = []


    if not (
        "revenue" in mapping
        or (
            "quantity" in mapping
            and "price" in mapping
        )
    ):

        warnings.append(
            "Revenue needs Revenue data or both Quantity and Price."
        )


    if not profit_available:

        warnings.append(
            "Profit analysis is disabled until unit cost and quantity data are available."
        )


    if confidence < 80:

        warnings.append(
            "Data confidence is below the recommended prototype threshold."
        )


    if "inventory" not in mapping:

        warnings.append(
            "Inventory data is unavailable; inventory recommendations are limited."
        )


    # ========================================================
    # AI BUSINESS INSIGHTS
    # ========================================================

    insights = []

    if product_rows:

        top_product = product_rows[0]

        insights.append(
            f"{top_product['product']} is the highest "
            f"revenue-generating product with "
            f"{money_fmt(top_product['revenue'])} in revenue."
        )


    if base_revenue > 0 and profit_available:

        margin = (
            base_profit / base_revenue
        ) * 100

        insights.append(
            f"Current estimated gross profit margin "
            f"is {margin:.1f}% based on the uploaded cost data."
        )


    if (
        profit_available
        and base_profit > 0
    ):

        insights.append(
            "The business is currently showing a positive "
            "estimated gross profit under the uploaded data."
        )

    elif profit_available:

        insights.append(
            "The uploaded data indicates that estimated "
            "gross profit should be reviewed before major decisions."
        )


    if "inventory" in mapping:

        if inventory_info["low_stock"] > 0:

            insights.append(
                "Inventory risk requires attention because "
                "some products are near the low-stock threshold."
            )

        else:

            insights.append(
                "No immediate low-stock warning was identified "
                "using the prototype inventory threshold."
            )


    if (
        "date" in mapping
        and len(revenue_trend) >= 2
    ):

        first_revenue = revenue_trend[0]["revenue"]

        last_revenue = revenue_trend[-1]["revenue"]

        if last_revenue > first_revenue:

            insights.append(
                "Revenue shows an upward movement between "
                "the earliest and latest available dates."
            )

        elif last_revenue < first_revenue:

            insights.append(
                "Revenue shows a downward movement between "
                "the earliest and latest available dates."
            )

        else:

            insights.append(
                "Revenue is relatively stable between "
                "the earliest and latest available dates."
            )


    # ========================================================
    # RECOMMENDATION
    # ========================================================

    recommendation = (
        "Use the Stress Tester before making major pricing "
        "or sales decisions. Compare multiple scenarios and "
        "review the Risk Agent assumptions before acting."
    )


    if product_rows:

        recommendation = (
            f"Prioritize analysis of {product_rows[0]['product']} "
            "and use scenario testing to evaluate pricing or "
            "sales-volume changes before implementation."
        )


    # ========================================================
    # AGENT SUMMARY
    # ========================================================

    agent_summary = {

        "data":
            f"Validated {rows:,} rows and detected "
            f"{len(mapping)} canonical business fields.",

        "analyst":
            f"Analyzed {len(product_rows)} product records "
            "and calculated available business metrics.",

        "decision":
            "Scenario engine is ready to evaluate "
            "sales and pricing decisions.",

        "risk":
            f"{len(warnings)} data limitations identified "
            "before decision simulation."
    }


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "rows":
            rows,

        "mapping":
            mapping,

        "confidence":
            confidence,

        "available":
            available,

        "base_revenue":
            round(
                base_revenue,
                2
            ),

        "base_cost":
            round(
                base_cost,
                2
            ),

        "base_profit":
            round(
                base_profit,
                2
            )
            if base_profit is not None
            else None,

        "profit_available":
            profit_available,

        "products":
            product_rows,

        "revenue_trend":
            revenue_trend,

        "inventory":
            inventory_info,

        "insights":
            insights,

        "recommendation":
            recommendation,

        "agent_summary":
            agent_summary,

        "warnings":
            warnings
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# ANALYZE API
# ============================================================

@app.route(
    "/api/analyze",
    methods=["POST"]
)
def api_analyze():

    file = request.files.get("file")

    if not file:

        return jsonify({
            "error":
                "Please upload a CSV or Excel file."
        }), 400


    extension = os.path.splitext(
        file.filename
    )[1].lower()


    if extension not in [
        ".csv",
        ".xlsx",
        ".xls"
    ]:

        return jsonify({
            "error":
                "Only CSV and Excel files are supported."
        }), 400


    upload_directory = (
        app.instance_path
    )

    os.makedirs(
        upload_directory,
        exist_ok=True
    )


    path = os.path.join(
        upload_directory,
        "_upload" + extension
    )


    file.save(path)


    try:

        df = load_file(path)


        if df.empty:

            return jsonify({
                "error":
                    "The uploaded file contains no data."
            }), 400


        result = analyze(df)

        result["filename"] = (
            file.filename
        )


        return jsonify(result)


    except Exception as error:

        return jsonify({
            "error":
                str(error)
        }), 400


    finally:

        if os.path.exists(path):

            try:
                os.remove(path)

            except Exception:
                pass


# ============================================================
# STRESS TEST API
# ============================================================

@app.route(
    "/api/stress",
    methods=["POST"]
)
def api_stress():

    try:

        data = request.get_json(
            force=True
        )

    except Exception:

        return jsonify({
            "error":
                "Invalid JSON request."
        }), 400


    # --------------------------------------------------------
    # INPUT
    # --------------------------------------------------------

    base_revenue = safe_number(
        data.get(
            "base_revenue",
            0
        )
    )


    base_cost = safe_number(
        data.get(
            "base_cost",
            0
        )
    )


    base_profit = data.get(
        "base_profit",
        None
    )


    if base_profit is not None:

        base_profit = safe_number(
            base_profit
        )


    change = abs(
        safe_number(
            data.get(
                "change",
                0
            )
        )
    )


    scenario = str(
        data.get(
            "scenario",
            "Increase sales"
        )
    ).strip()


    has_quantity = bool(
        data.get(
            "has_quantity",
            False
        )
    )


    has_price = bool(
        data.get(
            "has_price",
            False
        )
    )


    has_cost = bool(
        data.get(
            "has_cost",
            False
        )
    )


    if change > 100:

        change = 100


    # --------------------------------------------------------
    # SCENARIOS
    # --------------------------------------------------------

    sales_scenarios = {
        "Increase sales",
        "Reduce sales"
    }


    price_scenarios = {
        "Increase price",
        "Reduce price"
    }


    scenario_revenue = base_revenue

    scenario_cost = base_cost

    risks = []


    # ========================================================
    # SALES
    # ========================================================

    if scenario in sales_scenarios:

        if scenario == "Increase sales":

            factor = 1 + (
                change / 100
            )

            scenario_revenue = (
                base_revenue * factor
            )

            scenario_cost = (
                base_cost * factor
                if has_cost
                else 0
            )

            risks.append(
                f"Sales volume is assumed to increase by "
                f"{change:g}%, while price and unit cost remain unchanged."
            )

        else:

            factor = 1 - (
                change / 100
            )

            scenario_revenue = (
                base_revenue * factor
            )

            scenario_cost = (
                base_cost * factor
                if has_cost
                else 0
            )

            risks.append(
                f"Sales volume is assumed to decrease by "
                f"{change:g}%, while price and unit cost remain unchanged."
            )


    # ========================================================
    # PRICE
    # ========================================================

    elif scenario in price_scenarios:

        if not has_quantity or not has_price:

            if scenario == "Increase price":

                factor = 1 + (
                    change / 100
                )

            else:

                factor = 1 - (
                    change / 100
                )

            scenario_revenue = (
                base_revenue * factor
            )

            scenario_cost = base_cost

            risks.append(
                "Price scenario is an approximation because "
                "both Quantity and Price fields are required "
                "for a fully evidence-based simulation."
            )

        else:

            if scenario == "Increase price":

                factor = 1 + (
                    change / 100
                )

                scenario_revenue = (
                    base_revenue * factor
                )

                risks.append(
                    f"Selling price is assumed to increase by "
                    f"{change:g}%, while sales volume and unit cost remain unchanged."
                )

            else:

                factor = 1 - (
                    change / 100
                )

                scenario_revenue = (
                    base_revenue * factor
                )

                risks.append(
                    f"Selling price is assumed to decrease by "
                    f"{change:g}%, while sales volume and unit cost remain unchanged."
                )

            scenario_cost = base_cost


    # ========================================================
    # UNKNOWN
    # ========================================================

    else:

        factor = 1 + (
            change / 100
        )

        scenario_revenue = (
            base_revenue * factor
        )

        scenario_cost = (
            base_cost * factor
            if has_cost
            else 0
        )

        risks.append(
            "Scenario uses a proportional revenue assumption "
            "because the selected scenario is not fully modeled."
        )


    # ========================================================
    # PROFIT
    # ========================================================

    scenario_profit = None

    profit_delta = None


    if (
        base_profit is not None
        and has_cost
    ):

        scenario_profit = (
            scenario_revenue
            - scenario_cost
        )

        profit_delta = (
            scenario_profit
            - base_profit
        )

    else:

        risks.append(
            "Profit impact cannot be established because "
            "unit cost and quantity data are unavailable."
        )


    # ========================================================
    # REVENUE DELTA
    # ========================================================

    revenue_delta = (
        scenario_revenue
        - base_revenue
    )


    # ========================================================
    # GENERAL RISK
    # ========================================================

    risks.append(
        "Scenario results depend on the quality of the uploaded "
        "business data and the stated assumptions."
    )


    # ========================================================
    # INSIGHT
    # ========================================================

    if scenario in sales_scenarios:

        direction = (
            "increase"
            if scenario == "Increase sales"
            else "decrease"
        )


        if scenario_profit is not None:

            insight = (
                f"A {change:g}% {direction} in sales volume "
                f"changes projected revenue by "
                f"{money_fmt(revenue_delta)} "
                f"and projected profit by "
                f"{money_fmt(profit_delta)} "
                f"under the current price and cost assumptions."
            )

        else:

            insight = (
                f"A {change:g}% {direction} in sales volume "
                f"changes projected revenue by "
                f"{money_fmt(revenue_delta)}; "
                f"profit requires cost data."
            )


    elif scenario in price_scenarios:

        direction = (
            "increase"
            if scenario == "Increase price"
            else "decrease"
        )


        if scenario_profit is not None:

            insight = (
                f"A {change:g}% {direction} in selling price "
                f"changes projected revenue by "
                f"{money_fmt(revenue_delta)} "
                f"and projected profit by "
                f"{money_fmt(profit_delta)} "
                f"when sales volume and unit cost remain unchanged."
            )

        else:

            insight = (
                f"A {change:g}% price change "
                f"changes projected revenue by "
                f"{money_fmt(revenue_delta)}; "
                f"profit requires cost data."
            )


    else:

        insight = (
            "The selected scenario has been simulated "
            "using the available business data and stated assumptions."
        )


    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify({

        "scenario":
            scenario,

        "change":
            change,

        "base_revenue":
            round(
                base_revenue,
                2
            ),

        "scenario_revenue":
            round(
                scenario_revenue,
                2
            ),

        "revenue_delta":
            round(
                revenue_delta,
                2
            ),

        "base_profit":
            None
            if base_profit is None
            else round(
                base_profit,
                2
            ),

        "scenario_profit":
            None
            if scenario_profit is None
            else round(
                scenario_profit,
                2
            ),

        "profit_delta":
            None
            if profit_delta is None
            else round(
                profit_delta,
                2
            ),

        "risks":
            risks,

        "insight":
            insight
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )