import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer

print("📦 Loading movie data from 'movie_dict.pkl'...")

try:
  # Load your existing movie dictionary pickle file
  movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
  movies = pd.DataFrame(movies_dict)
  print(f"✅ Successfully loaded {len(movies)} movies.")
except FileNotFoundError:
  print(
      "❌ Error: 'movie_dict.pkl' not found. Please make sure this script is in"
      " the same folder as your pickle file."
  )
  exit()

# Combine available text columns for rich semantic understanding
# (Safely checks for 'overview' and 'tags' columns in your dataframe)
if "overview" in movies.columns and "tags" in movies.columns:
  movies["combined_text"] = (
      movies["overview"].fillna("") + " " + movies["tags"].fillna("")
  )
elif "overview" in movies.columns:
  movies["combined_text"] = movies["overview"].fillna("")
elif "tags" in movies.columns:
  movies["combined_text"] = movies["tags"].fillna("")
else:
  # Fallback to the text/title column if specific metadata columns aren't found
  text_columns = movies.select_dtypes(include=["object"]).columns
  movies["combined_text"] = movies[text_columns[0]].fillna("")

print(
    "🤖 Loading Sentence Transformer model ('all-MiniLM-L6-v2')... Please"
    " wait."
)
# This lightweight model converts text into smart semantic vectors locally
model = SentenceTransformer("all-MiniLM-L6-v2")

print("🔄 Generating embeddings for all movies (this may take a short moment)...")
movie_embeddings = model.encode(
    movies["combined_text"].tolist(), show_progress_bar=True
)

print("💾 Saving embeddings to 'movie_embeddings.pkl'...")
pickle.dump(movie_embeddings, open("movie_embeddings.pkl", "wb"))

print(
    "✨ Success! 'movie_embeddings.pkl' has been created. You can now run your"
    " Streamlit app."
)