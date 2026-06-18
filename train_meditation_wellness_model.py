
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay

# Load dataset
df = pd.read_csv("meditation_wellness_dataset.csv")

# Encode categorical columns
le_gender = LabelEncoder()
df['Gender'] = le_gender.fit_transform(df['Gender'])

le_meditation = LabelEncoder()
df['Previous_Meditation'] = le_meditation.fit_transform(df['Previous_Meditation'])

le_label = LabelEncoder()
df['Wellness_Level_Label'] = le_label.fit_transform(df['Wellness_Level'])

# Define features and label
X = df[['Age', 'Gender', 'Sleep_Hours', 'Screen_Time_Hours', 'Work_Stress',
        'Family_Stress', 'Mindfulness_Score', 'Previous_Meditation']]
y = df['Wellness_Level_Label']

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predictions and accuracy
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.4f}")

# Save model and encoders
joblib.dump(model, "meditation_rf_model.pkl")
joblib.dump(le_gender, "encoder_gender_meditation.pkl")
joblib.dump(le_meditation, "encoder_prev_meditation.pkl")
joblib.dump(le_label, "encoder_wellness_label.pkl")

# Plot confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le_label.classes_)
disp.plot(xticks_rotation='vertical')
plt.title("Confusion Matrix - Meditation & Wellness")
plt.tight_layout()
plt.savefig("meditation_wellness_confusion_matrix.png")
plt.show()
