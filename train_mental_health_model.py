
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay

# Load dataset
df = pd.read_csv("mental_health_assessment_dataset.csv")

# Encode Gender and Target
le_gender = LabelEncoder()
df['Gender'] = le_gender.fit_transform(df['Gender'])

le_status = LabelEncoder()
df['Mental_Health_Status_Label'] = le_status.fit_transform(df['Mental_Health_Status'])

# Define features and label
X = df[['Age', 'Gender', 'PHQ9', 'GAD7', 'DASS21_Depression', 'DASS21_Anxiety', 'DASS21_Stress', 'Mood_Score']]
y = df['Mental_Health_Status_Label']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.4f}")

# Save model and encoders
joblib.dump(model, "mental_rf_model.pkl")
joblib.dump(le_gender, "encoder_gender.pkl")
joblib.dump(le_status, "encoder_status.pkl")

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le_status.classes_)
disp.plot(xticks_rotation='vertical')
plt.title("Confusion Matrix - Mental Health Status (Random Forest)")
plt.tight_layout()
plt.savefig("mental_health_confusion_matrix.png")
plt.show()
