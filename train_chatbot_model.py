
import json
import numpy as np
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import MultinomialNB

# Load dataset
with open("chatbot_intents.json") as f:
    data = json.load(f)

# Extract patterns and tags
patterns = []
tags = []

for intent in data["intents"]:
    for pattern in intent["patterns"]:
        patterns.append(pattern.lower())
        tags.append(intent["tag"])

# Use default tokenizer
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(patterns)

# Encode the output labels
le = LabelEncoder()
y = le.fit_transform(tags)

# Train the classifier
model = MultinomialNB()
model.fit(X, y)

# Evaluate
accuracy = model.score(X, y)
print(f"Training Accuracy: {accuracy:.4f}")

# Save the model and encoders
joblib.dump(model, "chatbot_model.pkl")
joblib.dump(vectorizer, "chatbot_vectorizer.pkl")
joblib.dump(le, "chatbot_label_encoder.pkl")
