import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dynamic Pricing for Perishable Goods")
st.title("Dynamic Pricing for Perishable Goods")

# Single entry input
st.subheader("Enter Product Details")
product = st.text_input("Product Name", "Milk")
expiry_date = st.date_input("Expiry Date", value=datetime(2025, 6, 26))
inventory = st.number_input("Inventory Level", min_value=0, max_value=1000, value=30)
demand = st.selectbox("Demand Level", ["Low", "Medium", "High"])
base_price = st.number_input("Base Price (₹)", min_value=1, max_value=1000, value=50)

if st.button("Calculate Dynamic Price"):
    today = datetime(2025, 6, 24)
    days_left = (expiry_date - today.date()).days
    demand_factor = {"Low": 0.9, "Medium": 1.0, "High": 1.1}
    expiry_factor = 0.95 if days_left <= 2 else 1.0
    inventory_factor = 0.9 if inventory > 20 else 1.0

    dynamic_price = round(base_price * demand_factor[demand] * expiry_factor * inventory_factor, 2)
    st.success(f"Dynamic Price for {product}: ₹{dynamic_price}")

# Dataset Upload Option
st.markdown("---")
st.subheader("Upload Dataset for Bulk Pricing (CSV with columns: Product, Expiry_Date, Inventory, Demand, Base_Price)")

file = st.file_uploader("Upload your CSV file", type=["csv"])
if file is not None:
    df = pd.read_csv(file)
    try:
        today = datetime(2025, 6, 24)
        df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"], format="%d-%m-%Y", errors='coerce')
        df["Days_Left"] = (df["Expiry_Date"] - today).dt.days

        df["Demand_Factor"] = df["Demand"].map({"Low": 0.9, "Medium": 1.0, "High": 1.1})
        df["Expiry_Factor"] = (df["Days_Left"] <= 2).map({True: 0.95, False: 1.0})
        df["Inventory_Factor"] = (df["Inventory"] > 20).map({True: 0.9, False: 1.0})

        df["Dynamic_Price"] = (
            df["Base_Price"] * df["Demand_Factor"] * df["Expiry_Factor"] * df["Inventory_Factor"]
        ).round(2)

        df.drop(columns=["Days_Left", "Demand_Factor", "Expiry_Factor", "Inventory_Factor"], inplace=True)

        st.write("### Updated Dataset with Dynamic Prices")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Something went wrong: {e}")
