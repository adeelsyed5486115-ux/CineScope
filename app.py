
"""CineScope - Movie Rating & Data Explorer."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from extractor import (
    search_movies, search_multi, get_trending_movies,
    get_popular_movies, get_upcoming_movies,
    get_top_rated_movies, get_genres,
    discover_movies_by_genre, get_media_details
)

from cleaner import validate_movies, clean_movies

from database import (
    create_table, load_movies_to_database,
    get_all_movies, add_to_watchlist,
    remove_from_watchlist, get_watchlist
)

from eda import (
    dataset_summary, top_rated_movies, most_voted_movies
)


# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="CineScope | Movie Explorer",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #10131c;
    color: white;
}
.main-title {
    font-size: 42px;
    font-weight: 800;
}
.sub-title {
    color: #aab2c5;
}
div[data-testid="stMetric"] {
    background-color: #1b2232;
    padding: 15px;
    border-radius: 10px;
}
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ================= INITIALIZATION =================

try:
    create_table()
except Exception as error:
    st.error(f"Database error: {error}")

defaults = {
    "selected_media": None,
    "search_results": [],
    "search_query": "",
    "raw_movies": [],
    "cleaned_movies": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ================= HELPER FUNCTIONS =================

def poster_url(path):
    if not path:
        return None

    if str(path).startswith("http"):
        return path

    return f"https://image.tmdb.org/t/p/w500{path}"


def title_of(media):
    return media.get("title") or media.get("name") or "Untitled"


def date_of(media):
    return (
        media.get("release_date")
        or media.get("first_air_date")
        or "Unknown"
    )


def media_type(media):
    return media.get("media_type", "movie")


def database_df():
    try:
        data = get_all_movies()

        if isinstance(data, pd.DataFrame):
            return data

        return pd.DataFrame(data or [])

    except Exception:
        return pd.DataFrame()


# ================= DETAILS =================

def show_details(media_id, kind):
    """Show selected movie or TV details."""

    try:
        with st.spinner("Loading details..."):
            data = get_media_details(media_id, kind)

        if not data:
            st.error("No details received from TMDB.")
            return

        left, right = st.columns([1, 2])

        with left:
            image = poster_url(data.get("poster_path"))

            if image:
                st.image(image, use_container_width=True)
            else:
                st.info("Poster unavailable.")

        with right:
            st.subheader(title_of(data))

            if kind == "tv":
                st.caption("📺 TV Series")
                st.write(
                    "**First Air Date:**",
                    data.get("first_air_date", "Unknown")
                )
                st.write(
                    "**Seasons:**",
                    data.get("number_of_seasons", "Unknown")
                )
                st.write(
                    "**Episodes:**",
                    data.get("number_of_episodes", "Unknown")
                )
            else:
                st.caption("🎬 Movie")
                st.write(
                    "**Release Date:**",
                    data.get("release_date", "Unknown")
                )
                st.write(
                    "**Runtime:**",
                    f"{data.get('runtime', 'Unknown')} minutes"
                )

            st.write(
                "**Rating:** ⭐",
                data.get("vote_average", 0),
                "/10"
            )
            st.write("**Votes:**", data.get("vote_count", 0))

            genres = [
                genre["name"]
                for genre in data.get("genres", [])
                if isinstance(genre, dict) and genre.get("name")
            ]

            if genres:
                st.write("**Genres:**", ", ".join(genres))

        st.write("**Overview**")
        st.write(data.get("overview") or "Overview unavailable.")

    except Exception as error:
        st.error(f"Details loading error: {error}")


# ================= MOVIE CARD =================

def movie_card(media, index, section):
    """Display one movie card with its own details panel."""

    media_id = media.get("id")
    kind = media_type(media)
    card_id = f"{section}_{kind}_{media_id}_{index}"

    with st.container(border=True):

        image = poster_url(media.get("poster_path"))

        if image:
            st.image(image, use_container_width=True)
        else:
            st.markdown("### 🎬 Poster unavailable")

        st.markdown(f"**{title_of(media)}**")

        st.caption(
            "📺 TV Series" if kind == "tv" else "🎬 Movie"
        )

        st.write(f"Release: {date_of(media)}")
        st.write(f"⭐ Rating: {media.get('vote_average', 0)}/10")

        if st.button(
            "View Details",
            key=f"details_{card_id}",
            use_container_width=True
        ):
            st.session_state.selected_media = {
                "id": media_id,
                "type": kind,
                "card_id": card_id
            }
            st.rerun()

        if kind == "movie":
            if st.button(
                "📌 Add to Watchlist",
                key=f"watch_{card_id}",
                use_container_width=True
            ):
                try:
                    added = add_to_watchlist(media)

                    if added:
                        st.success("Movie added to Watchlist!")
                    else:
                        st.info("Movie is already in your Watchlist.")

                except Exception as error:
                    st.error(f"Could not add movie: {error}")

        selected = st.session_state.selected_media

        if selected and selected["card_id"] == card_id:
            st.divider()

            if st.button(
                "✖ Close Details",
                key=f"close_{card_id}"
            ):
                st.session_state.selected_media = None
                st.rerun()

            show_details(
                selected["id"],
                selected["type"]
            )


def movie_grid(movies, section):
    if not movies:
        st.info("No results found.")
        return

    for start in range(0, len(movies), 3):
        columns = st.columns(3)

        for position, media in enumerate(movies[start:start + 3]):
            with columns[position]:
                movie_card(
                    media,
                    start + position,
                    section
                )


# ================= HEADER =================

st.markdown(
    '<div class="main-title">🎬 CineScope</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">Discover movies and TV shows, '
    'explore ratings and manage your watchlist.</div>',
    unsafe_allow_html=True
)


# ================= NAVIGATION =================

page = st.radio(
    "Navigation",
    [
        "🏠 Home",
        "🎥 Discover",
        "📌 Watchlist",
        "📊 Analytics",
        "⚙️ ETL Pipeline"
    ],
    horizontal=True,
    key="main_navigation"
)

st.divider()


# ================= GLOBAL SEARCH =================
# Only Home and Discover have global TMDB search.

if page in ["🏠 Home", "🎥 Discover"]:

    with st.form("global_search_form"):
        col1, col2 = st.columns([5, 1])

        with col1:
            search_input = st.text_input(
                "Search",
                placeholder="Search movies or TV shows...",
                label_visibility="collapsed"
            )

        with col2:
            search_button = st.form_submit_button(
                "🔍 Search",
                use_container_width=True
            )

        if search_button:
            if search_input.strip():
                try:
                    st.session_state.search_results = search_multi(
                        search_input.strip()
                    )
                    st.session_state.search_query = search_input.strip()
                    st.session_state.selected_media = None

                except Exception as error:
                    st.error(f"Search failed: {error}")

            else:
                st.warning("Enter a movie or TV show name.")

    # Show global search results only on Home and Discover.

    if st.session_state.search_query:

        st.subheader(
            f"🔎 Results: {st.session_state.search_query}"
        )

        movie_grid(
            st.session_state.search_results,
            "global_search"
        )

        if st.button("Clear Search", key="clear_global_search"):
            st.session_state.search_results = []
            st.session_state.search_query = ""
            st.session_state.selected_media = None
            st.rerun()

        st.divider()


# ================= HOME =================

if page == "🏠 Home":

    st.header("Welcome to CineScope")

    st.subheader("🔥 Trending Movies")

    try:
        movie_grid(get_trending_movies(), "home_trending")

    except Exception as error:
        st.error(f"Could not load trending movies: {error}")

    st.divider()

    st.subheader("⭐ Popular Movies")

    try:
        movie_grid(get_popular_movies(), "home_popular")

    except Exception as error:
        st.error(f"Could not load popular movies: {error}")


# ================= DISCOVER =================

elif page == "🎥 Discover":

    st.header("🎥 Movie Discovery")

    category = st.selectbox(
        "Choose Category",
        [
            "Trending",
            "Popular",
            "Upcoming",
            "Top Rated",
            "Discover by Genre"
        ]
    )

    try:
        if category == "Trending":
            movies = get_trending_movies()

        elif category == "Popular":
            movies = get_popular_movies()

        elif category == "Upcoming":
            movies = get_upcoming_movies()

        elif category == "Top Rated":
            movies = get_top_rated_movies()

        else:
            genres = get_genres()

            if not genres:
                st.warning("Genres unavailable.")
                movies = []

            else:
                genre_name = st.selectbox(
                    "Select Genre",
                    list(genres.values())
                )

                genre_id = next(
                    key for key, value in genres.items()
                    if value == genre_name
                )

                movies = discover_movies_by_genre(genre_id)

        movie_grid(movies, f"discover_{category}")

    except Exception as error:
        st.error(f"Discovery error: {error}")


# ================= WATCHLIST =================

elif page == "📌 Watchlist":

    st.header("📌 My Watchlist")
    st.write("Your personally saved movies.")

    try:
        watchlist = get_watchlist()

        if isinstance(watchlist, pd.DataFrame):
            watchlist = watchlist.to_dict(orient="records")

        # Search only within saved watchlist movies.
        watchlist_search = st.text_input(
            "Search Your Watchlist",
            placeholder="Search saved movies by title...",
            key="watchlist_search"
        )

        if watchlist_search.strip():
            watchlist = [
                movie for movie in watchlist
                if watchlist_search.strip().lower()
                in movie.get("title", "").lower()
            ]

        if not watchlist:
            st.info(
                "No matching saved movies found. "
                "Add movies from Home or Discover."
            )

        else:
            st.write(f"**Movies Found: {len(watchlist)}**")

            for index, movie in enumerate(watchlist):

                # Database uses movie_id as its primary key.
                movie_id = movie.get("movie_id", movie.get("id"))

                left, middle, right = st.columns([1, 3, 1])

                with left:
                    image = poster_url(movie.get("poster_path"))

                    if image:
                        st.image(image, use_container_width=True)
                    else:
                        st.write("🎬")

                with middle:
                    st.subheader(movie.get("title", "Unknown"))

                    rating = movie.get(
                        "rating",
                        movie.get("vote_average", 0)
                    )

                    st.write(f"⭐ Rating: {rating}/10")
                    st.write(
                        f"Release: {movie.get('release_date', 'Unknown')}"
                    )

                with right:
                    if st.button(
                        "Remove",
                        key=f"remove_{movie_id}_{index}"
                    ):
                        remove_from_watchlist(movie_id)
                        st.rerun()

                st.divider()

    except Exception as error:
        st.error(f"Watchlist error: {error}")


# ================= ANALYTICS =================

elif page == "📊 Analytics":

    st.header("📊 Movie Analytics")

    df = database_df()

    if df.empty:
        st.info("No data available. Run the ETL Pipeline first.")

    else:
        rating_col = (
            "vote_average" if "vote_average" in df else "rating"
        )

        votes_col = (
            "vote_count" if "vote_count" in df else "votes"
        )

        for column in [rating_col, votes_col]:
            if column in df:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        average = (
            df[rating_col].mean()
            if rating_col in df else 0
        )

        votes = (
            df[votes_col].sum()
            if votes_col in df else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Movies", len(df))

        c2.metric(
            "Average Rating",
            f"{average:.2f}" if pd.notna(average) else "N/A"
        )

        c3.metric(
            "Total Votes",
            f"{int(votes):,}" if pd.notna(votes) else "N/A"
        )

        st.divider()

        st.subheader("📋 Dataset Summary")

        try:
            summary = dataset_summary(df)

            st.dataframe(
                pd.DataFrame(
                    summary.items(),
                    columns=["Metric", "Value"]
                ) if isinstance(summary, dict) else summary,
                use_container_width=True,
                hide_index=True
            )

        except Exception as error:
            st.warning(f"Summary unavailable: {error}")

        st.subheader("🏆 Top Rated Movies")

        try:
            st.dataframe(
                top_rated_movies(df),
                use_container_width=True,
                hide_index=True
            )

        except Exception as error:
            st.warning(f"Top rated data unavailable: {error}")

        st.subheader("🗳️ Most Voted Movies")

        try:
            st.dataframe(
                most_voted_movies(df),
                use_container_width=True,
                hide_index=True
            )

        except Exception as error:
            st.warning(f"Voting data unavailable: {error}")

        if rating_col in df:
            st.subheader("📈 Rating Distribution")

            st.bar_chart(
                df[rating_col]
                .dropna()
                .round()
                .value_counts()
                .sort_index()
            )

        if "genre" in df:
            st.subheader("🎭 Movies by Genre")

            counts = (
                df["genre"]
                .dropna()
                .astype(str)
                .str.split(",")
                .explode()
                .str.strip()
                .value_counts()
            )

            st.bar_chart(counts)

            if rating_col in df:
                st.subheader("⭐ Average Rating by Genre")

                genre_data = df[
                    ["genre", rating_col]
                ].dropna().copy()

                genre_data["genre"] = (
                    genre_data["genre"]
                    .astype(str)
                    .str.split(",")
                )

                genre_data = genre_data.explode("genre")

                averages = (
                    genre_data
                    .groupby("genre")[rating_col]
                    .mean()
                )

                st.bar_chart(averages)

        if "release_year" in df:
            st.subheader("📅 Movies by Release Year")

            years = pd.to_numeric(
                df["release_year"],
                errors="coerce"
            ).dropna()

            st.line_chart(
                years.value_counts().sort_index()
            )

        st.subheader("📥 Download Dataset")

        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "movie_analytics.csv",
            "text/csv"
        )


# ================= ETL PIPELINE =================

elif page == "⚙️ ETL Pipeline":

    st.header("⚙️ ETL Pipeline")

    st.write(
        "**Extract:** Collect TMDB data.  \n"
        "**Transform:** Validate and clean data.  \n"
        "**Load:** Store data in SQLite."
    )

    st.divider()

    st.subheader("1. Extract Movie Data")

    # This is an ETL extraction input, not global search.
    query = st.text_input(
        "Movie title to extract",
        placeholder="Example: Avengers",
        key="etl_query"
    )

    if st.button("Extract Data"):

        if query.strip():

            try:
                st.session_state.raw_movies = search_movies(
                    query.strip()
                )

                st.session_state.cleaned_movies = None

                st.success(
                    f"{len(st.session_state.raw_movies)} movies extracted."
                )

            except Exception as error:
                st.error(f"Extraction failed: {error}")

        else:
            st.warning("Enter a movie name.")

    raw = st.session_state.raw_movies

    if raw:

        st.dataframe(
            pd.DataFrame(raw),
            use_container_width=True
        )

        if st.button("Save Raw JSON"):

            folder = Path("data")
            folder.mkdir(exist_ok=True)

            path = folder / "raw_movies.json"

            path.write_text(
                json.dumps(
                    raw,
                    indent=4,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

            st.success(f"Saved: {path}")

    st.divider()

    st.subheader("2. Validate and Clean")

    if st.button("Validate and Clean"):

        if not raw:
            st.warning("Extract data first.")

        else:
            try:
                validated = validate_movies(raw)

                cleaned = clean_movies(validated)

                if not isinstance(cleaned, pd.DataFrame):
                    cleaned = pd.DataFrame(cleaned)

                st.session_state.cleaned_movies = cleaned

                st.success("Data cleaned successfully.")

            except Exception as error:
                st.error(f"Cleaning failed: {error}")

    cleaned = st.session_state.cleaned_movies

    if cleaned is not None:

        st.dataframe(
            cleaned,
            use_container_width=True
        )

        if st.button("Save Cleaned CSV"):

            folder = Path("data")
            folder.mkdir(exist_ok=True)

            path = folder / "cleaned_movies.csv"

            cleaned.to_csv(path, index=False)

            st.success(f"Saved: {path}")

    st.divider()

    st.subheader("3. Load into Database")

    if st.button("Load into Database"):

        if cleaned is None:
            st.warning("Clean the data first.")

        else:
            try:
                load_movies_to_database(cleaned)

                st.success("Data loaded successfully!")

            except Exception as error:
                st.error(f"Database loading failed: {error}")

    st.divider()

    st.subheader("4. Database Preview")

    df = database_df()

    if df.empty:
        st.info("Database is empty.")

    else:
        st.success(
            f"Database contains {len(df)} movies."
        )

        st.dataframe(
            df,
            use_container_width=True
        )


# ================= FOOTER =================

st.divider()

st.markdown(
    "<center>CineScope | Movie Rating & Data Explorer"
    "<br>Powered by TMDB, Python, Pandas and Streamlit</center>",
    unsafe_allow_html=True
)
