# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import plotly.graph_objects as go

st.set_page_config(page_title="Dynamic Pricing with AI")
st.title("Dynamic Pricing with AI Recommendation")

# ==== Load or Train Model Function ======
@st.cache_data
def load_model():
    data = {
        "Base_Price": [50, 40, 30, 20, 60, 80, 45, 70],
        "Inventory": [10, 25, 5, 50, 30, 60, 10, 15],
        "Demand": ["High", "Low", "Low", "Medium", "High", "Medium", "Low", "High"],
        "Days_Left": [5, 1, 0, 3, 10, 2, 1, 6],
        "Suggestion": ["Put-Even", "Don't Put", "Don't Put", "Put-Low", "Put-Even", "Put-Low", "Don't Put", "Put-Even"]
    }
    df_train = pd.DataFrame(data)
    le_demand = LabelEncoder()
    le_suggestion = LabelEncoder()
    df_train["Demand_Code"] = le_demand.fit_transform(df_train["Demand"])
    df_train["Suggestion_Code"] = le_suggestion.fit_transform(df_train["Suggestion"])

    X = df_train[["Base_Price", "Inventory", "Demand_Code", "Days_Left"]]
    y = df_train["Suggestion_Code"]
    model = RandomForestClassifier().fit(X, y)
    return model, le_demand, le_suggestion

model, le_demand, le_suggestion = load_model()

# ==== User Input Section ====
st.subheader("Enter Product Details")
product = st.text_input("Product Name", "Milk")
expiry_date = st.date_input("Expiry Date", value=datetime(2025, 6, 26))
inventory = st.number_input("Inventory Level", min_value=0, max_value=1000, value=30)
demand = st.selectbox("Demand Level", ["Low", "Medium", "High"])
base_price = st.number_input("Base Price (₹)", min_value=1, max_value=1000, value=50)

if st.button("Calculate Dynamic Price"):
    today = datetime.today().date()
    print(today)
    days_left = (expiry_date - today.date()).days
    demand_factor = {"Low": 0.9, "Medium": 1.0, "High": 1.1}
    expiry_factor = 0.95 if days_left <= 2 else 1.0
    inventory_factor = 0.9 if inventory > 20 else 1.0
    dynamic_price = round(base_price * demand_factor[demand] * expiry_factor * inventory_factor, 2)
    st.success(f"Dynamic Price for {product}: ₹{dynamic_price}")

if st.button("AI Suggestion"):
    days_left = (expiry_date -datetime.today().date().date()).days
    demand_code = le_demand.transform([demand])[0]
    features = pd.DataFrame([[base_price, inventory, demand_code, days_left]],
                            columns=["Base_Price", "Inventory", "Demand_Code", "Days_Left"])
    prediction = model.predict(features)[0]
    proba = model.predict_proba(features)[0]
    suggestion = le_suggestion.inverse_transform([prediction])[0]
    confidence = round(max(proba) * 100, 2)
    st.info(f"🧠 AI Suggestion: {suggestion} (Confidence: {confidence}%)")

# ==== Upload Dataset Section ====
st.markdown("---")
st.subheader("Upload CSV for Bulk Pricing & Suggestion")

file = st.file_uploader("Upload your CSV file", type=["csv"])
if file is not None:
    df = pd.read_csv(file)
    try:
        today = datetime.today().date()
        print(today)
        df["Expiry_Date"] = pd.to_datetime(df["Expiry_Date"], format="%d-%m-%Y", errors='coerce')
        df["Days_Left"] = (df["Expiry_Date"] - today).dt.days

        soon_expiring = df[df["Days_Left"] <= 2].shape[0]
        st.metric("Items Expiring Soon (<=2 days)", soon_expiring)

        df["Demand_Factor"] = df["Demand"].map({"Low": 0.9, "Medium": 1.0, "High": 1.1})
        df["Expiry_Factor"] = (df["Days_Left"] <= 2).map({True: 0.95, False: 1.0})
        df["Inventory_Factor"] = (df["Inventory"] > 20).map({True: 0.9, False: 1.0})

        df["Dynamic_Price"] = (
            df["Base_Price"] * df["Demand_Factor"] * df["Expiry_Factor"] * df["Inventory_Factor"]
        ).round(2)

        df["Waste_If_Not_Sold"] = df["Inventory"] * df["Base_Price"]
        df["Waste_With_Dynamic"] = df["Inventory"] * df["Dynamic_Price"]
        df["Waste_Reduced"] = df["Waste_If_Not_Sold"] - df["Waste_With_Dynamic"]

        df["Demand_Code"] = le_demand.transform(df["Demand"])
        df["AI_Suggestion_Code"] = model.predict(df[["Base_Price", "Inventory", "Demand_Code", "Days_Left"]])
        proba_all = model.predict_proba(df[["Base_Price", "Inventory", "Demand_Code", "Days_Left"]])
        df["Confidence"] = [f"{round(max(p)*100, 2)}%" for p in proba_all]
        df["AI_Suggestion"] = le_suggestion.inverse_transform(df["AI_Suggestion_Code"])

        counts = df["AI_Suggestion"].value_counts().to_dict()
        st.write(f"**Put-Even:** {counts.get('Put-Even', 0)}")
        st.write(f"**Put-Low:** {counts.get('Put-Low', 0)}")
        st.write(f"**Don't Put:** {counts.get('Don\'t Put', 0)}")

        if counts.get("Don't Put", 0) > 0:
            st.warning(f"⚠️ {counts['Don\'t Put']} items expiring within 2 days and marked 'Don’t Put' – consider donation or clearance sale.")

        fig = go.Figure(data=[
            go.Bar(name='Actual Waste', x=df["Product"] if "Product" in df else df.index, y=df["Waste_If_Not_Sold"]),
            go.Bar(name='Reduced Waste', x=df["Product"] if "Product" in df else df.index, y=df["Waste_With_Dynamic"])
        ])
        fig.update_layout(barmode='group', title="Waste Comparison (Actual vs. Reduced)", xaxis_title="Product", yaxis_title="Value (₹)")
        st.plotly_chart(fig)

        df.drop(columns=["Demand_Factor", "Expiry_Factor", "Inventory_Factor", "Demand_Code", "AI_Suggestion_Code"], inplace=True)
        st.write("### Updated Dataset with Dynamic Prices, AI Suggestions, Waste Calculation, and Confidence")
        st.dataframe(df)

    except Exception as e:
        st.error(f"Something went wrong: {e}")
