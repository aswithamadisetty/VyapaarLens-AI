
# VyapaarLens AI — Hackathon MVP

## Run
1. Install Python 3.11+.
2. Open terminal in this folder.
3. Run:
   pip install -r requirements.txt
4. Run:
   python app.py
5. Open:
   http://127.0.0.1:5000

## Demo dataset
Use `data/demo_business_sales.csv` first. It contains:
- Product
- Quantity
- Price
- Cost
- Inventory
- Date

This is intentionally shaped for the VyapaarLens prototype so Revenue, Cost and Profit can all be calculated.

## Real dataset
The UCI Online Retail dataset is a credible public sales dataset. It contains Quantity and UnitPrice, but it does NOT contain product cost or inventory, so profit analysis will remain limited unless you enrich it with cost/inventory data.

UCI Online Retail:
https://archive.ics.uci.edu/dataset/352/online+retail

For the hackathon demo, start with the included demo_business_sales.csv. Then optionally show the UCI dataset to demonstrate that the Data Agent can handle real-world transactional data.

## Architecture
- Data Agent: validation + canonical field mapping + confidence score
- Analyst Agent: product performance analysis
- Decision Agent: deterministic scenario calculations
- Risk Agent: assumptions and data limitations
- Orchestrator: Flask API routes coordinate the agents

Gemini can be added later for natural-language explanation, but the numeric calculations should remain deterministic Python calculations.

## Stress Tester logic

The Stress Tester models scenarios differently rather than applying one multiplier to every metric:
- Increase/Reduce sales: changes sales volume; price and unit cost remain unchanged.
- Increase/Reduce price: changes selling price; sales volume and unit cost remain unchanged.

Profit is recalculated as `scenario revenue - scenario cost`, so price scenarios do not incorrectly scale costs.
The UI also displays a plain-language decision insight and explicit scenario assumptions.
