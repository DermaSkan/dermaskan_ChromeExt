import pandas as pd
from google.cloud import storage
from flask import Flask, request, jsonify
from io import StringIO

def read_csv_from_gcs(bucket_name, source_blob_name):
    """Reads a CSV file from Google Cloud Storage into a Pandas DataFrame."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    data = blob.download_as_text()
    return pd.read_csv(StringIO(data))

def get_recommendation(input_data, predicted_category):
    # Filter the DataFrame based on the product link
    df = read_csv_from_gcs('dermadata', 'ml_folder/concernClassified.csv')
    ss = df[df['product link'] == input_data.get('Product Link', [''])[0]]
    concern = input_data.get('Skin_Concern_C', [''])[0]

    if ss.empty or not concern:
        return "Data not found or concern is missing in the input."

    # Extract the good and bad ingredients
    present_ingredient = eval(ss['present_ingredient'].iloc[0])
    good_ingredients = present_ingredient[concern]['good']
    bad_ingredients = present_ingredient[concern]['bad']

    category_msg = {
            3: "Excellent",
            2: "Great",
            1: "OK",
            0: "Not Recommended"
        }

    category_description = category_msg.get(predicted_category[0], "Unknown category")
    if category_description == "Unknown category":
        return category_description

    # Construct the appropriate recommendation string based on the predicted category
    if predicted_category[0] == 3:
        ingredients_list = ', '.join(good_ingredients)
        recommendation_str = f"Here is why DermaSkan rates this product {category_description} for you:\n" \
                                 f"• The product contains {ingredients_list}. All of these ingredients are ideal active ingredients to solve your {concern}."
    elif predicted_category[0] == 2:
        ingredients_list = ', '.join(good_ingredients)
        recommendation_str = f"Here is why DermaSkan rates this product {category_description} for you:\n" \
                                 f"• The product contains {ingredients_list}. All of these ingredients are ideal active ingredients to solve your {concern}."
    elif predicted_category[0] == 1:
        ingredients_list = ', '.join(good_ingredients)
        recommendation_str = f"Here is why we rated this product {category_description} for you:\n" \
                             f"• To help your {concern} concern, the product contains amazing ingredients such as {', '.join(good_ingredients)} to better your concern.\n • But it also contains some ingredients that may not help your concern much such as {', '.join(bad_ingredients)}"
    elif predicted_category[0] == 0:
        ingredients_list = ', '.join(bad_ingredients)
        recommendation_str = f"Here is why DermaSkan rates this product {category_description} for you:\n" \
                             f"• For your {concern}, active ingredients such as {ingredients_list} are being looked for. This product doesn’t contain the necessary active ingredients."
    else:
        recommendation_str = "Unknown category"

    return recommendation_str

def get_recommendation_api(data, result):
    recommendation = get_recommendation(data, result)
    return recommendation