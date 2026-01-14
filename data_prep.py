import pandas as pd
import ast
import nltk
from nltk.stem.porter import PorterStemmer
import os

# Ensure data directory exists
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Download nltk resources if not present (handles first-time run)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def clean_json(obj):
    """Extract 'name' from JSON list strings."""
    try:
        L = []
        for i in ast.literal_eval(obj):
            L.append(i['name'])
        return L
    except:
        return []

def clean_json_top3(obj):
    """Extract top 3 names from JSON list strings."""
    try:
        L = []
        counter = 0
        for i in ast.literal_eval(obj):
            if counter != 3:
                L.append(i['name'])
                counter += 1
            else:
                break
        return L
    except:
        return []

def fetch_director(obj):
    """Extract Director name from crew."""
    L = []
    try:
        for i in ast.literal_eval(obj):
            if i['job'] == 'Director':
                L.append(i['name'])
                break
        return L
    except:
        return []

def collapse(L):
    """Remove spaces: 'Sam Worthington' -> 'SamWorthington'"""
    L1 = []
    for i in L:
        L1.append(i.replace(" ",""))
    return L1

print("Loading raw datasets from 'data/' folder...")
try:
    movies = pd.read_csv(os.path.join(DATA_DIR, 'tmdb_5000_movies.csv'))
    credits = pd.read_csv(os.path.join(DATA_DIR, 'tmdb_5000_credits.csv'))
except FileNotFoundError:
    print("Error: Raw CSV files not found in 'data/' folder. Please download them from Kaggle.")
    exit()

# 1. Merge Datasets
print("Merging datasets...")
movies = movies.merge(credits, on='title')

# 2. Select Relevant Columns
# We keep metadata (release_date, vote_average) for your Filter & Sorting features
print("Selecting columns...")
movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'release_date', 'vote_average', 'vote_count']]

# 3. Handle Missing Data
movies.dropna(inplace=True)

# 4. Apply Transformations (Extracting real data from JSON strings)
print("Transforming JSON fields...")
movies['genres'] = movies['genres'].apply(clean_json)
movies['keywords'] = movies['keywords'].apply(clean_json)
movies['cast'] = movies['cast'].apply(clean_json_top3)
movies['crew'] = movies['crew'].apply(fetch_director)

# 5. Process Overview
movies['overview'] = movies['overview'].apply(lambda x: x.split())

# 6. Collapse Spaces (Creating dense tags)
# This turns "Science Fiction" into "ScienceFiction" so it's treated as one distinct tag
movies['genres'] = movies['genres'].apply(collapse)
movies['keywords'] = movies['keywords'].apply(collapse)
movies['cast'] = movies['cast'].apply(collapse)
movies['crew'] = movies['crew'].apply(collapse)

# 7. Create the Master 'tags' Column
print("Creating master tags...")
movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']

# 8. Create Final DataFrame
# We keep the raw metadata separate from the tags for UI display
new_df = movies[['movie_id', 'title', 'tags', 'release_date', 'vote_average', 'vote_count']]

# 9. Clean Tags (Join list to string & lowercase)
new_df.loc[:, 'tags'] = new_df['tags'].apply(lambda x: " ".join(x))
new_df.loc[:, 'tags'] = new_df['tags'].apply(lambda x: x.lower())

# 10. Apply Stemming
# 'loved', 'loving', 'love' -> all become 'love'
print("Applying Porter Stemmer (this might take a moment)...")
ps = PorterStemmer()
def stem(text):
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)

new_df.loc[:, 'tags'] = new_df['tags'].apply(stem)

# 11. Rename ID for consistency
new_df.rename(columns={'movie_id': 'id'}, inplace=True)

# 12. Save
output_path = os.path.join(DATA_DIR, 'movies.csv')
new_df.to_csv(output_path, index=False)
print(f"Success! Processed data saved to '{output_path}'.")