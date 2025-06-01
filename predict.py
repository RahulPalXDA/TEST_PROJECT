import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Load data
data = pd.read_csv('data.csv')

# Encode hometown and college names
le_hometown = LabelEncoder()
le_college = LabelEncoder()
data['Hometown_encoded'] = le_hometown.fit_transform(data['Hometown'])
data['College_encoded'] = le_college.fit_transform(data['College Name'])

# Split data
X = data[['Hometown_encoded', 'Annual Income (₹)']]
y = data['College_encoded']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=500)
model.fit(X_train, y_train)

# Check if 'Hijli' exists in the dataset
if 'Hijli' in data['Hometown'].values:
    hijli_encoded = le_hometown.transform(['Hijli'])
    input_features = [[hijli_encoded[0], 600000]]
    predicted_college_encoded = model.predict(input_features)
    predicted_college = le_college.inverse_transform(predicted_college_encoded)
    print(f"Predicted College: {predicted_college[0]}")
else:
    print("Error: 'Hijli' not found in the dataset.")
