
"""Database management for Movie Rating & Data Explorer."""

import sqlite3
from pathlib import Path

import pandas as pd


# -----------------------------------
# 1. Database and CSV paths
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = BASE_DIR / "movies.db"
CSV_FILE = BASE_DIR / "cleaned_movies.csv"


# -----------------------------------
# 2. Connect to Database
# -----------------------------------

def connect_database():
    """Connect to the SQLite database."""

    return sqlite3.connect(DATABASE_FILE)


# -----------------------------------
# 3. Create Movies Table
# -----------------------------------

def create_table() -> None:
    """Create the movies table if it does not exist."""

    connection = connect_database()

    try:
        cursor = connection.cursor()

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

        connection.commit()

        print("Movies table created successfully.")

    finally:
        connection.close()


# -----------------------------------
# 4. Load CSV into Database
# -----------------------------------

def load_movies_to_database() -> None:
    """Read cleaned CSV data and insert it into SQLite."""

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            "cleaned_movies.csv not found. Run cleaner.py first."
        )

    df = pd.read_csv(CSV_FILE)

    if df.empty:
        print("No movie records available to insert.")
        return

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
            f"Missing CSV columns: {missing_columns}"
        )

    df = df[required_columns]

    # Convert missing values into Python None
    df = df.astype(object).where(pd.notna(df), None)

    records = []

    for row in df.itertuples(index=False, name=None):
        records.append(
            tuple(
                value.item() if hasattr(value, "item") else value
                for value in row
            )
        )

    connection = connect_database()

    try:
        cursor = connection.cursor()

        cursor.executemany("""
            INSERT OR REPLACE INTO movies (
                id,
                title,
                release_date,
                release_year,
                vote_average,
                vote_count,
                genre
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, records)

        connection.commit()

        print(f"Successfully loaded {len(records)} movies.")

    finally:
        connection.close()


# -----------------------------------
# 5. Retrieve All Movies
# -----------------------------------

def get_all_movies() -> list[tuple]:
    """Retrieve all movie records from database."""

    connection = connect_database()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM movies
            ORDER BY title
        """)

        return cursor.fetchall()

    finally:
        connection.close()


# -----------------------------------
# 6. Search Movies
# -----------------------------------

def search_database(movie_name: str) -> list[tuple]:
    """Search movies by title in SQLite database."""

    if not movie_name.strip():
        return []

    connection = connect_database()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM movies
            WHERE title LIKE ?
            ORDER BY title
        """, (f"%{movie_name.strip()}%",))

        return cursor.fetchall()

    finally:
        connection.close()


# -----------------------------------
# 7. Main Database Pipeline
# -----------------------------------

def main() -> None:
    """Run the complete database pipeline."""

    try:
        create_table()

        load_movies_to_database()

        movies = get_all_movies()

        print(f"\nTotal movies in database: {len(movies)}")

        print("\nFirst 5 movies:")

        for movie in movies[:5]:
            print(movie)

        print("\nDatabase pipeline completed successfully!")

    except (sqlite3.Error, FileNotFoundError, ValueError) as error:
        print("Database error:", error)


if __name__ == "__main__":
    main()
