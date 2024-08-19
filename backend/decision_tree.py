import pandas as pd
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from google.cloud import storage
from io import StringIO
import os
import tempfile

def read_csv_from_gcs(bucket_name, source_blob_name):
    """Reads a CSV file from Google Cloud Storage into a Pandas DataFrame."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    data = blob.download_as_text()
    return pd.read_csv(StringIO(data))

def write_csv_to_gcs(df, bucket_name, destination_blob_name):
    """Writes a Pandas DataFrame to a CSV file in Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file_name = temp_file.name
        df.to_csv(temp_file_name, index=False)
    
    # Upload the temporary file to GCS
    blob.upload_from_filename(temp_file_name, content_type='text/csv')
    print(f"Data uploaded to {destination_blob_name} in bucket {bucket_name}.")

    # Clean up the temporary file
    os.remove(temp_file_name)

def main_model():
    # Define the bucket name and file paths
    bucket_name = 'dermadata'
    initial_data_blob = 'ml_folder/112rows.csv'
    cleaned_data_blob = 'ml_folder/cleaned_112.csv'
    all_fixed_data_blob = 'ml_folder/allfixed.csv'
    combined_features_blob = 'ml_folder/combined_features.csv'
    features_blob = 'ml_folder/features.csv'
    test_set_blob = 'ml_folder/test set.csv'
    test_data_blob = 'ml_folder/test.csv'
    backend_user_data_blob = 'ml_folder/backend_user_data.csv'
    onehot_train_blob = 'ml_folder/onehot_train.csv'
    onehot_test_blob = 'ml_folder/onehot_test.csv'

    # Read the initial dataset from GCS
    data = read_csv_from_gcs(bucket_name, initial_data_blob)

    data.columns = data.columns.str.strip()
    data = data.drop(['What active ingredient (or ingredients) are present for the concern?', 
                      'If there is fragrance in the product, is it impacting the rating? (put N/A if no fragrance)'], axis=1)

    rating_map = {
        'Great': 'Great',
        ' Excellent': 'Excellent',
        'Excellent ': 'Excellent',
        'Excellent': 'Excellent',
        ' Great': 'Great',
        'Ok': 'Ok',
        'Not recommended': 'Not recommended',
        'Not recommended ': 'Not recommended'
    }
    data['Rating (Not recommended, OK, Great, Excellent)'] = data['Rating (Not recommended, OK, Great, Excellent)'].str.strip().map(rating_map)

    # Write cleaned data back to GCS
    write_csv_to_gcs(data, bucket_name, cleaned_data_blob)

    data = read_csv_from_gcs(bucket_name, cleaned_data_blob)

    df = read_csv_from_gcs(bucket_name, all_fixed_data_blob)

    data['Product Link Copy'] = data['Product Link']  # Copy the column before setting it as index
    df['Product Link Copy'] = df['Product Link']

    df.set_index('Product Link', inplace=True)
    data.set_index('Product Link', inplace=True)

    matching_links = data.index.intersection(df.index)
    print(f'Number of matching product links: {len(matching_links)}')

    data.loc[matching_links, 'Skin_Type_P'] = df.loc[matching_links, 'Skin Type']
    data.loc[matching_links, 'Skincare_Concerns_P'] = df.loc[matching_links, 'Skincare Concerns']
    data.loc[matching_links, 'Fragrance_Free_P'] = df.loc[matching_links, 'Fragrance Free']

    def clean_skin_type(s):
        s = s.lower().replace("and", ",").replace("\n", "").replace("[", "").replace("]", "").replace("'", "").strip()
        return ','.join(sorted(set(s.replace(",", " ").split())))

    data['Cleaned_Skin_Type'] = data['Skin_Type_P'].apply(clean_skin_type)

    def clean_skincare_concerns(s):
        concern_map = {
            r'\bdryness\b': 'Dryness',
            r'\boiliness\b': 'Oiliness',
            r'fine\s+lines\s*(and)?\s*wrinkles|loss\s+of\s+firmness\s*(and)?\s*elasticity': 'Aging',
            r'\bacne\b': 'Acne',
            r'\bdark\s+spots\b': 'Dark Spots'
        }

        s = s.lower().replace("\n", " ").replace("[", "").replace("]", "").replace("'", " ").replace(",", " ").strip()
        concerns = set()

        for pattern, concern in concern_map.items():
            if re.search(pattern, s):
                concerns.add(concern)

        return ', '.join(sorted(concerns))

    data['Cleaned_Skincare_Concerns'] = data['Skincare_Concerns_P'].apply(clean_skincare_concerns)

    # Write combined features data back to GCS
    write_csv_to_gcs(data, bucket_name, combined_features_blob)

    data.drop(['Skin_Type_P','Skincare_Concerns_P'], axis=1, inplace=True)

    # Write features data back to GCS
    write_csv_to_gcs(data, bucket_name, features_blob)

    df = read_csv_from_gcs(bucket_name, features_blob)

    def expand_multilabel_col(df, column_name, prefix):
        dummies = df[column_name].str.get_dummies(sep=',')
        dummies.columns = [prefix + col.strip() for col in dummies.columns]  # Add prefix and strip spaces
        return dummies

    categorical_columns = ['Skin type', 'Concern', 'Sensitivity', 'Fragrance Preference', 'Degree of Concern', 'Fragrance_Free_P']
    one_hot_encoded_data = pd.get_dummies(df[categorical_columns])

    one_hot_cleaned_skin_type = expand_multilabel_col(df, 'Cleaned_Skin_Type', 'SkinType_')
    one_hot_cleaned_skincare_concerns = expand_multilabel_col(df, 'Cleaned_Skincare_Concerns', 'Skincare_')

    temp_encoded_df = pd.concat([one_hot_encoded_data, one_hot_cleaned_skin_type, one_hot_cleaned_skincare_concerns], axis=1)

    final_encoded_df = temp_encoded_df.groupby(temp_encoded_df.columns, axis=1).sum()

    final_encoded_df['Rating'] = df['Rating (Not recommended, OK, Great, Excellent)']
    final_encoded_df['Product Link'] = df['Product Link Copy'].astype('category')

    train_encoded_df = final_encoded_df.copy()

    train_encoded_df.drop('SkinType_sensitive', axis=1, inplace=True)

    # Write onehot train data back to GCS
    write_csv_to_gcs(train_encoded_df, bucket_name, onehot_train_blob)

    rating_mapping = {'Not recommended': 0, 'Ok': 1, 'Great': 2, 'Excellent': 3}
    train_encoded_df['Rating_Numeric'] = train_encoded_df['Rating'].map(rating_mapping)

    correlation_with_rating = train_encoded_df.corr(numeric_only=True)['Rating_Numeric'].sort_values(ascending=False)

    print("Correlation of each feature with the 'Rating_Numeric' column:")
    print(correlation_with_rating)

    train_data = read_csv_from_gcs(bucket_name, features_blob)

    test_data = read_csv_from_gcs(bucket_name, test_set_blob)

    train_data = train_data[~train_data.index.duplicated(keep='first')]
    test_data = test_data[~test_data.index.duplicated(keep='first')]

    matching_links = test_data.index.intersection(train_data.index)
    print(f'Number of matching product links: {len(matching_links)}')

    test_data.loc[matching_links, 'Fragrance_Free_P'] = train_data.loc[matching_links, 'Fragrance_Free_P']
    test_data.loc[matching_links, 'Cleaned_Skin_Type'] = train_data.loc[matching_links, 'Cleaned_Skin_Type']
    test_data.loc[matching_links, 'Cleaned_Skincare_Concerns'] = train_data.loc[matching_links, 'Cleaned_Skincare_Concerns']

    # Write test data back to GCS
    write_csv_to_gcs(test_data, bucket_name, test_data_blob)

    categorical_columns = ['Skin type', 'Concern', 'Sensitivity', 'Fragrance Preference', 'Degree of Concern', 'Fragrance_Free_P']
    one_hot_encoded_data = pd.get_dummies(test_data[categorical_columns])

    one_hot_cleaned_skin_type = expand_multilabel_col(test_data, 'Cleaned_Skin_Type', 'SkinType_')
    one_hot_cleaned_skincare_concerns = expand_multilabel_col(test_data, 'Cleaned_Skincare_Concerns', 'Skincare_')

    temp_encoded_df = pd.concat([one_hot_encoded_data, one_hot_cleaned_skin_type, one_hot_cleaned_skincare_concerns], axis=1)

    test_encoded_df = temp_encoded_df.groupby(temp_encoded_df.columns, axis=1).sum()

    test_encoded_df['Rating'] = test_data['Rating']
    test_encoded_df['Product Link'] = test_data['Product Link'].astype('category')

    # Write encoded test data back to GCS
    write_csv_to_gcs(test_encoded_df, bucket_name, backend_user_data_blob)

    test_encoded_df = read_csv_from_gcs(bucket_name, backend_user_data_blob)

    # Only drop the column if it exists
    if 'SkinType_sensitive' in test_encoded_df.columns:
        test_encoded_df.drop('SkinType_sensitive', axis=1, inplace=True)
        print("Column 'SkinType_sensitive' dropped.")
    else:
        print("Column 'SkinType_sensitive' not found in the DataFrame.")

    rating_mapping = {'Not recommended': 0, 'Ok': 1, 'Great': 2, 'Excellent': 3}
    test_encoded_df['Rating_Numeric'] = test_encoded_df['Rating'].map(rating_mapping)

    # Write onehot test data back to GCS
    write_csv_to_gcs(test_encoded_df, bucket_name, onehot_test_blob)

    label_encoder = LabelEncoder()

    train_encoded_df['Product Link Encoded'] = label_encoder.fit_transform(train_encoded_df['Product Link'])
    test_encoded_df['Product Link Encoded'] = label_encoder.transform(test_encoded_df['Product Link'])

    X_train = train_encoded_df.drop(['Rating', 'Product Link', 'Rating_Numeric'], axis=1)
    y_train = train_encoded_df['Rating_Numeric']
    X_test = test_encoded_df.drop(['Rating', 'Product Link', 'Rating_Numeric'], axis=1)
    y_test = test_encoded_df['Rating_Numeric']

    model = DecisionTreeClassifier(random_state=42)

    model.fit(X_train, y_train)

    train_predictions = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, train_predictions)
    print(f"Training Accuracy: {train_accuracy:.2f}")

    test_predictions = model.predict(X_test)
    return test_predictions

main_model()
