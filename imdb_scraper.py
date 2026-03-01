import requests
from bs4 import BeautifulSoup
import json
import re
import sys
import time

def scrape_imdb_movies():
    """
    Scrape IMDb for movies with ratings between 3.0 and 5.0
    Returns JSON array with id, title, year, rating
    """
    
    # IMDb advanced search URL - using a different approach
    url = "https://www.imdb.com/search/title/"
    
    params = {
        'user_rating': '3.0,5.0',
        'sort': 'user_rating,desc',
        'count': '50'  # Get more to ensure we have enough
    }
    
    # More realistic browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    print(f"Fetching movies from IMDb...")
    print(f"URL: {url}")
    
    try:
        # Make the request with timeout
        session = requests.Session()
        response = session.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple possible selectors for movie items
        movie_items = []
        
        # Method 1: Standard IMDb lister items
        movie_items = soup.find_all('div', class_='lister-item mode-advanced')
        
        # Method 2: If no items found, try alternative selectors
        if not movie_items:
            movie_items = soup.find_all('div', class_='lister-item')
        
        if not movie_items:
            movie_items = soup.find_all('div', {'data-testid': 'lister-item'})
        
        print(f"Found {len(movie_items)} movie items")
        
        # If still no items, save HTML for debugging
        if len(movie_items) == 0:
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved debug HTML to debug.html")
            
            # Try to find any movie links as fallback
            all_links = soup.find_all('a', href=re.compile(r'/title/tt\d+/'))
            print(f"Found {len(all_links)} title links")
        
        results = []
        
        for item in movie_items[:25]:  # Limit to 25 items
            try:
                # Extract IMDb ID - multiple methods
                imdb_id = None
                
                # Method 1: Look for link with title reference
                link = item.find('a', href=re.compile(r'/title/tt\d+/'))
                if link and link.get('href'):
                    href = link['href']
                    match = re.search(r'tt\d+', href)
                    if match:
                        imdb_id = match.group()
                
                if not imdb_id:
                    continue
                
                # Extract title
                title_elem = item.find('h3', class_='lister-item-header')
                if title_elem:
                    title_link = title_elem.find('a')
                    title = title_link.text.strip() if title_link else ''
                else:
                    title = ''
                
                # Extract year
                year_elem = item.find('span', class_='lister-item-year')
                if year_elem:
                    year_text = year_elem.text.strip()
                    # Extract year using regex (find 4-digit number)
                    year_match = re.search(r'\d{4}', year_text)
                    year = year_match.group() if year_match else ''
                else:
                    year = ''
                
                # Extract rating
                rating_elem = item.find('div', class_='ratings-bar')
                if rating_elem:
                    rating_strong = rating_elem.find('strong')
                    rating = rating_strong.text.strip() if rating_strong else ''
                else:
                    # Try alternative rating location
                    rating_elem = item.find('span', class_='rating-rating')
                    rating = rating_elem.text.strip() if rating_elem else ''
                
                # Only add if we have all required fields
                if imdb_id and title and year and rating:
                    # Ensure rating is between 3 and 5
                    try:
                        rating_float = float(rating)
                        if 3.0 <= rating_float <= 5.0:
                            results.append({
                                "id": imdb_id,
                                "title": title,
                                "year": year,
                                "rating": rating
                            })
                    except ValueError:
                        pass
                    
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
        
        # If we still have no results, try a completely different approach
        if len(results) == 0:
            print("Trying alternative scraping method...")
            return alternative_scrape_method()
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def alternative_scrape_method():
    """Alternative method using a different IMDb endpoint"""
    
    print("Using alternative scraping method...")
    
    # Use a different URL structure
    url = "https://www.imdb.com/search/title/?user_rating=3.0,5.0&sort=user_rating,desc&count=25"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # Try to find all movie containers using a more general approach
        for item in soup.find_all(['div', 'article'], class_=True):
            if 'lister-item' in ' '.join(item.get('class', [])):
                try:
                    # Extract using regex patterns
                    html_str = str(item)
                    
                    # Find ID
                    id_match = re.search(r'/title/(tt\d+)/', html_str)
                    if not id_match:
                        continue
                    imdb_id = id_match.group(1)
                    
                    # Find title
                    title_match = re.search(r'alt="([^"]+)"', html_str)
                    if not title_match:
                        title_match = re.search(r'<a[^>]*>([^<]+)</a>', html_str)
                    title = title_match.group(1) if title_match else ''
                    
                    # Find year
                    year_match = re.search(r'(\d{4})', html_str)
                    year = year_match.group(1) if year_match else ''
                    
                    # Find rating
                    rating_match = re.search(r'(\d+\.\d+)', html_str)
                    rating = rating_match.group(1) if rating_match else ''
                    
                    if imdb_id and title and year and rating:
                        results.append({
                            "id": imdb_id,
                            "title": title,
                            "year": year,
                            "rating": rating
                        })
                        
                        if len(results) >= 25:
                            break
                            
                except Exception as e:
                    continue
        
        return results[:25]
        
    except Exception as e:
        print(f"Alternative method failed: {e}")
        return []

def main():
    """Main function"""
    
    print("="*60)
    print("IMDb Movie Scraper - 23ds3000079@ds.study.iitm.ac.in")
    print("="*60)
    print("Rating Range: 3.0 - 5.0")
    print("="*60)
    
    # Scrape movies
    movies = scrape_imdb_movies()
    
    if movies:
        # Output JSON
        json_output = json.dumps(movies, indent=2)
        print("\n" + json_output)
        
        # Save to file
        with open('imdb_movies.json', 'w') as f:
            f.write(json_output)
        
        print(f"\n✅ Successfully scraped {len(movies)} movies")
        print("📁 Results saved to imdb_movies.json")
        
        # Also save a simple text file with count
        with open('results.txt', 'w') as f:
            f.write(f"IMDb Movies Scraped: {len(movies)}\n")
            f.write(f"Rating Range: 3.0-5.0\n")
            f.write(f"Generated by: 23ds3000079@ds.study.iitm.ac.in\n")
    else:
        print("❌ No movies found")
        
        # Create a sample response for testing
        print("\nCreating sample data for demonstration...")
        sample_movies = [
            {"id": "tt0111161", "title": "The Shawshank Redemption", "year": "1994", "rating": "9.3"},
            {"id": "tt0068646", "title": "The Godfather", "year": "1972", "rating": "9.2"},
            {"id": "tt0071562", "title": "The Godfather Part II", "year": "1974", "rating": "9.0"},
            {"id": "tt0468569", "title": "The Dark Knight", "year": "2008", "rating": "9.0"},
            {"id": "tt0050083", "title": "12 Angry Men", "year": "1957", "rating": "9.0"},
        ]
        
        print(json.dumps(sample_movies[:5], indent=2))
        print("\n⚠️ Note: These are sample movies, not actual results from your rating range.")
        sys.exit(1)

if __name__ == "__main__":
    main()
