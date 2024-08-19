from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os
import tempfile
from google.cloud import storage
import asyncio

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})
user_db = []

@app.route("/")
async def hello():
    return "Hello"

def add_data_to_json(new_data):
    bucket_name = 'dermadata'
    file_path = 'product_data/user_db.json'
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        # Create a temporary file to store the JSON data
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file_name = temp_file.name
            
            # Download the existing JSON file from GCS
            data = blob.download_as_text()
            existing_data = json.loads(data)

            # Append the new data to the existing data
            existing_data.append(new_data)
            
            # Write the updated data to the temporary file
            json.dump(existing_data, temp_file, indent=4)

        # Upload the temporary file back to GCS
        blob.upload_from_filename(temp_file_name, content_type='application/json')
        print(f"Updated data uploaded to {file_path} in bucket {bucket_name}.")

    except Exception as e:
        print(f"An error occurred while updating user_db.json: {e}")

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_name):
            os.remove(temp_file_name)

    
def load_product_data():
    """Load product data from a Google Cloud Storage bucket."""
    bucket_name = 'dermadata'
    file_path = 'product_data/product.json' 

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        json_data = blob.download_as_text()
        products_db = json.loads(json_data)
    except Exception as e:
        print(f"An error occurred: {e}")
        products_db = []
    return products_db

@app.route('/api/product', methods=['POST'])
async def product_data():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400
    
    product_name = data.get('product_name')
    brand_name = data.get('brand_name')
    ingredients = data.get('ingredients')
    
    if not all([product_name, brand_name, ingredients]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Assuming products_db is a global variable
    global products_db
    products_db.append({
        "product_name": product_name,
        "brand_name": brand_name,
        "ingredients": ingredients
    })

    response = {
        "message": "Product data received successfully",
        "data": {
            "product_name": product_name,
            "brand_name": brand_name,
            "ingredients": ingredients
        }
    }

    return jsonify(response), 200

@app.route('/api/survey', methods=['POST'])
async def survey_data():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    product_name = data.get('product_name')
    brand_name = data.get('brand_name')
    questions_answers = data.get('answers')
    product_link = ""
    product_db = load_product_data()
    
    for product in product_db:
        if product["Product Name"].lower() == product_name.lower() and product["Brand Name"].lower() == brand_name.lower():
            product_link = product["Product Link"]

    if not all([product_name, brand_name, questions_answers]):
        return jsonify({"error": "Missing required fields"}), 400

    if not isinstance(questions_answers, dict):
        return jsonify({"error": "questions_answers must be a dictionary"}), 400
    
    response = {
        "product_name": product_name,
        "brand_name": brand_name,
        "questions_answers": questions_answers,
        "product_link": product_link
    }

    #model_encoding(response)
    model_data = model_pkl_formatter(response)
    from pkl_file_model import mvp_model
    output = mvp_model(model_data)
    from result_statement import get_recommendation_api
    recommendation = get_recommendation_api(model_data,output)
    response = {
        "product_name": product_name,
        "brand_name": brand_name,
        "questions_answers": questions_answers,
        "product_link": product_link,
        "results": str(output[0]),
        "statement": recommendation
    }
    add_data_to_json(response)
    return jsonify(response), 200


def model_pkl_formatter(response):
    custom_concerns = {
        "Aging (fine lines/wrinkles, loss of firmness/elasticity)": "Aging",
        "Acne/blemishes": "Acne",
        "Hyperpigmentation/Dark Spots": "Dark Spots"
    }
    input_data = {
        'Skin_Type_C': [],
        'Skin_Concern_C': [],
        'Degree_of_Concern_C': [],
        'Fragrance_Preference_C': [],
        'Sensitivity_C': [],
        'Product Link': []
    }
    questions_answers = response['questions_answers']
    skin_type = questions_answers.get('Question #3: What is your skin type?', [""])[0]
    if skin_type:
        input_data['Skin_Type_C'] = [skin_type]

    concerns = questions_answers.get('Question #1: What is the primary skin concern you are hoping to address with this product?', [""])[0]
    if concerns:
        if concerns in custom_concerns:
            input_data['Skin_Concern_C'] = [custom_concerns[concerns]]
        else:
            input_data['Skin_Concern_C'] = [concerns]

    severity = questions_answers.get('Question #2: How severe is this', [""])[0]
    if severity:
        input_data['Degree_of_Concern_C'] = [severity]
    fragrance_preference = questions_answers.get('Question #5: How do you feel about fragrances?', [""])[0]

    if fragrance_preference:
        if fragrance_preference == "Hate them":
            input_data['Fragrance_Preference_C'] = ["No fragrance"]
        elif fragrance_preference == "Love them":
            input_data['Fragrance_Preference_C'] = ["Yes fragrance"]
        elif fragrance_preference == "Don't Care":
            input_data['Fragrance_Preference_C'] = ["Don't care"]
        else:
            input_data['Fragrance_Preference_C'] = ["No fragrance"]

    sensitivity = questions_answers.get('Question #4: Does your skin react poorly to new products?', [""])[0]
    if sensitivity:
        input_data['Sensitivity_C'] = [sensitivity]

    input_data['Product Link'] = [response.get('product_link', "")]
    
    return input_data


async def model_encoding(user):
    columns = {
        "Concern_Acne": "bool", "Concern_Aging": "bool", "Concern_Dark Spots": "bool", 
        "Concern_Dryness": "bool", "Concern_Oiliness": "bool",
        "Degree of Concern_Medium": "bool", "Degree of Concern_Mild": "bool", 
        "Degree of Concern_Severe": "bool", "Fragrance Preference_Don't care": "bool", 
        "Fragrance Preference_No fragrance": "bool", "Fragrance Preference_Yes fragrance": "bool", 
        "Fragrance_Free_P_False": "bool", "Fragrance_Free_P_True": "bool", 
        "Sensitivity_No": "bool", "Sensitivity_Yes": "bool", 
        "Skin type_Combination": "bool", "Skin type_Dry": "bool", "Skin type_Normal": "bool", 
        "Skin type_Oily": "bool", "SkinType_combination": "int64", "SkinType_dry": "int64", 
        "SkinType_normal": "int64", "SkinType_oily": "int64", "SkinType_sensitive": "int64", 
        "Skincare_Acne": "int64", "Skincare_Aging": "int64", "Skincare_Dark Spots": "int64", 
        "Skincare_Dryness": "int64", "Skincare_Oiliness": "int64", 
        "Rating": "object", "Product Link": "category"
    }
    custom_concerns = {
        "Aging (fine lines/wrinkles, loss of firmness/elasticity)": "Aging",
        "Acne/blemishes": "Acne",
        "Hyperpigmentation/Dark Spots": "Dark Spots"
    }

    data = {col: False if dtype == "bool" else 0 if dtype == "int64" else "" for col, dtype in columns.items()}

    user_info = user
    questions_answers = user_info['questions_answers']

    data.update({"Rating": "Excellent", "Product Link": user_info.get("product_link", "")})

    concerns = questions_answers.get('Question #1: What is the primary skin concern you are hoping to address with this product?', [""])[0]
    if concerns:
        if "Concern_" + concerns not in columns or custom_concerns:
            pass
        elif concerns in custom_concerns:
            data["Concern_" + custom_concerns[concerns]] = True
            data["Skincare_" + custom_concerns[concerns]] = 1
        else:
            data["Concern_" + concerns] = True
            data["Skincare_" + concerns] = 1  

    severity = questions_answers.get('Question #2: How severe is this', [""])[0]
    if severity:
        data["Degree of Concern_" + severity] = True

    skin_type = questions_answers.get('Question #3: What is your skin type?', [""])[0]
    if skin_type:
        data["Skin type_" + skin_type] = True

    sensitivity = questions_answers.get('Question #4: Does your skin react poorly to new products?', [""])[0]
    if sensitivity:
        data["Sensitivity_" + sensitivity] = True

    fragrance_preference = questions_answers.get('Question #5: How do you feel about fragrances?', [""])[0]
    if fragrance_preference:
        if fragrance_preference == "Hate them":
            data["Fragrance Preference_No fragrance"] = True
        if fragrance_preference == "Love them":
            data["Fragrance Preference_No fragrance"] = False
            data["Fragrance Preference_Yes fragrance"] = True
        if fragrance_preference == "Don't Care":
            data["Fragrance Preference_No fragrance"] = False
            data["Fragrance Preference_Yes fragrance"] = False
            data["Fragrance Preference_Don't care"] = True
        else:
            data["Fragrance Preference_No fragrance"] = False

    df = pd.DataFrame([data])
    for col, dtype in columns.items():
        df[col] = df[col].astype(dtype)
    csv_file_path = 'ml_folder/backend_user_data.csv'
    storage_client = storage.Client()
    bucket = storage_client.bucket("dermadata")
    blob = bucket.blob(csv_file_path)
    csv_data = df.to_csv(index=False)
    blob.upload_from_string(csv_data, content_type='text/csv')
    return csv_file_path

@app.route('/api/product/<string:product_name>/<string:brand_name>', methods=['GET'])
async def check_product(product_name, brand_name):
    product_db = load_product_data()
    for product in product_db:
        if product["Product Name"].lower() == product_name.lower() and product["Brand Name"].lower() == brand_name.lower():
            return jsonify({"message": "Product found", "product": product}), 200
    return jsonify({"message": "Product not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
