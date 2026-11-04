
"""Movie Rating & Data Explorer - Streamlit Web App."""

import requests
import pandas as pd
import streamlit as st

from extractor import (
    search_movies,
    get_genres,
    extract_movie_details,
    save_raw_data
)

from cleaner import (
    validate_movies,
    clean_movies,
    save_cleaned_data
)

from database import (
    create_table,
    load_movies_to_database
)

from eda import (
    load_movies,
    dataset_summary,
    top_rated_movies,
    genre_analysis,
    year_analysis
)


# -----------------------------------
# 1. Page Configuration
# -----------------------------------

st.set_page_config(
    page_title="Movie Rating & Data Explorer",
    page_icon="🎬",
    layout="wide"
)


# -----------------------------------
# 2. Application Heading
# -----------------------------------

st.title("🎬 Movie Rating & Data Explorer")

st.write(
    "Search movies, explore ratings, "
    "and analyze movie data."
)

st.divider()


# -----------------------------------
# 3. Sidebar Search
# -----------------------------------

st.sidebar.header("🔎 Movie Search")

movie_name = st.sidebar.text_input(
    "Enter movie name",
    placeholder="e.g. Spider-Man"
)

page_number = st.sidebar.number_input(
    "Page number",
    min_value=1,
    value=1,
    step=1
)

search_button = st.sidebar.button(
    "Search Movies",
    use_container_width=True
)


# -----------------------------------
# 4. Search and Data Pipeline
# -----------------------------------

if search_button:

    if not movie_name.strip():

        st.sidebar.warning(
            "Please enter a movie name."
        )

    else:

        try:

            with st.spinner("Fetching movie data..."):

                # Extract
                raw_movies = search_movies(
                    movie_name,
                    page=int(page_number)
                )

                if not raw_movies:

                    st.session_state["search_results"] = []
                    st.warning("No movies found.")

                else:

                    # Save original API data
                    save_raw_data(raw_movies)

                    # Get genre information
                    genre_map = get_genres()

                    # Transform API data for display
                    display_movies = [
                        extract_movie_details(movie, genre_map)
                        for movie in raw_movies
                    ]

                    # Validate
                    valid_movies = validate_movies(
                        raw_movies
                    )

                    if not valid_movies:
                        st.warning(
                            "No valid movie records found."
                        )
                    else:

                        # Clean and transform
                        cleaned_df = clean_movies(
                            valid_movies,
                            genre_map
                        )

                        # Save CSV
                        save_cleaned_data(cleaned_df)

                        # Load into database
                        create_table()
                        load_movies_to_database()

                        st.session_state[
                            "search_results"
                        ] = raw_movies

                        st.session_state[
                            "genre_map"
                        ] = genre_map

                        st.success(
                            f"{len(raw_movies)} movies found "
                            "and processed successfully!"
                        )

        except requests.RequestException as error:

            st.error(f"TMDB API error: {error}")

        except (ValueError, TypeError) as error:

            st.error(f"Data processing error: {error}")

        except FileNotFoundError as error:

            st.error(str(error))


# -----------------------------------
# 5. Display Search Results
# -----------------------------------

if "search_results" in st.session_state:

    results = st.session_state["search_results"]

    if results:

        st.header("🎥 Movie Search Results")

        st.write(
            f"Showing {len(results)} results."
        )

        genre_map = st.session_state["genre_map"]

        for start in range(0, len(results), 3):

            columns = st.columns(3)

            for column, movie in zip(
                columns,
                results[start:start + 3]
            ):

                details = extract_movie_details(
                    movie,
                    genre_map
                )

                with column:

                    poster_path = movie.get("poster_path")

                    if poster_path:

                        poster_url = (
                            "https://image.tmdb.org/t/p/w500"
                            + poster_path
                        )

                        st.image(
                            poster_url,
                            use_container_width=True
                        )

                    else:

                        st.info("Poster not available")

                    st.subheader(
                        details["title"]
                    )

                    st.write(
                        f"📅 Release Date: "
                        f"{details['release_year']}"
                    )

                    st.write(
                        f"⭐ Rating: "
                        f"{details['rating']}"
                    )

                    st.write(
                        f"🎭 Genre: "
                        f"{', '.join(details['genre']) or 'Unknown'}"
                    )

                    st.write(
                        f"🗳️ Votes: {details['votes']}"
                    )

                    st.divider()


# -----------------------------------
# 6. Analytics Dashboard
# -----------------------------------

st.header("📊 Movie Analytics Dashboard")

try:

    df = load_movies()

    # Dataset Summary
    summary = dataset_summary(df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Movies",
        summary["total_movies"]
    )

    col2.metric(
        "Average Rating",
        summary["average_rating"]
    )

    col3.metric(
        "Total Votes",
        summary["total_votes"]
    )

    col4.metric(
        "Unique Genres",
        summary["unique_genres"]
    )

    st.divider()

    # Top Rated Movies
    st.subheader("🏆 Top Rated Movies")

    top_movies = top_rated_movies(
        df,
        limit=10
    )

    if not top_movies.empty:

        st.dataframe(
            top_movies[
                [
                    "title",
                    "vote_average",
                    "vote_count",
                    "genre"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No top-rated movies available.")

    st.divider()

    # Genre Analysis
    st.subheader("🎭 Genre Analysis")

    genre_df = genre_analysis(df)

    if not genre_df.empty:

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:

            st.write("Average Rating by Genre")

            st.bar_chart(
                genre_df["average_rating"]
            )

        with chart_col2:

            st.write("Movies by Genre")

            st.bar_chart(
                genre_df["movie_count"]
            )

        st.dataframe(
            genre_df,
            use_container_width=True
        )

    else:

        st.info("No genre information available.")

    st.divider()

    # Year Analysis
    st.subheader("📅 Yearly Movie Trends")

    year_df = year_analysis(df)

    if not year_df.empty:

        st.line_chart(
            year_df["movie_count"]
        )

        st.dataframe(
            year_df,
            use_container_width=True
        )

    else:

        st.info("No yearly data available.")

except (FileNotFoundError, ValueError):

    st.info(
        "Search for movies first to generate "
        "your analytics dashboard."
    )


# -----------------------------------
# 7. Footer
# -----------------------------------

st.divider()

st.caption(
    "Movie Rating & Data Explorer | "
    "Powered by Python, Streamlit and TMDB API"
)
