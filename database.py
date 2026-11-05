
"""SQLite database module for Movie Rating & Data Explorer."""

import sqlite3
import json
import pandas as pd

from pathlib import Path


# --------------------------------------------------
# 1. DATABASE CONFIGURATION
# --------------------------------------------------

DB_NAME = "movies.db"
CLEANED_FILE = "cleaned_movies.csv"


# --------------------------------------------------
# 2. DATABASE CONNECTION
# --------------------------------------------------

def connect_database():
    """Create and return a database connection."""

    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row

    return connection


# --------------------------------------------------
# 3. CREATE DATABASE TABLES
# --------------------------------------------------

def create_table():
    """Create movies and watchlist tables if they do not exist."""

    connection = connect_database()
    cursor = connection.cursor()

    # Existing ETL movies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            release_date TEXT,
            release_year INTEGER,
            vote_average REAL,
            vote_count INTEGER,
            genre TEXT
        )
    """)

    # New Watchlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            movie_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            release_date TEXT,
            rating REAL,
            overview TEXT,
            poster_path TEXT,
            genre TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# --------------------------------------------------
# 4. LOAD CLEANED MOVIES INTO DATABASE
# --------------------------------------------------

def load_movies_to_database(
    data: pd.DataFrame | str | Path = CLEANED_FILE
) -> None:
    """Load cleaned movie data into SQLite database."""

    # Accept either DataFrame or CSV file path
    if isinstance(data, pd.DataFrame):
        df = data.copy()

    else:
        file_path = Path(data)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Cleaned movie file not found: {data}"
            )

        df = pd.read_csv(file_path)

    required_columns = [
        "id",
        "title",
        "release_date",
        "release_year",
        "vote_average",
        "vote_count",
        "genre"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    connection = connect_database()

    try:
        for _, row in df.iterrows():

            movie_id = row["id"]

            if pd.isna(movie_id):
                continue

            title = row["title"]

            if pd.isna(title) or not str(title).strip():
                continue

            genre = row["genre"]

            if isinstance(genre, (list, dict)):
                genre = json.dumps(genre)

            elif pd.isna(genre):
                genre = "Unknown"

            release_date = row["release_date"]

            if pd.isna(release_date):
                release_date = None

            release_year = row["release_year"]

            if pd.isna(release_year):
                release_year = None

            vote_average = row["vote_average"]

            if pd.isna(vote_average):
                vote_average = 0

            vote_count = row["vote_count"]

            if pd.isna(vote_count):
                vote_count = 0

            connection.execute("""
                INSERT INTO movies (
                    id,
                    title,
                    release_date,
                    release_year,
                    vote_average,
                    vote_count,
                    genre
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    release_date = excluded.release_date,
                    release_year = excluded.release_year,
                    vote_average = excluded.vote_average,
                    vote_count = excluded.vote_count,
                    genre = excluded.genre
            """, (
                int(movie_id),
                str(title),
                release_date,
                release_year,
                vote_average,
                vote_count,
                str(genre)
            ))

        connection.commit()

    finally:
        connection.close()

    print("Movies successfully loaded into database.")


# --------------------------------------------------
# 5. GET ALL MOVIES
# --------------------------------------------------

def get_all_movies() -> list[dict]:
    """Retrieve all movies from the database."""

    connection = connect_database()

    try:
        cursor = connection.execute(
            "SELECT * FROM movies ORDER BY title"
        )

        movies = [dict(row) for row in cursor.fetchall()]

        return movies

    finally:
        connection.close()


# --------------------------------------------------
# 6. SEARCH MOVIES IN DATABASE
# --------------------------------------------------

def search_database(search_term: str) -> list[dict]:
    """Search movies by title in SQLite database."""

    if not search_term.strip():
        return []

    connection = connect_database()

    try:
        cursor = connection.execute("""
            SELECT *
            FROM movies
            WHERE title LIKE ?
            ORDER BY title
        """, (f"%{search_term.strip()}%",))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# 7. ADD MOVIE TO WATCHLIST
# --------------------------------------------------

def add_to_watchlist(movie: dict) -> bool:
    """Add a movie to the user's watchlist."""

    movie_id = movie.get("id")

    if movie_id is None:
        raise ValueError("Movie ID is required.")

    title = movie.get("title") or movie.get("original_title")

    if not title:
        raise ValueError("Movie title is required.")

    release_date = movie.get("release_date") or None

    rating = movie.get(
        "vote_average",
        movie.get("rating", 0)
    )

    overview = movie.get("overview", "")

    poster_path = movie.get("poster_path")

    genre = movie.get("genre", [])

    if isinstance(genre, list):
        genre = json.dumps(genre)

    elif isinstance(genre, dict):
        genre = json.dumps(genre)

    elif genre is None:
        genre = ""

    connection = connect_database()

    try:
        cursor = connection.execute("""
            INSERT OR IGNORE INTO watchlist (
                movie_id,
                title,
                release_date,
                rating,
                overview,
                poster_path,
                genre
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            int(movie_id),
            title,
            release_date,
            rating,
            overview,
            poster_path,
            str(genre)
        ))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# --------------------------------------------------
# 8. REMOVE MOVIE FROM WATCHLIST
# --------------------------------------------------

def remove_from_watchlist(movie_id: int) -> bool:
    """Remove a movie from the watchlist."""

    connection = connect_database()

    try:
        cursor = connection.execute("""
            DELETE FROM watchlist
            WHERE movie_id = ?
        """, (movie_id,))

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# --------------------------------------------------
# 9. GET COMPLETE WATCHLIST
# --------------------------------------------------

def get_watchlist() -> list[dict]:
    """Retrieve all saved movies from watchlist."""

    connection = connect_database()

    try:
        cursor = connection.execute("""
            SELECT *
            FROM watchlist
            ORDER BY added_at DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# --------------------------------------------------
# 10. CHECK WATCHLIST MOVIE
# --------------------------------------------------

def is_movie_in_watchlist(movie_id: int) -> bool:
    """Check whether a movie already exists in watchlist."""

    connection = connect_database()

    try:
        cursor = connection.execute("""
            SELECT 1
            FROM watchlist
            WHERE movie_id = ?
        """, (movie_id,))

        return cursor.fetchone() is not None

    finally:
        connection.close()


# --------------------------------------------------
# 11. CLEAR COMPLETE WATCHLIST
# --------------------------------------------------

def clear_watchlist() -> None:
    """Remove all movies from watchlist."""

    connection = connect_database()

    try:
        connection.execute("DELETE FROM watchlist")
        connection.commit()

    finally:
        connection.close()
