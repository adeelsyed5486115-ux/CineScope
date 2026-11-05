
"""Data cleaning and validation module for CineScope."""

import json
from pathlib import Path
from typing import Optional, Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError


# ==========================================
# 1. MOVIE DATA MODEL
# ==========================================

class Movie(BaseModel):
    """Validate individual movie records."""

    id: Optional[int] = None
    title: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: float = 0.0
    vote_count: int = 0

    genre_ids: list[int] = Field(default_factory=list)
    genres: list[dict[str, Any]] = Field(default_factory=list)


# ==========================================
# 2. LOAD RAW DATA
# ==========================================

def load_raw_data(
    filename: str = "raw_movies.json"
) -> list[dict]:

    file_path = Path(filename)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {filename}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Raw data must be a list.")

    return data


# ==========================================
# 3. VALIDATE MOVIES
# ==========================================

def validate_movies(raw_movies: list[dict]) -> list[Movie]:

    valid_movies = []

    for movie_data in raw_movies:

        try:
            movie = Movie(**movie_data)

            if movie.id is None or not movie.title:
                continue

            valid_movies.append(movie)

        except (ValidationError, TypeError, ValueError) as error:
            print(f"Invalid movie skipped: {error}")

    return valid_movies


# ==========================================
# 4. CONVERT GENRES
# ==========================================

def convert_genres(
    genre_ids: list[int],
    genre_map: dict[int, str],
    genres: Optional[list[dict]] = None
) -> str:
    """Convert genre IDs or genre objects into names."""

    genre_names = []

    # First use genre names if TMDB provided them
    if genres:

        for genre in genres:

            if isinstance(genre, dict):
                name = genre.get("name")

                if name:
                    genre_names.append(name)

            elif isinstance(genre, str):
                genre_names.append(genre)

    # Otherwise convert genre IDs
    if not genre_names:

        for genre_id in genre_ids:

            name = genre_map.get(genre_id)

            if name:
                genre_names.append(name)

    # Remove duplicate genre names
    genre_names = list(dict.fromkeys(genre_names))

    return ", ".join(genre_names) if genre_names else "Unknown"


# ==========================================
# 5. CLEAN MOVIES
# ==========================================

def clean_movies(
    movies: list[Movie],
    genre_map: Optional[dict[int, str]] = None
) -> pd.DataFrame:
    """Clean and transform validated movie records."""

    # Automatically fetch genre mapping if not supplied
    if genre_map is None:

        from extractor import get_genres

        genre_map = get_genres()

    cleaned_records = []

    for movie in movies:

        release_date = movie.release_date or "Unknown"

        release_year = (
            int(release_date[:4])
            if release_date != "Unknown"
            and release_date[:4].isdigit()
            else None
        )

        genre = convert_genres(
            movie.genre_ids,
            genre_map,
            movie.genres
        )

        cleaned_records.append({

            "id": movie.id,
            "title": movie.title.strip(),

            "release_date": release_date,
            "release_year": release_year,

            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,

            "genre": genre,

            # Compatibility with existing app
            "rating": movie.vote_average,
            "votes": movie.vote_count
        })

    df = pd.DataFrame(cleaned_records)

    if df.empty:
        return df

    # Remove empty titles
    df["title"] = df["title"].fillna("").str.strip()
    df = df[df["title"] != ""]

    # Remove duplicate movie IDs
    df = df.drop_duplicates(
        subset=["id"],
        keep="first"
    )

    # Handle missing values
    df["release_date"] = df["release_date"].fillna("Unknown")
    df["genre"] = df["genre"].fillna("Unknown")

    # Numeric conversion
    df["vote_average"] = pd.to_numeric(
        df["vote_average"],
        errors="coerce"
    ).fillna(0)

    df["vote_count"] = pd.to_numeric(
        df["vote_count"],
        errors="coerce"
    ).fillna(0).astype(int)

    # Synchronize compatibility columns
    df["rating"] = df["vote_average"]
    df["votes"] = df["vote_count"]

    return df.reset_index(drop=True)


# ==========================================
# 6. SAVE CLEANED DATA
# ==========================================

def save_cleaned_data(
    df: pd.DataFrame,
    filename: str = "cleaned_movies.csv"
) -> None:

    if df.empty:
        print("No cleaned data available.")
        return

    file_path = Path(filename)

    if not file_path.is_absolute():
        file_path = Path(__file__).resolve().parent / file_path

    df.to_csv(
        file_path,
        index=False,
        encoding="utf-8"
    )

    print(f"Cleaned data saved to: {file_path}")


# ==========================================
# 7. COMPLETE ETL PIPELINE
# ==========================================

def main():

    print("Loading raw movie data...")

    raw_movies = load_raw_data()

    print("Validating movies...")

    validated_movies = validate_movies(raw_movies)

    print("Loading genre mapping...")

    from extractor import get_genres
    genre_map = get_genres()

    print("Cleaning movie data...")

    cleaned_df = clean_movies(
        validated_movies,
        genre_map
    )

    print("Saving cleaned data...")

    save_cleaned_data(cleaned_df)

    print("\nETL cleaning completed!")

    print("\nDataset Preview:")
    print(cleaned_df.head())

    print("\nTotal Movies:", len(cleaned_df))


if __name__ == "__main__":
    main()
