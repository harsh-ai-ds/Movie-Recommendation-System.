import os
import joblib
import pandas as pd
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- LOAD LIGHTWEIGHT DATA AT STARTUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load metadata normally (small file)
movies_dict = joblib.load(os.path.join(script_dir, "movie_dict.pkl"))
movies = pd.DataFrame(movies_dict)

# Memory-map the similarity matrix so it doesn't bloat active RAM
similarity = joblib.load(
    os.path.join(script_dir, "similarity.pkl"), mmap_mode="r"
)

# --- LAZY-LOAD HEAVY AI MODELS (Prevents Startup OOM Crash on Render 512MB) ---
_model = None
_movie_embeddings = None


def get_sentence_model():
  global _model
  if _model is None:
    from sentence_transformers import SentenceTransformer

    _model = SentenceTransformer("all-MiniLM-L6-v2")
  return _model


def get_movie_embeddings():
  global _movie_embeddings
  if _movie_embeddings is None:
    _movie_embeddings = joblib.load(
        os.path.join(script_dir, "movie_embeddings.pkl"), mmap_mode="r"
    )
  return _movie_embeddings


TMDB_API_KEY = "75abee69f215d836dbd71095ae7c151f"  # Replace with your TMDB API Key


# --- HELPER FUNCTIONS FOR TMDB API & MOVIE STREAMING ---
def fetch_poster(movie_id):
  try:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={"75abee69f215d836dbd71095ae7c151f"}&language=en-US"
    res = requests.get(url, timeout=5).json()
    if "poster_path" in res and res["poster_path"]:
      return "https://image.tmdb.org/t/p/w500" + res["poster_path"]
  except Exception:
    pass
  return "https://via.placeholder.com/500x750?text=No+Image"


def fetch_full_movie_stream(movie_id):
  # Returns full movie embed stream link via TMDB ID
  return f"https://multiembed.mov/?tmdb=1&video_id={movie_id}"


# --- ROUTES ---


@app.route("/")
def home():
  movie_list = sorted(movies["title"].tolist())
  return render_template("index.html", movie_list=movie_list)


@app.route("/recommend_movie", methods=["POST"])
def recommend_movie():
  data = request.get_json()
  movie_name = data.get("movie_name")

  if not movie_name or movie_name not in movies["title"].values:
    return jsonify({"status": "error", "message": "Movie not found"}), 400

  movie_index = movies[movies["title"] == movie_name].index[0]
  distances = similarity[movie_index]

  # CHANGE THIS: Start from 0 to include the movie itself first, then its 11 related movies
  top_matches = sorted(
      list(enumerate(distances)), reverse=True, key=lambda x: x[1]
  )[0:12]

  recommendations = []
  for idx, score in top_matches:
    m_id = movies.iloc[idx].movie_id
    recommendations.append({
        "title": movies.iloc[idx].title,
        "poster": fetch_poster(m_id),
        "trailer": fetch_full_movie_stream(m_id),
        # Show 100% for the exact movie, and similarity percentage for related ones
        "score": (
            100.0 if idx == movie_index else round(score * 100, 1)
        ),
    })

  return jsonify({"status": "success", "recommendations": recommendations})


@app.route("/recommend_mood", methods=["POST"])
def recommend_mood():
  data = request.get_json()
  query = data.get("query", "")

  if not query.strip():
    return (
        jsonify(
            {
                "status": "error",
                "message": "Query description cannot be empty",
            }
        ),
        400,
    )

  # Load model and embeddings only when requested (Lazy Loading)
  model = get_sentence_model()
  movie_embeddings = get_movie_embeddings()

  from sentence_transformers import util

  query_embedding = model.encode(query, convert_to_tensor=True)
  scores = util.cos_sim(query_embedding, movie_embeddings)[0]
  top_results = scores.argsort(descending=True)[:12]

  recommendations = []
  for idx in top_results:
    movie_idx = idx.item()
    m_id = movies.iloc[movie_idx].movie_id
    recommendations.append({
        "title": movies.iloc[movie_idx].title,
        "poster": fetch_poster(m_id),
        "trailer": fetch_full_movie_stream(
            m_id
        ),  # Stream link instead of trailer
        "score": round(scores[movie_idx].item() * 100, 1),
    })

  return jsonify({"status": "success", "recommendations": recommendations})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)