from flask import Blueprint, request, jsonify, render_template
from backend.nlp_engine import NeuroBrain
import requests
import re
import urllib.parse
import json
import os
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

api = Blueprint('api', __name__)

# --- BRAIN INITIALIZATION ---
print("--- STARTING NEUROSTREAM BACKEND ---")
brains = {
    'movies': NeuroBrain('movies'),
    'games': NeuroBrain('games')
    # Books removed
}
print("--- BACKEND READY ---")

# --- CONFIG ---
TMDB_API_KEY = "3204728227f7f1dc7a497f40e0ac2f29"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
CACHE_FILE = 'data/poster_cache.json'

# --- CACHE SYSTEM ---
poster_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r') as f:
            poster_cache = json.load(f)
        print(f"✅ Loaded {len(poster_cache)} posters from cache.")
    except:
        print("⚠️ Cache empty or corrupt.")

def save_cache():
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(poster_cache, f)
    except: pass

# --- NETWORK SETUP ---
session = requests.Session()
adapter = HTTPAdapter(max_retries=Retry(connect=3, read=3, backoff_factor=0.5))
session.mount('http://', adapter)
session.mount('https://', adapter)

@api.route('/')
def home():
    """
    Directly load the Main App interface.
    The Landing Page is removed; this is now the entry point.
    """
    return render_template('index.html')

# --- HELPER: Parallel Poster Fetcher ---
def process_movie_poster(movie):
    """Fetches poster AND corrects the ID if needed."""
    original_id = str(movie['id'])
    
    # 1. FAST PATH: Check Cache
    if original_id in poster_cache:
        cached_data = poster_cache[original_id]
        if isinstance(cached_data, str):
            movie['poster'] = cached_data
        else:
            movie['poster'] = cached_data.get('poster')
            movie['id'] = cached_data.get('tmdb_id', original_id)
        return movie

    # 2. SLOW PATH: Network Call
    poster_url = "https://via.placeholder.com/300x450?text=No+Poster"
    final_tmdb_id = original_id 
    
    try:
        url = f"{TMDB_BASE_URL}/movie/{original_id}?api_key={TMDB_API_KEY}"
        res = session.get(url, timeout=1.0)
        
        if res.status_code == 200:
            data = res.json()
            if data.get('poster_path'):
                poster_url = f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
        else:
            q = urllib.parse.quote(movie['title'])
            s_url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={q}"
            s_res = session.get(s_url, timeout=1.0).json()
            if s_res.get('results'):
                first = s_res['results'][0]
                final_tmdb_id = str(first['id'])
                if first.get('poster_path'):
                    poster_url = f"https://image.tmdb.org/t/p/w500{first['poster_path']}"
    except:
        pass

    movie['poster'] = poster_url
    movie['id'] = final_tmdb_id 

    poster_cache[original_id] = {
        'poster': poster_url,
        'tmdb_id': final_tmdb_id
    }
    
    return movie

# --- API ROUTES ---

@api.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        media_type = data.get('type', 'movies')
        mode = data.get('mode', 'search')
        query = data.get('query', '')
        # REMOVED: era = data.get('era', None)
        page = data.get('page', 1)
        
        brain = brains.get(media_type)
        if not brain: return jsonify({'error': 'Invalid media type'}), 400

        limit = 12
        offset = (page - 1) * limit
        results = []
        
        if mode == 'random':
            results = brain.get_random(top_k=limit)
        else:
            fetch_k = page * limit
            # REMOVED: filters={'era': era} from the search call below
            all_results = brain.search(query, top_k=fetch_k) 
            if len(all_results) > offset:
                results = all_results[offset : offset + limit]
        
        # Parallel Processing for Movies
        if media_type == 'movies' and results:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(process_movie_poster, results))
            save_cache()
        
        return jsonify(results)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/api/details/<media_type>/<item_id>')
def get_details(media_type, item_id):
    if media_type == 'movies':
        return get_movie_details(item_id)
    elif media_type == 'games':
        return get_game_details(item_id)
    
    return jsonify({'error': 'Invalid type'}), 400

def get_movie_details(movie_id):
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,watch/providers"
        data = session.get(url, timeout=3).json()
        
        cast = [a['name'] for a in data.get('credits', {}).get('cast', [])[:8]]
        director, writers, music = [], [], []
        
        if 'credits' in data:
            for person in data['credits'].get('crew', []):
                job = person.get('job', '')
                if job == 'Director': director.append(person['name'])
                elif job in ['Screenplay', 'Writer', 'Story']: writers.append(person['name'])
                elif job in ['Original Music Composer', 'Music']: music.append(person['name'])
        
        providers = []
        link = ""
        if 'watch/providers' in data:
            results = data['watch/providers'].get('results', {})
            region = results.get('US') or (list(results.values())[0] if results else {})
            link = region.get('link', '')
            if 'flatrate' in region:
                providers = [p['provider_name'] for p in region['flatrate']]

        backdrop = f"https://image.tmdb.org/t/p/w1280{data.get('backdrop_path')}" if data.get('backdrop_path') else None
        companies = [c['name'] for c in data.get('production_companies', [])[:3]]
        collection = data.get('belongs_to_collection', {}).get('name') if data.get('belongs_to_collection') else None
        
        return jsonify({
            'title': data.get('title'), 
            'tagline': data.get('tagline'),
            'overview': data.get('overview'),
            'vote_average': round(data.get('vote_average', 0), 1),
            'vote_count': data.get('vote_count'),
            'year': data.get('release_date', '')[:4], 
            'runtime': data.get('runtime'),
            'status': data.get('status'),
            'budget': data.get('budget', 0),
            'revenue': data.get('revenue', 0),
            'original_language': data.get('original_language', 'en').upper(),
            'genres': [g['name'] for g in data.get('genres', [])],
            'cast': cast, 
            'backdrop': backdrop,
            'director': director,
            'writers': list(set(writers)),
            'music': music,
            'companies': companies,
            'collection': collection,
            'providers': providers, 
            'link': link,
            'type': 'movie'
        })
    except Exception as e: return jsonify({'error': str(e)}), 500

def get_game_details(game_id):
    brain = brains['games']
    try:
        row = brain.df[brain.df['id'] == str(game_id)].iloc[0]
        genres = str(row.get('genres', '')).replace(';', ',').split(',')

        return jsonify({
            'title': row['title'], 
            'overview': row['overview'],
            'vote_average': row['vote_average'], 
            'year': int(row['year']),
            'developer': str(row.get('developer', 'Unknown')),
            'publisher': str(row.get('publisher', 'Unknown')),
            'genres': genres, 
            'poster': str(row.get('poster', '')),
            'type': 'game'
        })
    except: return jsonify({'error': 'Game not found'}), 404

@api.route('/api/trailer/<string:title>')
def get_trailer(title):
    media_type = request.args.get('type', 'movie')
    year = request.args.get('year', '')
    suffix = "gameplay trailer" if media_type == 'game' else "official trailer"
    search_query = f"{title} {year} {suffix}"
    try:
        query = urllib.parse.quote(search_query)
        url = f"https://www.youtube.com/results?search_query={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        video_ids = re.findall(r'"videoId":"(.{11})"', res.text)
        if video_ids: return jsonify({'key': video_ids[0]})
        return jsonify({'error': 'Not found'}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500