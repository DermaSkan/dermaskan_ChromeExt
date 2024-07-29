from flask import Flask, request, jsonify, json
from flask_cors import CORS
import pandas as pd 
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

user_db = []

def load_product_data():
    try:
        with open('product.json', 'r') as file:
            products_db = json.load(file)
    except FileNotFoundError:
        products_db = []
    return products_db

@app.route('/api/product', methods=['POST'])
def product_data():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400
    
    product_name = data.get('product_name')
    brand_name = data.get('brand_name')
    ingredients = data.get('ingredients')
    
    if not all([product_name, brand_name, ingredients]):
        return jsonify({"error": "Missing required fields"}), 400
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
def survey_data():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    product_name = data.get('product_name')
    brand_name = data.get('brand_name')
    questions_answers = data.get('answers')
    product_link=""
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
            "product_link" : product_link
        }
    model_encoding(response)
    print(user_db)
    from decision_tree import main_model
    output = main_model()
    response = {
            "product_name": product_name,
            "brand_name": brand_name,
            "questions_answers": questions_answers,
            "product_link" : product_link,
            "results": str(output[0])
        }
    print(response)
    with open("user_db.json", 'w') as file:
        json.dump(response, file, indent=4)
    user_db.append(response)
    return jsonify(response), 200

def model_encoding(user):
    columns = {
        "Concern_Acne": "bool", "Concern_Aging": "bool", "Concern_Dark Spots": "bool", 
        "Concern_Dryness": "bool", "Concern_Oiliness": "bool",
        "Degree of Concern_Medium": "bool", "Degree of Concern_Mild": "bool", 
        "Degree of Concern_Severe": "bool", "Fragrance Preference_Don't care": "bool", 
        "Fragrance Preference_No fragrance": "bool", "Fragrance Preference_Yes fragrance": "bool", 
        "Fragrance_Free_P_False": "bool", 
        "Fragrance_Free_P_True": "bool", "Sensitivity_No": "bool", "Sensitivity_Yes": "bool", 
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

    csv_file_path = 'backend_user_data.csv'
    df.to_csv(csv_file_path, index=False)

    return csv_file_path




@app.route('/api/product/<string:product_name>/<string:brand_name>', methods=['GET'])
def check_product(product_name, brand_name):
    product_db = load_product_data()
    for product in product_db:
        if product["Product Name"].lower() == product_name.lower() and product["Brand Name"].lower() == brand_name.lower():
            return jsonify({"message": "Product found", "product": product}), 200

    return jsonify({"message": "Product not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
