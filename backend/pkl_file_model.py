import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder
from google.cloud import storage
from io import BytesIO
from io import StringIO

def read_pkl_from_gcs(bucket_name, file_path):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    file_data = blob.download_as_bytes()
    with BytesIO(file_data) as file_stream:
        data = pickle.load(file_stream)
    return data


def read_csv_from_gcs(bucket_name, source_blob_name):
    """Reads a CSV file from Google Cloud Storage into a Pandas DataFrame."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    data = blob.download_as_text()
    return pd.read_csv(StringIO(data))


def mvp_model(input_data):
    model = read_pkl_from_gcs('dermadata','ml_folder/DecisionTreeMVP.pkl')
    label_encoders = read_pkl_from_gcs('dermadata','ml_folder/label_encoder.pkl')
    input_df = pd.DataFrame(input_data)

    categories = {
        'Skin_Type_C': ['Dry', 'Oily', 'Normal', 'Combination'],
        'Skin_Concern_C': ['Dryness','Dullness', 'Oiliness','Acne', 'Aging', 'Pores', 'Uneven texture','Uneven skin tone',
                        'Redness','Dark Spots'],
        'Degree_of_Concern_C': ['Severe', 'Medium', 'Mild'],
        'Fragrance_Preference_C': ['No fragrance', 'Yes fragrance', 'Doesn’t care'],
        'Sensitivity_C': ['Yes', 'No']
    }

    for column, cats in categories.items():
        input_df[column] = pd.Categorical(input_df[column], categories=cats)
        one_hot = pd.get_dummies(input_df[column], prefix=column, dtype=int)
        input_df = pd.concat([input_df, one_hot], axis=1)
        input_df.drop(column, axis=1, inplace=True)

    input_df['Product Link Encoded'] = label_encoders.transform(input_df['Product Link'])
    input_df.drop('Product Link', axis=1, inplace=True)

    input_df.reset_index(drop=True, inplace=True)
    prod=read_csv_from_gcs("dermadata","ml_folder/product_data_encoded.csv")
    merged_df = pd.merge(input_df, prod, on='Product Link Encoded', how='left')
    pd.set_option('display.max_rows', None)  # None means unlimited
    pd.set_option('display.max_columns', None)  # None means unlimited
    column_order = [
    'product link', 'normal_P', 'dry_P','oily_P','combination_P','Dryness',
    'Dullness', 'Oiliness', 'Acne', 'Aging', 'Pores', 'Uneven texture',
    'Uneven skin tone', 'Redness', 'Dark spots', 'Skin_Type_C_Combination', 'Skin_Type_C_Dry', 'Skin_Type_C_Normal',
    'Skin_Type_C_Oily', 'Skin_Concern_C_Acne', 'Skin_Concern_C_Aging',
    'Skin_Concern_C_Dark Spots','Skin_Concern_C_Dryness','Skin_Concern_C_Dullness',
    'Skin_Concern_C_Oiliness','Skin_Concern_C_Pores','Skin_Concern_C_Redness',
    'Skin_Concern_C_Uneven skin tone','Skin_Concern_C_Uneven texture','Degree_of_Concern_C_Medium',
    'Degree_of_Concern_C_Mild','Degree_of_Concern_C_Severe','Fragrance_Preference_C_Doesn’t care',
    'Fragrance_Preference_C_No fragrance','Fragrance_Preference_C_Yes fragrance','Sensitivity_C_No',
    'Sensitivity_C_Yes','fragrance_P_No fragrance','fragrance_P_Yes fragrance','Good for Sensitive Skin_P_No',
    'Good for Sensitive Skin_P_Yes','Product Link Encoded'
    ]

    input_for_prediction = merged_df[column_order]

    k = input_for_prediction.drop(['product link'], axis=1)

    predicted_category = model.predict(k)
    return predicted_category
