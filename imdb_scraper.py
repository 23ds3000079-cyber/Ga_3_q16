import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_imdb_rating_range(min_rating=3.0, max_rating=5.0, max_titles=25):
    """
    Scrape IMDb for movies with ratings between min_rating and max_rating
    
    Args:
        min_rating: Minimum rating (default 3.0)
        max_rating: Maximum rating (default 5.0)
        max_titles: Maximum number of titles to extract (default 25)
    
    Returns:
        List of dictionaries with id, title, year, rating
    """
    
    # Construct IMDb advanced search URL
    base_url = "https://www.imdb.com/search/title/"
    params = {
        'user_rating': f"{min_rating},{max_rating}",
        'sort': 'user_rating,desc',
        'count': max_titles  # Request max titles directly
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Fetching movies with ratings between {min_rating} and {max_rating}...")
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all movie containers
        movie_containers = soup.find_all('div', class_='lister-item mode-advanced')
        
        results = []
        
        for container in movie_containers[:max_titles]:
            try:
                # Extract IMDb ID from the link
                link_tag = container.find('a', href=True)
                if link_tag and '/title/' in link_tag['href']:
                    # Extract ID from href like /title/tt1234567/
                    href = link_tag['href']
                    imdb_id = href.split('/title/')[1].split('/')[0]
                else:
                    continue
                
                # Extract title
                title_tag = container.find('h3', class_='lister-item-header').find('a')
                title = title_tag.text.strip() if title_tag else "N/A"
                
                # Extract year
                year_tag = container.find('span', class_='lister-item-year')
                year = year_tag.text.strip() if year_tag else "N/A"
                # Clean up year (remove parentheses)
                year = year.replace('(', '').replace(')', '').replace('I', '').strip()
                
                # Extract rating
                rating_tag = container.find('div', class_='ratings-bar')
                if rating_tag:
                    rating_value = rating_tag.find('strong')
                    rating = rating_value.text.strip() if rating_value else "N/A"
                else:
                    rating = "N/A"
                
                # Only include if we have all data
                if imdb_id and title != "N/A" and year != "N/A" and rating != "N/A":
                    results.append({
                        "id": imdb_id,
                        "title": title,
                        "year": year,
                        "rating": rating
                    })
                
            except Exception as e:
                print(f"Error parsing a movie entry: {e}")
                continue
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from IMDb: {e}")
        return []

def main():
    """Main function to scrape IMDb and output JSON"""
    
    # Scrape movies with ratings between 3 and 5
    movies = scrape_imdb_rating_range(min_rating=3.0, max_rating=5.0, max_titles=25)
    
    # Output as formatted JSON
    print(json.dumps(movies, indent=2))
    
    # Also save to file
    with open('imdb_movies_3_to_5.json', 'w') as f:
        json.dump(movies, f, indent=2)
    
    print(f"\n✅ Found {len(movies)} movies with ratings between 3 and 5")
    print("📁 Results saved to imdb_movies_3_to_5.json")

if __name__ == "__main__":
    main()
