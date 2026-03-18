import streamlit as st
import requests
import random

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Movie Recommender", layout="wide")

# -------------------------------
# DARK MODE CSS
# -------------------------------

st.markdown("""
<style>

/* Main background */

.stApp{
background:#020617;
color:white;
}

/* Sidebar */

[data-testid="stSidebar"]{
background:#020617;
color:white;
}

/* Text input */

input{
background:#1e293b !important;
color:white !important;
border-radius:8px !important;
}

/* Selectbox text */

[data-baseweb="select"] div{
color:white !important;
background:#1e293b !important;
}

/* Buttons */

button{
background:#22c55e !important;
color:white !important;
border-radius:8px !important;
font-weight:600 !important;
}

button:hover{
background:#16a34a !important;
color:white !important;
}

/* Labels */

label{
color:white !important;
}

/* Movie cards */

.movie-card{
background:#0f172a;
padding:12px;
border-radius:12px;
text-align:center;
height:420px;
display:flex;
flex-direction:column;
justify-content:space-between;
transition:0.3s;
box-shadow:0 8px 20px rgba(0,0,0,0.6);
}

.movie-card:hover{
transform:scale(1.05);
box-shadow:0 16px 40px rgba(0,0,0,0.9);
}

/* Poster */

.poster{
width:100%;
height:300px;
object-fit:cover;
border-radius:10px;
}

/* Movie title */

.movie-title{
font-size:16px;
font-weight:600;
min-height:40px;
color:white;
}

/* Rating */

.rating{
background:#facc15;
color:black;
padding:4px 12px;
border-radius:20px;
width:fit-content;
margin:auto;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------

st.sidebar.title("⚙️ Filters")

min_rating = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 5.0)

num_movies = st.sidebar.slider("Number of Movies", 1, 20, 10)

sort_by = st.sidebar.selectbox(
    "Sort Movies",
    ["default", "rating"]
)

only_poster = st.sidebar.checkbox("Only Movies With Poster")

shuffle_movies = st.sidebar.checkbox("Shuffle Movies")

# -------------------------------
# HEADER
# -------------------------------

st.title("🎬 Movie Recommendation System")
st.write("Find movies similar to your favorites")

# -------------------------------
# SEARCH
# -------------------------------

query = st.text_input("Search Movie")

suggestions = []

if query:
    res = requests.get(f"{API_URL}/search?q={query}")
    if res.status_code == 200:
        suggestions = res.json()

selected_movie = None

if suggestions:
    selected_movie = st.selectbox("Select Movie", suggestions)

# -------------------------------
# RECOMMENDATION
# -------------------------------

if st.button("Recommend") and selected_movie:

    res = requests.post(
        f"{API_URL}/recommend",
        data={"movie": selected_movie}
    )

    if res.status_code == 200:

        data = res.json()
        movies = data["recommendations"]

        # convert rating safely
        for m in movies:
            try:
                m["rating"] = float(m["rating"])
            except:
                m["rating"] = 0

        # rating filter
        movies = [m for m in movies if m["rating"] >= min_rating]

        # poster filter
        if only_poster:
            movies = [m for m in movies if m["poster"]]

        # sorting
        if sort_by == "Highest Rating":
            movies = sorted(
                movies,
                key=lambda x: x["rating"],
                reverse=True
            )

        # shuffle
        if shuffle_movies:
            random.shuffle(movies)

        # limit
        movies = movies[:num_movies]

        # display
        st.subheader(f"Recommended for {selected_movie}")

        cols = st.columns(5)

        for i, movie in enumerate(movies):

            poster = movie["poster"] if movie["poster"] else "https://via.placeholder.com/300x450"

            with cols[i % 5]:

                st.markdown(
                    f"""
                    <div class="movie-card">
                        <img class="poster" src="{poster}">
                        <div class="movie-title">{movie['title']}</div>
                        <div class="rating">⭐ {movie['rating']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# -------------------------------
# TOP MOVIES
# -------------------------------

st.divider()
st.subheader("🔥 Top Movies")

res = requests.get(API_URL)

if res.status_code == 200:

    data = res.json()
    movies = data["movies"]

    cols = st.columns(5)

    for i, movie in enumerate(movies):

        poster = movie["poster"] if movie["poster"] else "https://via.placeholder.com/300x450"

        with cols[i % 5]:

            st.markdown(
                f"""
                <div class="movie-card">
                    <img class="poster" src="{poster}">
                    <div class="movie-title">{movie['title']}</div>
                    <div class="rating">⭐ {movie['rating']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )