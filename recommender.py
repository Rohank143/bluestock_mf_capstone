"""
Module: recommender.py
Description: A simple rule-based mutual fund recommender based on risk appetite.
"""
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def recommend_funds(risk_appetite):
    """Recommend top 3 funds based on the user's risk appetite."""
    # Mapping risk appetite to fund risk_grade
    risk_mapping = {
        'Low': ['Low', 'Moderately Low'],
        'Moderate': ['Moderate', 'Moderately High'],
        'High': ['High', 'Very High']
    }
    
    # Capitalize correctly
    risk_appetite = risk_appetite.capitalize()
    
    if risk_appetite not in risk_mapping:
        logging.warning("Invalid risk appetite. Please enter 'Low', 'Moderate', or 'High'.")
        return
        
    target_categories = risk_mapping[risk_appetite]
    
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), 'recommender_data.csv')
    if not os.path.exists(data_path):
        logging.error("recommender_data.csv not found. Please run advanced_analytics_generator.py first.")
        return
        
    df = pd.read_csv(data_path)
    
    # Filter matching risk categories
    matching_funds = df[df['risk_category'].isin(target_categories)].copy()
    
    if matching_funds.empty:
        print(f"No funds found for the given risk appetite '{risk_appetite}'.")
        return
        
    # Rank funds by Sharpe ratio descending
    matching_funds.sort_values(by='Sharpe_Ratio', ascending=False, inplace=True)
    top_3 = matching_funds.head(3).copy()
    top_3['Rank'] = range(1, len(top_3) + 1)
    
    # Required output format: | Rank | Fund Name | Risk Grade | Sharpe Ratio |
    print(f"\n--- Top 3 Recommended Funds for {risk_appetite} Risk Appetite ---\n")
    print(f"{'Rank':<5} | {'Fund Name':<60} | {'Risk Grade':<15} | {'Sharpe Ratio':<12}")
    print("-" * 105)
    for _, row in top_3.iterrows():
        print(f"{row['Rank']:<5} | {row['scheme_name']:<60} | {row['risk_category']:<15} | {row['Sharpe_Ratio']:.4f}")
    print("-" * 105)

if __name__ == "__main__":
    print("Welcome to the Bluestock Rule-Based Fund Recommender!")
    print("=====================================================")
    while True:
        user_input = input("Enter your risk appetite (Low/Moderate/High) or 'q' to quit: ").strip()
        if user_input.lower() == 'q':
            print("Exiting...")
            break
        recommend_funds(user_input)
