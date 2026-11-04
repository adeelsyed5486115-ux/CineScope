import requests

from extractor import (
    search_movies,
    get_genres,
    extract_movie_details,
    save_raw_data
)


def main() -> None:
    """Run the movie search and data extraction program."""

    movie_name = input("Enter movie name: ").strip()

    if not movie_name:
        print("Please enter a movie name.")
        return

    page_input = input("Enter page number (default 1): ").strip()

    try:
        page = int(page_input) if page_input else 1

        if page < 1:
            print("Page number must be at least 1.")
            return

        movies = search_movies(movie_name, page=page)

        if not movies:
            print("No movies found on this page.")
            return

        genre_map = get_genres()

        # Save all raw results returned by the API
        save_raw_data(movies)

        print(f"\nFound {len(movies)} movies on page {page}:\n")

        for movie in movies[:5]:
            details = extract_movie_details(movie, genre_map)

            print("Title:", details["title"])
            print("Release Date:", details["release_year"])
            print("Rating:", details["rating"])
            print("Genre:", ", ".join(details["genre"]) or "Unknown")
            print("Votes:", details["votes"])
            print("-" * 30)

        if len(movies) > 5:
            print("Showing first 5 movies. More results are available on this page.")

    except ValueError as error:
        print("Invalid input or configuration:", error)

    except requests.RequestException as error:
        print("API or network error:", error)

    except RuntimeError as error:
        print("Error:", error)


if __name__ == "__main__":
    main()