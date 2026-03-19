from fastapi import FastAPI, Form, Query
import pickle
import httpx
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv
from rapidfuzz import process

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

app = FastAPI()

df = pickle.load(open("df.pkl", "rb"))
indices = pickle.load(open("indices.pkl", "rb"))
tfidf_matrix = pickle.load(open("tfidf_matrix.pkl", "rb"))

movie_titles = df["title"].tolist()

client = httpx.AsyncClient(timeout=5)
movie_cache = {}

# -------------------------------
# FUZZY MATCH
# -------------------------------
def find_closest_movie(user_input):
    user_input = user_input.lower().strip()

    # ✅ Step 1: Exact match
    for title in movie_titles:
        if user_input == title.lower():
            return title

    # ✅ Step 2: Partial match (contains)
    partial_matches = [
        title for title in movie_titles
        if user_input in title.lower()
    ]

    if partial_matches:
        return partial_matches[0]

    # ✅ Step 3: Fuzzy match (VERY STRICT)
    match, score, _ = process.extractOne(user_input, movie_titles)

    print(f"[FUZZY] {user_input} → {match} ({score})")

    if score < 85:   
        return None

    return match

# -------------------------------
# FETCH MOVIE
# -------------------------------
async def fetch_movie_details(title):

    if title in movie_cache:
        return movie_cache[title]

    try:
        clean_title = title.split("(")[0].strip()

        response = await client.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": clean_title
            }
        )

        data = response.json()

        if not data.get("results"):
            return None

        movie = data["results"][0]

        result = {
            "title": title,
            "poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get("poster_path") else "",
            "rating": float(movie.get("vote_average", 0))
        }

        movie_cache[title] = result
        return result

    except:
        return None

# -------------------------------
# RECOMMEND
# -------------------------------
async def recommend(movie, n=10, min_rating=0, sort_by="default"):

    matched_movie = find_closest_movie(movie)

    if not matched_movie:
        return None, []

    idx = indices[matched_movie]

    sim_scores = cosine_similarity(
        tfidf_matrix[idx:idx+1],
        tfidf_matrix
    ).flatten()

    similar_idx = sim_scores.argsort()[::-1][1:200]

    results = []

    for i in similar_idx:
        title = df.iloc[i]["title"]

        details = await fetch_movie_details(title)

        if not details:
            continue

        if details["rating"] < float(min_rating):
            continue

        results.append(details)

        if len(results) >= n:
            break

    if sort_by == "rating":
        results.sort(key=lambda x: x["rating"], reverse=True)

    return matched_movie, results

# -------------------------------
# RECOMMEND API
# -------------------------------
@app.post("/recommend")
async def get_recommendations(
    movie: str = Form(...),
    n: int = Form(10),
    min_rating: float = Form(0),
    sort_by: str = Form("default")
):
    matched_movie, recommendations = await recommend(movie, n, min_rating, sort_by)

    if not matched_movie:
        return {
        "error": "Movie not found in database",
        "recommendations": []
    }

    return {
    "matched_movie": matched_movie,
    "recommendations": recommendations
}

# -------------------------------
# LIVE SEARCH API
# -------------------------------
@app.get("/search")
async def search(q: str = Query("")):
    if not q:
        return []

    suggestions = df[
        df["title"].str.contains(q, case=False, na=False)
    ]["title"].drop_duplicates().head(8)

    return suggestions.tolist()

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()