import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import joblib

# 1. Load CSV
df = pd.read_csv("itsm_train.csv")   # Make sure your CSV is here
df['text'] = df['text'].astype(str)

# 2. Encode labels
le = LabelEncoder()
df['label_encoded'] = le.fit_transform(df['label'])

# 3. Create Embeddings Model
model = SentenceTransformer('all-MiniLM-L6-v2')  # very fast + accurate

# 4. Convert all texts → embeddings
embeddings = model.encode(df['text'], show_progress_bar=True)

# 5. Train classifier
clf = LogisticRegression(max_iter=2000)
clf.fit(embeddings, df['label_encoded'])

# 6. Save artifacts
joblib.dump(model, "embedder.joblib")
joblib.dump(clf, "classifier.joblib")
joblib.dump(le, "label_encoder.joblib")

print("TRAINING COMPLETE ✔️")
