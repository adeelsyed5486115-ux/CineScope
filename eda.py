
"""Exploratory Data Analysis module for Movie Rating & Data Explorer."""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# --------------------------------------------------
# 1. LOAD CLEANED MOVIE DATA
# --------------------------------------------------

def load_movies(
    filename: str = "cleaned_movies.csv"
) -> pd.DataFrame:
    """Load cleaned movie dataset from CSV."""

    file_path = Path(filename)

    if not file_path.is_absolute():
        file_path = Path(__file__).resolve().parent / file_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {file_path}"
        )

    return pd.read_csv(file_path)


# --------------------------------------------------
# 2. PREPARE DATA
# --------------------------------------------------

def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare movie data for exploratory analysis."""

    df = df.copy()

    if "vote_average" not in df.columns and "rating" in df.columns:
        df["vote_average"] = df["rating"]

    if "vote_count" not in df.columns and "votes" in df.columns:
        df["vote_count"] = df["votes"]

    if "vote_average" in df.columns:
        df["vote_average"] = pd.to_numeric(
            df["vote_average"],
            errors="coerce"
        )

    if "vote_count" in df.columns:
        df["vote_count"] = pd.to_numeric(
            df["vote_count"],
            errors="coerce"
        ).fillna(0)

    if "release_year" in df.columns:
        df["release_year"] = pd.to_numeric(
            df["release_year"],
            errors="coerce"
        )

    return df


# --------------------------------------------------
# 3. DATASET SUMMARY
# --------------------------------------------------

def dataset_summary(df: pd.DataFrame) -> dict:
    """Return important statistics about the movie dataset."""

    df = prepare_data(df)

    if df.empty:
        return {
            "total_movies": 0,
            "average_rating": 0.0,
            "highest_rating": 0.0,
            "lowest_rating": 0.0,
            "total_votes": 0
        }

    ratings = df["vote_average"].dropna()

    return {
        "total_movies": len(df),

        "average_rating": round(
            ratings.mean(), 2
        ) if not ratings.empty else 0.0,

        "highest_rating": round(
            ratings.max(), 2
        ) if not ratings.empty else 0.0,

        "lowest_rating": round(
            ratings.min(), 2
        ) if not ratings.empty else 0.0,

        "total_votes": int(
            df["vote_count"].sum()
        ) if "vote_count" in df.columns else 0
    }


# --------------------------------------------------
# 4. TOP RATED MOVIES
# --------------------------------------------------

def top_rated_movies(
    df: pd.DataFrame,
    n: int = 10
) -> pd.DataFrame:
    """Return highest rated movies."""

    df = prepare_data(df)

    return (
        df.sort_values(
            by="vote_average",
            ascending=False
        )
        .head(n)
        .reset_index(drop=True)
    )


# --------------------------------------------------
# 5. LOWEST RATED MOVIES
# --------------------------------------------------

def lowest_rated_movies(
    df: pd.DataFrame,
    n: int = 10
) -> pd.DataFrame:
    """Return lowest rated movies."""

    df = prepare_data(df)

    return (
        df.sort_values(
            by="vote_average",
            ascending=True
        )
        .head(n)
        .reset_index(drop=True)
    )


# --------------------------------------------------
# 6. GENRE-WISE MOVIE COUNT
# --------------------------------------------------

def genre_movie_count(
    df: pd.DataFrame
) -> pd.Series:
    """Calculate the number of movies in each genre."""

    if df.empty or "genre" not in df.columns:
        return pd.Series(dtype=int)

    genres = (
        df["genre"]
        .fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
    )

    genres = genres[
        (genres != "")
        & (genres.str.lower() != "unknown")
    ]

    return genres.value_counts()


# --------------------------------------------------
# 7. GENRE-WISE AVERAGE RATING
# --------------------------------------------------

def genre_average_rating(
    df: pd.DataFrame
) -> pd.Series:
    """Calculate average rating for every genre."""

    df = prepare_data(df)

    if df.empty or "genre" not in df.columns:
        return pd.Series(dtype=float)

    genre_df = df[["genre", "vote_average"]].copy()

    genre_df["genre"] = (
        genre_df["genre"]
        .fillna("")
        .astype(str)
        .str.split(",")
    )

    genre_df = genre_df.explode("genre")

    genre_df["genre"] = genre_df["genre"].str.strip()

    genre_df = genre_df[
        (genre_df["genre"] != "")
        & (genre_df["genre"].str.lower() != "unknown")
    ]

    return (
        genre_df.groupby("genre")["vote_average"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
    )


# --------------------------------------------------
# 8. RATING DISTRIBUTION
# --------------------------------------------------

def rating_distribution(
    df: pd.DataFrame
) -> pd.Series:
    """Calculate the distribution of movie ratings."""

    df = prepare_data(df)

    if df.empty:
        return pd.Series(dtype=int)

    ratings = df["vote_average"].dropna()

    bins = [
        0, 2, 4, 6, 8, 10
    ]

    labels = [
        "0-2",
        "2-4",
        "4-6",
        "6-8",
        "8-10"
    ]

    return pd.cut(
        ratings,
        bins=bins,
        labels=labels,
        include_lowest=True
    ).value_counts().sort_index()


# --------------------------------------------------
# 9. RELEASE YEAR ANALYSIS
# --------------------------------------------------

def movies_by_year(
    df: pd.DataFrame
) -> pd.Series:
    """Calculate the number of movies released each year."""

    df = prepare_data(df)

    if df.empty or "release_year" not in df.columns:
        return pd.Series(dtype=int)

    years = df["release_year"].dropna()

    return (
        years.value_counts()
        .sort_index()
        .astype(int)
    )


# --------------------------------------------------
# 10. MOST POPULAR MOVIES
# --------------------------------------------------

def most_voted_movies(
    df: pd.DataFrame,
    n: int = 10
) -> pd.DataFrame:
    """Return movies with the highest number of votes."""

    df = prepare_data(df)

    if "vote_count" not in df.columns:
        return pd.DataFrame()

    return (
        df.sort_values(
            by="vote_count",
            ascending=False
        )
        .head(n)
        .reset_index(drop=True)
    )


# --------------------------------------------------
# 11. GENRE COUNT CHART
# --------------------------------------------------

def plot_genre_distribution(
    df: pd.DataFrame
):
    """Create a bar chart showing movies by genre."""

    genre_counts = genre_movie_count(df)

    if genre_counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))

    genre_counts.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title("Movies by Genre")
    ax.set_xlabel("Genre")
    ax.set_ylabel("Number of Movies")
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()

    return fig


# --------------------------------------------------
# 12. GENRE AVERAGE RATING CHART
# --------------------------------------------------

def plot_genre_ratings(
    df: pd.DataFrame
):
    """Create a chart showing average rating by genre."""

    average_ratings = genre_average_rating(df)

    if average_ratings.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))

    average_ratings.plot(
        kind="bar",
        ax=ax
    )

    ax.set_title("Average Rating by Genre")
    ax.set_xlabel("Genre")
    ax.set_ylabel("Average Rating")
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()

    return fig


# --------------------------------------------------
# 13. RATING DISTRIBUTION CHART
# --------------------------------------------------

def plot_rating_distribution(
    df: pd.DataFrame
):
    """Create a chart showing movie rating distribution."""

    df = prepare_data(df)

    if df.empty:
        return None

    ratings = df["vote_average"].dropna()

    if ratings.empty:
        return None

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.hist(
        ratings,
        bins=10,
        edgecolor="black"
    )

    ax.set_title("Movie Rating Distribution")
    ax.set_xlabel("Movie Rating")
    ax.set_ylabel("Number of Movies")

    fig.tight_layout()

    return fig


# --------------------------------------------------
# 14. RELEASE YEAR CHART
# --------------------------------------------------

def plot_movies_by_year(
    df: pd.DataFrame
):
    """Create a chart showing movies released by year."""

    year_counts = movies_by_year(df)

    if year_counts.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))

    year_counts.plot(
        kind="line",
        marker="o",
        ax=ax
    )

    ax.set_title("Movies Released by Year")
    ax.set_xlabel("Release Year")
    ax.set_ylabel("Number of Movies")

    fig.tight_layout()

    return fig


# --------------------------------------------------
# 15. COMPLETE EDA SUMMARY
# --------------------------------------------------

def generate_eda_report(
    df: pd.DataFrame
) -> dict:
    """Generate a complete exploratory data analysis report."""

    df = prepare_data(df)

    return {
        "dataset_summary": dataset_summary(df),
        "top_rated_movies": top_rated_movies(df),
        "lowest_rated_movies": lowest_rated_movies(df),
        "genre_movie_count": genre_movie_count(df),
        "genre_average_rating": genre_average_rating(df),
        "rating_distribution": rating_distribution(df),
        "movies_by_year": movies_by_year(df),
        "most_voted_movies": most_voted_movies(df)
    }


# --------------------------------------------------
# 16. TEST EDA MODULE
# --------------------------------------------------

if __name__ == "__main__":

    try:
        movies_df = load_movies()

        print("\nDATASET SUMMARY")
        print(dataset_summary(movies_df))

        print("\nTOP RATED MOVIES")
        print(top_rated_movies(movies_df))

        print("\nLOWEST RATED MOVIES")
        print(lowest_rated_movies(movies_df))

        print("\nGENRE MOVIE COUNT")
        print(genre_movie_count(movies_df))

        print("\nGENRE AVERAGE RATINGS")
        print(genre_average_rating(movies_df))

        print("\nRATING DISTRIBUTION")
        print(rating_distribution(movies_df))

        print("\nMOVIES BY YEAR")
        print(movies_by_year(movies_df))

        print("\nMOST VOTED MOVIES")
        print(most_voted_movies(movies_df))

        print("\nEDA analysis completed successfully!")

    except FileNotFoundError as error:
        print(error)
