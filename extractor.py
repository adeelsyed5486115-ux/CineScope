import os
import streamlit as st
import requests
import json
from dotenv import load_dotenv

load_dotenv()

try:
    cloud_token = st.secrets.get("TMDB_ACCESS_TOKEN")
except Exception:
    cloud_token = None

TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN") or cloud_token

BASE_URL = "https://api.themoviedb.org/3"

def search_movies(movie_name : str, page : int = 1)->list[dict]:
    """Search movies by title using TMDB API"""

    if not TMDB_ACCESS_TOKEN:
        raise ValueError("TMDB access token is missing in .env")

    if not movie_name.strip():
        return []
    

    url = f"{BASE_URL}/search/movie"

    headers = {
        "Authorization" : f"Bearer {TMDB_ACCESS_TOKEN}",
        "accept" : "application/json"
    }

    params = {
        "query" : movie_name.strip(),
        "language" : "en-US",
        "page" : page
    }

    response = requests.get(
        url,
        headers = headers,
        params = params,
        timeout = 15
    )

    response.raise_for_status()

    data = response.json()

    return data.get("results", [])

def get_genres()->dict[int , str]:
    """Return a mapping genre IDs to genre names"""

    url = f"{BASE_URL}/genre/movie/list"

    headers = {
        "Authorization" : f"Bearer {TMDB_ACCESS_TOKEN}",
        "accept" : "application/json"
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()

    return {
        genre["id"] : genre["name"]
        for genre in data.get("genres", [])
    }

def extract_movie_details(movie:dict, genre_map:dict[int, str])->dict:
    """Extract the required fields from one movie"""

    release_date = movie.get("release_date") or ""

    genre_names = [genre_map[genre_id] for genre_id in movie.get("genre_ids", []) if genre_id in genre_map]

    return {
        "title" : movie.get("title", "unknown"),
        "rating" : movie.get("vote_average", 0),
        "release_year" : movie.get("release_date", "unknown"),
        "genre" : genre_names,
        "votes" : movie.get("vote_count", 0)
    }

def save_raw_data(movies : list[dict], filename : str = "raw_movies.json")->None:
    """Save raw movie data to a JSON file"""

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(movies, file, indent=4, ensure_ascii=False)

    print(f"Raw data save to {filename}")