from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
import pickle
import requests
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

TMDB_API_KEY = "3f823c8283b2bcaf89d321b4aebc8140"


# Load model files
df = pickle.load(open("df.pkl", "rb"))
indices = pickle.load(open("indices.pkl", "rb"))
tfidf_matrix = pickle.load(open("tfidf_matrix.pkl", "rb"))


# Cache for movie details
movie_cache = {}

# Fetch movie details from TMDB


def fetch_movie_details(title):

    if title in movie_cache:
        return movie_cache[title]

    try:

        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"

        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data["results"]:
            return None

        movie = data["results"][0]

        poster = ""
        if movie.get("poster_path"):
            poster = "https://image.tmdb.org/t/p/w500" + movie["poster_path"]

        rating = movie.get("vote_average", "N/A")

        result = {
            "title": title,
            "poster": poster,
            "rating": rating
        }

        movie_cache[title] = result

        return result

    except Exception as e:

        print("TMDB error:", e)
        return None



# Recommendation Function
def recommend(movie, n=10, min_rating=0, sort_by="default"):

    if movie not in indices:
        return []

    idx = indices[movie]

    sim_scores = cosine_similarity(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()

    similar_idx = sim_scores.argsort()[::-1][1:50]

    results = []

    for i in similar_idx:

        title = df.iloc[i]["title"]

        details = fetch_movie_details(title)

        if not details:
            continue

        rating = details["rating"]

        #  Apply rating filter
        if rating != "N/A" and float(rating) < min_rating:
            continue

        results.append(details)

    # limit number of movies
    results = results[:n]

    #  sorting
    if sort_by == "rating":
        results = sorted(results, key=lambda x: x["rating"], reverse=True)

    return results



# Home Endpoint (Top Movies)
@app.get("/")
def home():

    sample = df.head(8)

    movies = []

    for _, row in sample.iterrows():

        title = row["title"]

        details = fetch_movie_details(title)

        if details:
            movies.append(details)

        else:
            movies.append({
                "title": title,
                "poster": "",
                "rating": "N/A"
            })

    return {"movies": movies}



# Recommendation API
@app.post("/recommend")
def get_recommendations(movie: str = Form(...)):

    recommendations = recommend(movie)

    return {
        "selected_movie": movie,
        "recommendations": recommendations
    }


# Movie Search API
@app.get("/search")
async def search(q: str):

    if not q:
        return JSONResponse([])

    suggestions = df[
        df["title"].str.contains(q, case=False, na=False)
    ]["title"].drop_duplicates().head(10)

    return JSONResponse(suggestions.tolist())