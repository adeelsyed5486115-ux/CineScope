"""Data validation, cleaning and transformation for movie data."""

import json
from pathlib import Path

import pandas as pd
import requests
from pydantic import BaseModel, Field, ValidationError

from extractor import get_genres


# -----------------------------------
# 1. Pydantic Movie Model
# -----------------------------------

class Movie(BaseModel):

    id: int | None = None
    title: str | None = None
    release_date: str | None = None
    vote_average: float | None = None
    vote_count: int | None = None
    genre_ids: list[int] = Field(default_factory=list)


# -----------------------------------
# 2. Load Raw JSON Data
# -----------------------------------

def load_raw_data(filename: str = "raw_movies.json") -> list[dict]:
    """Load raw movie data from JSON file."""

    file_path = Path(__file__).resolve().parent / filename

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of movies.")

    return data


# -----------------------------------
# 3. Validate Movie Data
# -----------------------------------

def validate_movies(raw_movies: list[dict]) -> list[dict]:
    """Validate raw movie records using Pydantic."""

    valid_movies = []

    for movie_data in raw_movies:

        try:
            movie = Movie(**movie_data)

            valid_movies.append(movie.__dict__)

        except ValidationError as error:
            print("Invalid movie record skipped:", error)

        except (TypeError, ValueError) as error:
            print("Invalid movie data skipped:", error)

    print(f"Valid movies: {len(valid_movies)}")
    print(f"Invalid movies: {len(raw_movies) - len(valid_movies)}")

    return valid_movies


# -----------------------------------
# 4. Convert Genre IDs to Names
# -----------------------------------

def convert_genres(
    genre_ids: list[int],
    genre_map: dict[int, str]
) -> str:
    """Convert TMDB genre IDs into readable genre names."""

    genre_names = [
        genre_map[genre_id]
        for genre_id in genre_ids
        if genre_id in genre_map
    ]

    return ", ".join(genre_names) if genre_names else "Unknown"


# -----------------------------------
# 5. Clean and Transform Data
# -----------------------------------

def clean_movies(
    movies: list[dict],
    genre_map: dict[int, str]
) -> pd.DataFrame:
    """Clean and transform validated movie data."""

    df = pd.DataFrame(movies)

    if df.empty:
        return df

    # Remove movies without a title
    df["title"] = df["title"].fillna("").astype(str).str.strip()

    df = df[df["title"] != ""].copy()

    # Remove duplicate movies using TMDB ID
    df = df.drop_duplicates(subset=["id"], keep="first")

    # Handle missing release dates
    df["release_date"] = (
        df["release_date"].fillna("").astype(str).str.strip()
    )

    df.loc[df["release_date"] == "", "release_date"] = "Unknown"

    # Convert rating into numeric values
    df["vote_average"] = pd.to_numeric(
        df["vote_average"], errors="coerce"
    )

    # Handle missing vote counts
    df["vote_count"] = pd.to_numeric(
        df["vote_count"], errors="coerce"
    ).fillna(0).astype(int)

    # Convert genre IDs into genre names
    df["genre"] = df["genre_ids"].apply(
        lambda ids: convert_genres(ids, genre_map)
    )

    # Extract release year
    release_dates = pd.to_datetime(
        df["release_date"], errors="coerce"
    )

    df["release_year"] = release_dates.dt.year.astype("Int64")

    # Remove original genre ID column
    df = df.drop(columns=["genre_ids"])

    # Arrange final columns
    df = df[
        [
            "id",
            "title",
            "release_date",
            "release_year",
            "vote_average",
            "vote_count",
            "genre"
        ]
    ]

    df = df.reset_index(drop=True)

    return df


# -----------------------------------
# 6. Save Cleaned Data
# -----------------------------------

def save_cleaned_data(
    df: pd.DataFrame,
    filename: str = "cleaned_movies.csv"
) -> None:
    """Save cleaned movie data into CSV format."""

    file_path = Path(__file__).resolve().parent / filename

    df.to_csv(file_path, index=False, encoding="utf-8-sig")

    print(f"Cleaned data saved to: {file_path}")


# -----------------------------------
# 7. Main Pipeline
# -----------------------------------

def main() -> None:
    """Run the complete data cleaning pipeline."""

    try:

        # Load raw data
        raw_movies = load_raw_data()

        print(f"Raw movies loaded: {len(raw_movies)}")

        # Validate data
        valid_movies = validate_movies(raw_movies)

        if not valid_movies:
            print("No valid movie records available.")
            return

        # Get TMDB genre information
        genre_map = get_genres()

        # Clean and transform data
        cleaned_df = clean_movies(valid_movies, genre_map)

        if cleaned_df.empty:
            print("No movies available after cleaning.")
            return

        # Save cleaned data
        save_cleaned_data(cleaned_df)

        # Display results
        print("\nCleaned Movie Data:")
        print(cleaned_df.head())

        print("\nDataset Information:")
        print(cleaned_df.info())

        print("\nCleaning completed successfully!")

    except FileNotFoundError:
        print("Error: raw_movies.json file not found.")

    except json.JSONDecodeError:
        print("Error: Invalid JSON file.")

    except requests.RequestException as error:
        print("TMDB API error:", error)

    except (ValueError, TypeError) as error:
        print("Data processing error:", error)


if __name__ == "__main__":
    main()
