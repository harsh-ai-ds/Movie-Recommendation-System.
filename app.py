import os
import pickle
import pandas as pd
import requests
from flask import Flask, jsonify, render_template, request
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# --- LOAD LOCAL ML DATA & MODELS ON STARTUP ---
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load pickle files safely
movies_dict = pickle.load(
    open(os.path.join(script_dir, "movie_dict.pkl"), "rb")
)
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(
    open(os.path.join(script_dir, "similarity.pkl"), "rb")
)
movie_embeddings = pickle.load(
    open(os.path.join(script_dir, "movie_embeddings.pkl"), "rb")
)

# Load lightweight sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

TMDB_API_KEY = "75abee69f215d836dbd71095ae7c151f"  # Replace with your TMDB API Key


# --- HELPER FUNCTIONS FOR TMDB API ---
def fetch_poster(movie_id):
  try:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={"75abee69f215d836dbd71095ae7c151f"}"
    res = requests.get(url, timeout=5).json()
    if "poster_path" in res and res["poster_path"]:
      return "https://image.tmdb.org/t/p/w500/" + res["poster_path"]
  except Exception:
    pass
  return "https://via.placeholder.com/500x750?text=Poster+Not+Available"


def fetch_trailer(movie_id):
  try:
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={"75abee69f215d836dbd71095ae7c151f"}&language=en-US"
    res = requests.get(url, timeout=5).json()
    if "results" in res:
      for video in res["results"]:
        if video.get("site") == "YouTube" and video.get("type") == "Trailer":
          return f"https://www.youtube.com/embed/{video['key']}"
  except Exception:
    pass
  return None


# --- ROUTES ---


@app.route("/")
def home():
  # Render the main HTML templates and pass the list of movie titles
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
  top_matches = sorted(
      list(enumerate(distances)), reverse=True, key=lambda x: x[1]
  )[1:13]

  recommendations = []
  for idx, _ in top_matches:
    m_id = movies.iloc[idx].movie_id
    recommendations.append({
        "title": movies.iloc[idx].title,
        "poster": fetch_poster(m_id),
        "trailer": fetch_trailer(m_id),
        "score": None,
    })

  return jsonify({"status": "success", "recommendations": recommendations})


@app.route("/recommend_mood", methods=["POST"])
def recommend_mood():
  data = request.get_json()
  query = data.get("query", "")

  if not query.strip():
    return (
        jsonify(
            {"status": "error", "message": "Query description cannot be empty"}
        ),
        400,
    )

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
        "trailer": fetch_trailer(m_id),
        "score": round(scores[movie_idx].item() * 100, 1),
    })

  return jsonify({"status": "success", "recommendations": recommendations})


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)