"""TMDB data extraction module for Movie Rating & Data Explorer."""

import os
import json
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

load_dotenv()

try:
    cloud_token = st.secrets.get("TMDB_ACCESS_TOKEN")
except Exception:
    cloud_token = None

TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN") or cloud_token

BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json"
}


# --------------------------------------------------
# 2. COMMON API REQUEST FUNCTION
# --------------------------------------------------

def make_api_request(
    endpoint: str,
    params: dict | None = None
) -> dict[str, Any]:
    """Send a request to TMDB API and return JSON data."""

    if not TMDB_ACCESS_TOKEN:
        raise ValueError(
            "TMDB access token is missing. Check your .env file."
        )

    url = f"{BASE_URL}/{endpoint.lstrip('/')}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params or {},
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# 3. GLOBAL MOVIE AND TV SEARCH
# --------------------------------------------------

def search_multi(
    query: str,
    page: int = 1
) -> list[dict]:
    """
    Search movies and TV shows together.

    TMDB Multi Search can also return people, so only
    movie and TV results are returned.
    """

    if not query or not query.strip():
        return []

    data = make_api_request(
        "search/multi",
        {
            "query": query.strip(),
            "language": "en-US",
            "page": page,
            "include_adult": False
        }
    )

    results = data.get("results", [])

    return [
        item
        for item in results
        if item.get("media_type") in ("movie", "tv")
    ]


# --------------------------------------------------
# 4. MOVIE SEARCH
# --------------------------------------------------

def search_movies(
    movie_name: str,
    page: int = 1
) -> list[dict]:
    """Search movies by title using TMDB API."""

    if not movie_name or not movie_name.strip():
        return []

    data = make_api_request(
        "search/movie",
        {
            "query": movie_name.strip(),
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 5. TV SERIES SEARCH
# --------------------------------------------------

def search_tv_shows(
    show_name: str,
    page: int = 1
) -> list[dict]:
    """Search TV series by title."""

    if not show_name or not show_name.strip():
        return []

    data = make_api_request(
        "search/tv",
        {
            "query": show_name.strip(),
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 6. TRENDING MOVIES
# --------------------------------------------------

def get_trending_movies(
    time_window: str = "week",
    page: int = 1
) -> list[dict]:
    """Get trending movies for today or this week."""

    if time_window not in ("day", "week"):
        raise ValueError("time_window must be 'day' or 'week'.")

    data = make_api_request(
        f"trending/movie/{time_window}",
        {
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 7. POPULAR MOVIES
# --------------------------------------------------

def get_popular_movies(page: int = 1) -> list[dict]:
    """Get popular movies from TMDB."""

    data = make_api_request(
        "movie/popular",
        {
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 8. UPCOMING MOVIES
# --------------------------------------------------

def get_upcoming_movies(page: int = 1) -> list[dict]:
    """Get upcoming movie releases."""

    data = make_api_request(
        "movie/upcoming",
        {
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 9. TOP RATED MOVIES
# --------------------------------------------------

def get_top_rated_movies(page: int = 1) -> list[dict]:
    """Get top rated movies from TMDB."""

    data = make_api_request(
        "movie/top_rated",
        {
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 10. MOVIE GENRES
# --------------------------------------------------

def get_genres() -> dict[int, str]:
    """Return movie genre IDs mapped to genre names."""

    data = make_api_request(
        "genre/movie/list",
        {"language": "en-US"}
    )

    return {
        genre["id"]: genre["name"]
        for genre in data.get("genres", [])
    }


# --------------------------------------------------
# 11. TV GENRES
# --------------------------------------------------

def get_tv_genres() -> dict[int, str]:
    """Return TV genre IDs mapped to genre names."""

    data = make_api_request(
        "genre/tv/list",
        {"language": "en-US"}
    )

    return {
        genre["id"]: genre["name"]
        for genre in data.get("genres", [])
    }


# --------------------------------------------------
# 12. DISCOVER MOVIES BY GENRE
# --------------------------------------------------

def discover_movies_by_genre(
    genre_id: int,
    page: int = 1
) -> list[dict]:
    """Discover movies belonging to a particular genre."""

    data = make_api_request(
        "discover/movie",
        {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 13. DISCOVER TV SHOWS BY GENRE
# --------------------------------------------------

def discover_tv_by_genre(
    genre_id: int,
    page: int = 1
) -> list[dict]:
    """Discover TV shows belonging to a particular genre."""

    data = make_api_request(
        "discover/tv",
        {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 14. COMPLETE MOVIE DETAILS
# --------------------------------------------------

def get_movie_details(movie_id: int) -> dict:
    """Get complete details of a selected movie."""

    return make_api_request(
        f"movie/{movie_id}",
        {"language": "en-US"}
    )


# --------------------------------------------------
# 15. COMPLETE TV SHOW DETAILS
# --------------------------------------------------

def get_tv_details(tv_id: int) -> dict:
    """Get complete details of a selected TV show."""

    return make_api_request(
        f"tv/{tv_id}",
        {"language": "en-US"}
    )


# --------------------------------------------------
# 16. UNIVERSAL MEDIA DETAILS
# --------------------------------------------------

def get_media_details(
    media_id: int,
    media_type: str
) -> dict:
    """Get details of either a movie or a TV show."""

    if media_type == "movie":
        return get_movie_details(media_id)

    if media_type == "tv":
        return get_tv_details(media_id)

    raise ValueError(
        "media_type must be either 'movie' or 'tv'."
    )


# --------------------------------------------------
# 17. MOVIE CAST INFORMATION
# --------------------------------------------------

def get_movie_credits(movie_id: int) -> dict:
    """Get cast and crew information for a movie."""

    return make_api_request(
        f"movie/{movie_id}/credits",
        {"language": "en-US"}
    )


# --------------------------------------------------
# 18. SIMILAR MOVIES
# --------------------------------------------------

def get_similar_movies(
    movie_id: int,
    page: int = 1
) -> list[dict]:
    """Get movies similar to the selected movie."""

    data = make_api_request(
        f"movie/{movie_id}/similar",
        {
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 19. MOVIE RECOMMENDATIONS
# --------------------------------------------------

def get_movie_recommendations(
    movie_id: int,
    page: int = 1
) -> list[dict]:
    """Get TMDB recommendations for a selected movie."""

    data = make_api_request(
        f"movie/{movie_id}/recommendations",
        {
            "language": "en-US",
            "page": page
        }
    )

    return data.get("results", [])


# --------------------------------------------------
# 20. EXTRACT MOVIE DATA
# --------------------------------------------------

def extract_movie_details(
    movie: dict,
    genre_map: dict[int, str]
) -> dict:
    """Extract and standardize required movie fields."""

    release_date = movie.get("release_date") or ""

    if movie.get("genre_ids") is not None:
        genre_ids = movie.get("genre_ids", [])
    else:
        genre_ids = [
            genre["id"]
            for genre in movie.get("genres", [])
        ]

    genre_names = [
        genre_map[genre_id]
        for genre_id in genre_ids
        if genre_id in genre_map
    ]

    return {
        "id": movie.get("id"),
        "title": movie.get("title") or "Unknown",
        "release_date": release_date,
        "release_year": (
            release_date[:4] if release_date else "Unknown"
        ),
        "rating": movie.get("vote_average", 0),
        "vote_average": movie.get("vote_average", 0),
        "votes": movie.get("vote_count", 0),
        "vote_count": movie.get("vote_count", 0),
        "genre_ids": genre_ids,
        "genre": genre_names,
        "overview": movie.get("overview", ""),
        "poster_path": movie.get("poster_path"),
        "backdrop_path": movie.get("backdrop_path"),
        "original_language": movie.get("original_language", ""),
        "popularity": movie.get("popularity", 0),
        "media_type": "movie"
    }


# --------------------------------------------------
# 21. EXTRACT TV SHOW DATA
# --------------------------------------------------

# --------------------------------------------------
# 21. EXTRACT TV SHOW DATA
# --------------------------------------------------

def extract_tv_details(
    show: dict,
    genre_map: dict[int, str]
) -> dict:
    """Extract and standardize required TV show fields."""

    first_air_date = show.get("first_air_date") or ""

    # Get genre IDs safely
    genre_ids = show.get("genre_ids") or [
        genre["id"]
        for genre in show.get("genres", [])
        if isinstance(genre, dict) and genre.get("id") is not None
    ]

    # Convert genre IDs into genre names
    genre_names = [
        genre_map[genre_id]
        for genre_id in genre_ids
        if genre_id in genre_map
    ]

    return {
        "id": show.get("id"),
        "title": show.get("name") or "Unknown",
        "release_date": first_air_date,
        "release_year": (
            first_air_date[:4] if first_air_date else "Unknown"
        ),
        "rating": show.get("vote_average", 0),
        "vote_average": show.get("vote_average", 0),
        "votes": show.get("vote_count", 0),
        "vote_count": show.get("vote_count", 0),
        "genre_ids": genre_ids,
        "genre": genre_names,
        "overview": show.get("overview", ""),
        "poster_path": show.get("poster_path"),
        "backdrop_path": show.get("backdrop_path"),
        "original_language": show.get("original_language", ""),
        "popularity": show.get("popularity", 0),
        "media_type": "tv"
    }


# --------------------------------------------------
# 22. SAVE RAW DATA
# --------------------------------------------------

def save_raw_data(
    movies: list[dict],
    filename: str = "raw_movies.json"
) -> None:
    """Save raw movie data to a JSON file."""

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            movies,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Raw data saved to {filename}")