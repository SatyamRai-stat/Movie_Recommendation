import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Movie Recommender", layout="wide")


# CSS 
st.markdown("""
<style>

/* Background */
.stApp {
    background-color: #f1f5f9;
    color: #1e293b;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #e2e8f0;
}

/* Title */
h1 {
    text-align: center;
    color: #1e293b;
}

/* Input */
input {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border-radius: 10px !important;
    border: 1px solid #cbd5f5 !important;
    padding: 10px !important;
}

/* Selectbox */
[data-baseweb="select"] div {
    background-color: #ffffff !important;
    color: #1e293b !important;
}

/* Button */
button {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: bold !important;
}

button:hover {
    transform: scale(1.05);
}

/* Movie Card */
.movie-card {
    background: #ffffff;
    padding: 12px;
    border-radius: 15px;
    text-align: center;
    transition: 0.3s;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.1);
}

.movie-card:hover {
    transform: translateY(-8px);
    box-shadow: 0px 12px 25px rgba(0,0,0,0.2);
}

/* Poster */
.poster {
    width: 100%;
    border-radius: 10px;
}

/* Title */
.movie-title {
    font-size: 15px;
    font-weight: 600;
    margin-top: 8px;
    color: #1e293b;
}

/* Rating */
.rating {
    background: #facc15;
    color: black;
    padding: 4px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-top: 5px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

#SIDEBAR
st.sidebar.title("⚙️ Filters")

min_rating = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 5.0)
num_movies = st.sidebar.slider("Number of Movies", 1, 20, 10)
sort_by = st.sidebar.radio(
    "Sort By",
    ["default", "rating"]
)

# TITLE
st.title("🎬 Smart Movie Recommender")

# SEARCH + LIVE SUGGESTIONS
query = st.text_input("Search Movie")

selected_movie = None

if query:
    res = requests.get(f"{API_URL}/search?q={query}")

    if res.status_code == 200:
        suggestions = res.json()

        if suggestions:
            selected_movie = st.radio(
                            "Suggestions",
                            suggestions,
                            horizontal=True
)


# AUTO RECOMMEND
movie_to_use = None

if selected_movie:
    movie_to_use = selected_movie
if st.button("Recommend"):

    movie_to_use = selected_movie if selected_movie else query

    with st.spinner("Fetching recommendations..."):

        res = requests.post(
            f"{API_URL}/recommend",
            data={
                "movie": movie_to_use,
                "n": num_movies,
                "min_rating": min_rating,
                "sort_by": sort_by
            }
        )

    if res.status_code == 200:

        data = res.json()
        if "error" in data:
            st.error(data["error"])
            st.stop()

        movies = data.get("recommendations", [])
        matched = data.get("matched_movie")

        if not movies:
            st.error("No results found 😢")
        else:
            if matched:
                st.success(f"Showing results for: {matched}")

            cols = st.columns(5)

            for i, m in enumerate(movies):
                poster = m["poster"] or "https://via.placeholder.com/300x450"

                with cols[i % 5]:
                    st.markdown(f"""
                    <div class="movie-card">
                        <img class="poster" src="{poster}">
                        <div>{m['title']}</div>
                        <div class="rating">⭐ {round(m['rating'],1)}</div>
                    </div>
                    """, unsafe_allow_html=True)