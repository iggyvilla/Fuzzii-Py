from functools import cache
from discord.ext.commands.errors import ExtensionAlreadyLoaded
import requests
import json
from bs4 import BeautifulSoup
from requests.api import request

class NHentaiComic:
    def __init__(self, code: int):
        if not isinstance(code, int):
            raise Exception('The code given is not of type int')
        
        self.code = code
        self.thumbnail = None
        self.title = None
        self.favorites = None
        self.pages = []
        self.tags = []
        self.img_extensions = []
        self.scrape()

    def log(self, msg):
        print('[NH.P] -> ' + msg)

    def scrape(self):
        result = requests.get(f'https://nhentai.net/g/{self.code}')

        if result.status_code == 404:
            raise ValueError("The comic does not exist.")
        
        else:

            soup = BeautifulSoup(result.content, 'html.parser')

            self.title = soup.select('h1.title span.pretty')[0].text
            self.log(f'Found title of doujin {self.code} - {self.title}')

            for div in soup.find_all('div'):
                try:
                    if div.attrs['class'][0] == 'container' and div.attrs['id'] == 'bigcontainer':
                        self.thumbnail = div.div.a.img.attrs['data-src']
                    elif div.attrs['class'][0] == 'buttons':
                        self.favorites = int(div.a.span.span.text[1:-1])
                    elif div.attrs['class'][0] == 'thumbs':
                        # Image extensions
                        for thumbnail in div.find_all('div'):
                            self.img_extensions.append(thumbnail.a.img['data-src'][-3:])
                except Exception:
                    continue

            for span in soup.find_all('span'):
                try:
                    span_class = span.attrs['class'][0]
                    
                    if span_class == "tags":
                        for a_tag in span.find_all('a'):
                            self.tags.append(a_tag.span.text.title())
                except KeyError:
                    continue
            
            # Gets the first page of the comic to derive links to all pages
            num_pages = int(self.tags[-1])
            result = requests.get(f'https://nhentai.net/g/{self.code}/1/')
            soup = BeautifulSoup(result.content, 'html.parser')

            url = soup.select('#image-container')
            link = url[0].a.img.attrs['src']
    
            for k in range(1, num_pages + 1):
                self.pages.append(f'{link[:-5]}{k}.{self.img_extensions[k-1]}')
            
            self.log(f'Successfully retrieved doujin {self.code}!')


def has_rating(code: int) -> bool:
    """Checks if code given already has a rating"""
    ratings = grab_ratings()
    if str(code) in ratings:
        return True
    return False


def grab_ratings() -> dict:
    """Grabs the hentai ratings from nhdbratings.json file"""
    with open('jsons/nhdbratings.json', 'r') as f:
        return json.load(f)


def write_ratings(ratings: dict) -> None:
    """Writes to the nhdbratings.json file"""
    with open('jsons/nhdbratings.json', 'w') as f:
        json.dump(ratings, f, indent=4)


class CachedNHentaiComic():
    """A class that handles a cached comic (from JSON to an accessible class)"""
    def __init__(self, cache_entry: dict) -> None:
        self.code = cache_entry["code"]
        self.title = cache_entry["title"]
        self.thumbnail = cache_entry["thumbnail"]
        self.favorites = cache_entry["favorites"]
        self.pages = cache_entry["pages"]
        self.tags = cache_entry["tags"]

    def __repr__(self):
        return f'<CacheNHentaiComic code={self.code} title={self.title} favorites={self.favorites}>'


def grab_nhcache():
    """Returns the items in the current nhcache"""
    with open('jsons/nhdb.json', 'r') as f:
        return json.load(f)  


def in_nhcache(key: int) -> bool:
    """Checks if a comic is inside the nhcache""" 
    with open('jsons/nhdb.json', 'r') as f:
        cache = json.load(f)
        
    if str(key) in cache:
        return True
    else:
        return False


def grab_comic(key: int) -> CachedNHentaiComic:
    """Grabs a comic from the nhcache"""
    with open('jsons/nhdb.json', 'r') as f:
        cache = json.load(f) 
        
    if in_nhcache(key):
        return CachedNHentaiComic(cache[str(key)])
    else:
        return KeyError("Comic not in cache")


def add_nhcache(comic: NHentaiComic) -> None:
    """Adds a new comic into the nhcache"""
    cache = grab_nhcache()
    
    # Check if comic is already in the cache
    if comic.code in cache:
        return
    
    cache[comic.code] = {"code": comic.code, 
                  "title": comic.title, 
                  "favorites": comic.favorites, 
                  "pages": comic.pages, 
                  "thumbnail": comic.thumbnail,
                  "tags": comic.tags
                  }
    with open('jsons/nhdb.json', 'w') as f:
        json.dump(cache, f, indent=4)
        
