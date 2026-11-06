from datetime import datetime, timezone, timedelta
import csv
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from recipe_scrapers import scrape_html
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

AZ_INDEX_URL = "https://www.allrecipes.com/recipes-a-z-6735880"
OUTPUT_CSV = "allrecipes_new_monthly_recipes.csv"


def get_sub_index_links(main_url):
    print(f"Scanning main A-Z index page: {main_url}")
    try:
        res = requests.get(main_url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"Failed to fetch A-Z page. Status: {res.status_code}")
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        sub_links = set()

        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if href and ("recipes-a-z" in href or "recipe" in href):
                full_url = urljoin(main_url, href)
                if "allrecipes.com" in full_url:
                    sub_links.add(full_url)

        print(f"-> Discovered {len(sub_links)} total sub-index pages.")
        return list(sub_links)
    except Exception as e:
        print(f"Error fetching A-Z main page: {e}")
        return []


def get_recipe_links_from_sub(sub_url):
    recipe_urls = set()
    try:
        res = requests.get(sub_url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if href and "/recipe/" in href:
                full_url = urljoin(sub_url, href)
                if "allrecipes.com/recipe/" in full_url:
                    recipe_urls.add(full_url)

        return list(recipe_urls)
    except Exception:
        return []


def main():
    # Calculate the cutoff date (30 days ago from today)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    print(
        f"Filtering for recipes published or updated since: {cutoff_date.strftime('%Y-%m-%d')}"
    )

    sub_indexes = get_sub_index_links(AZ_INDEX_URL)
    all_recipe_urls = set()

    print("\nScanning all sub-indexes for recipe links...")
    for idx, sub_url in enumerate(sub_indexes, 1):
        print(f"Checking sub-index ({idx}/{len(sub_indexes)}): {sub_url}")
        found_links = get_recipe_links_from_sub(sub_url)
        all_recipe_urls.update(found_links)
        time.sleep(0.8)

    unique_recipes = list(all_recipe_urls)
    print(
        f"\nFound {len(unique_recipes)} total links. Checking dates and extracting content..."
    )

    new_recipes_database = []
    skipped_count = 0

    for idx, url in enumerate(unique_recipes, 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                continue

            scraper = scrape_html(res.text, org_url=url)

            # Check publication/modification date from Schema.org metadata
            recipe_date = None
            try:
                # recipe-scrapers provides a .ada() or schema lookup method for date
                raw_date = scraper.schema.data.get("datePublished") or scraper.schema.data.get("dateModified")
                if raw_date:
                    recipe_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except Exception:
                pass

            # If a date is found and it's older than 30 days, skip it
            if recipe_date and recipe_date < cutoff_date:
                skipped_count += 1
                continue

            title = scraper.title()
            prep_time = f"{scraper.prep_time()} mins" if scraper.prep_time() else "N/A"
            cook_time = f"{scraper.cook_time()} mins" if scraper.cook_time() else "N/A"
            servings = scraper.yields() or "N/A"

            ingredients = " | ".join(scraper.ingredients())
            instructions = " || ".join(scraper.instructions_list())

            new_recipes_database.append(
                [
                    title,
                    prep_time,
                    cook_time,
                    servings,
                    ingredients,
                    instructions,
                    url,
                ]
            )

            print(f"[{idx}/{len(unique_recipes)}] Added recent recipe: {title}")
            time.sleep(1.2)

        except Exception as e:
            print(f"Skipping link due to error: {e}")

    # Save only the newly published/updated recipes to a monthly CSV file
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Title",
                "Prep Time",
                "Cook Time",
                "Servings",
                "Ingredients",
                "Instructions",
                "URL",
            ]
        )
        writer.writerows(new_recipes_database)

    print(
        f"\nMonthly run complete! Saved {len(new_recipes_database)} new recipes to '{OUTPUT_CSV}' (Skipped {skipped_count} older entries)."
    )


if __name__ == "__main__":
    main()