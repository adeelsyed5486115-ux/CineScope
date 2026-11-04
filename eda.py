
"""Exploratory Data Analysis and Visualization for Movie Data."""

import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------------
# 1. Project Paths
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = BASE_DIR / "movies.db"

CHARTS_DIR = BASE_DIR / "charts"


# -----------------------------------
# 2. Load Data from Database
# -----------------------------------

def load_movies() -> pd.DataFrame:
    """Load movie records from SQLite database."""

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            "movies.db not found. Run database.py first."
        )

    connection = sqlite3.connect(DATABASE_FILE)

    try:
        df = pd.read_sql_query(
            "SELECT * FROM movies",
            connection
        )

    finally:
        connection.close()

    if df.empty:
        raise ValueError("No movie records found in database.")

    return df


# -----------------------------------
# 3. Dataset Summary
# -----------------------------------

def dataset_summary(df: pd.DataFrame) -> dict:
    """Generate a summary of the movie dataset."""

    summary = {
        "total_movies": len(df),
        "average_rating": round(
            df["vote_average"].mean(), 2
        ),
        "total_votes": int(
            df["vote_count"].fillna(0).sum()
        ),
        "unique_genres": (
            df["genre"].dropna().nunique()
        ),
        "missing_values": int(
            df.isnull().sum().sum()
        )
    }

    return summary


# -----------------------------------
# 4. Top Rated Movies
# -----------------------------------

def top_rated_movies(
    df: pd.DataFrame,
    limit: int = 10,
    min_votes: int = 10
) -> pd.DataFrame:
    """Find the highest-rated movies."""

    filtered_df = df[
        (df["vote_average"].notna()) &
        (df["vote_count"] >= min_votes)
    ].copy()

    return filtered_df.sort_values(
        by="vote_average",
        ascending=False
    ).head(limit)


# -----------------------------------
# 5. Genre Analysis
# -----------------------------------

def genre_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average rating and movie count by genre."""

    genre_df = df[
        ["genre", "vote_average"]
    ].dropna().copy()

    genre_df["genre"] = genre_df["genre"].str.split(", ")

    genre_df = genre_df.explode("genre")

    genre_df = genre_df[
        genre_df["genre"] != "Unknown"
    ]

    result = (
        genre_df.groupby("genre")
        .agg(
            average_rating=("vote_average", "mean"),
            movie_count=("vote_average", "count")
        )
        .round(2)
        .sort_values(
            by="average_rating",
            ascending=False
        )
    )

    return result


# -----------------------------------
# 6. Year Analysis
# -----------------------------------

def year_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze movie count and average rating by year."""

    year_df = df.dropna(
        subset=["release_year"]
    ).copy()

    result = (
        year_df.groupby("release_year")
        .agg(
            movie_count=("id", "count"),
            average_rating=("vote_average", "mean")
        )
        .round(2)
        .sort_index()
    )

    return result


# -----------------------------------
# 7. Create Charts Folder
# -----------------------------------

def create_charts_folder() -> None:
    """Create folder for saving visualizations."""

    CHARTS_DIR.mkdir(exist_ok=True)


# -----------------------------------
# 8. Genre Rating Chart
# -----------------------------------

def plot_genre_ratings(
    genre_df: pd.DataFrame
) -> None:
    """Create a bar chart of average genre ratings."""

    if genre_df.empty:
        print("No genre data available.")
        return

    chart_data = genre_df.sort_values(
        "average_rating"
    )

    plt.figure(figsize=(10, 6))

    plt.barh(
        chart_data.index,
        chart_data["average_rating"]
    )

    plt.title("Average Movie Rating by Genre")
    plt.xlabel("Average Rating")
    plt.ylabel("Genre")

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "genre_ratings.png"
    )

    plt.close()


# -----------------------------------
# 9. Movie Count Chart
# -----------------------------------

def plot_movie_counts(
    genre_df: pd.DataFrame
) -> None:
    """Create a bar chart of movies in each genre."""

    if genre_df.empty:
        print("No genre data available.")
        return

    chart_data = genre_df.sort_values(
        "movie_count",
        ascending=False
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        chart_data.index,
        chart_data["movie_count"]
    )

    plt.title("Number of Movies by Genre")
    plt.xlabel("Genre")
    plt.ylabel("Movie Count")

    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "genre_movie_counts.png"
    )

    plt.close()


# -----------------------------------
# 10. Yearly Movie Trend Chart
# -----------------------------------

def plot_yearly_trend(
    year_df: pd.DataFrame
) -> None:
    """Create a line chart showing yearly movie counts."""

    if year_df.empty:
        print("No release year data available.")
        return

    plt.figure(figsize=(10, 6))

    plt.plot(
        year_df.index,
        year_df["movie_count"],
        marker="o"
    )

    plt.title("Movie Releases by Year")
    plt.xlabel("Release Year")
    plt.ylabel("Number of Movies")

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        CHARTS_DIR / "yearly_movie_trend.png"
    )

    plt.close()


# -----------------------------------
# 11. Main EDA Pipeline
# -----------------------------------

def main() -> None:
    """Run complete EDA and visualization pipeline."""

    try:

        # Load database records
        df = load_movies()

        print("\n========== DATASET SUMMARY ==========")

        summary = dataset_summary(df)

        for key, value in summary.items():
            print(f"{key}: {value}")

        # Top rated movies
        print("\n========== TOP RATED MOVIES ==========")

        top_movies = top_rated_movies(df)

        print(
            top_movies[
                ["title", "vote_average", "vote_count"]
            ].to_string(index=False)
        )

        # Genre analysis
        print("\n========== GENRE ANALYSIS ==========")

        genre_df = genre_analysis(df)

        print(genre_df)

        # Year analysis
        print("\n========== YEAR ANALYSIS ==========")

        year_df = year_analysis(df)

        print(year_df)

        # Generate visualizations
        create_charts_folder()

        plot_genre_ratings(genre_df)

        plot_movie_counts(genre_df)

        plot_yearly_trend(year_df)

        print("\n========== EDA COMPLETED ==========")

        print("All charts saved inside the charts folder.")

    except (FileNotFoundError, ValueError, sqlite3.Error) as error:
        print("EDA Error:", error)


if __name__ == "__main__":
    main()
