# 📊 VyapaarLens AI — Smart Business Intelligence & Decision Support

**Turn business data into actionable insights. Simulate decisions. Understand risks before acting.**

VyapaarLens AI is a business intelligence and decision-support web application designed to help small businesses analyze sales data, understand product performance, monitor inventory, and evaluate hypothetical business scenarios.

## 🚀 Key Features

### 📂 1. Smart Data Upload
- Upload business datasets in CSV and Excel formats.
- Automatically detect common business column names and aliases.
- Map uploaded columns to standardized business fields.
- Calculate a data confidence score.
- Identify missing data that may limit analysis.

### 📈 2. Business Performance Analytics
- Calculate total revenue, cost, and profit when the required data is available.
- Identify top-performing products.
- Visualize product performance through charts.
- Analyze revenue trends when transaction dates are available.

### 📦 3. Inventory Intelligence
- Identify products with low stock levels.
- Flag products with high inventory levels.
- Generate inventory-related insights using configurable thresholds.

### 🤖 4. Multi-Agent Decision Workflow

| Agent | Responsibility |
|---|---|
| Data Agent | Validates datasets and detects business fields. |
| Analyst Agent | Analyzes sales, revenue, costs, and product performance. |
| Decision Agent | Simulates hypothetical business scenarios. |
| Risk Agent | Identifies missing information, assumptions, and limitations. |
| Orchestrator | Coordinates the workflow through Flask API endpoints. |

### 🧪 5. AI Decision Stress Tester
Simulate different business scenarios:

- Increase sales
- Reduce sales
- Increase price
- Reduce price

View projected revenue changes, profit impacts when sufficient data is available, and associated assumptions.

### 💡 6. Business Insights
- Generate data-driven business insights.
- Highlight potential business risks.
- Support informed decisions using numerical analysis.
- Display recommendations based on available data.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Data Analysis:** Pandas, NumPy
- **Frontend:** HTML, CSS, JavaScript
- **Visualization:** Chart.js
- **Excel Support:** openpyxl

## 🏗️ Project Structure

```text
VyapaarLens_AI_MVP/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── demo_business_sales.csv
├── instance/
├── static/
└── templates/
    └── index.html
