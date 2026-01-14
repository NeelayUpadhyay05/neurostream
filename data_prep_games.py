import pandas as pd
import numpy as np
import os
import ast

# Ensure data directory exists
DATA_DIR = 'data'

print("Loading Steam datasets...")
try:
    # 1. Load the core datasets
    df_main = pd.read_csv(os.path.join(DATA_DIR, 'steam.csv'))
    df_desc = pd.read_csv(os.path.join(DATA_DIR, 'steam_description_data.csv'))
    df_media = pd.read_csv(os.path.join(DATA_DIR, 'steam_media_data.csv'))
    df_reqs = pd.read_csv(os.path.join(DATA_DIR, 'steam_requirements_data.csv'))
except FileNotFoundError as e:
    print(f"Error: Missing file. {e}")
    print("Please ensure steam.csv, steam_description_data.csv, steam_media_data.csv, and steam_requirements_data.csv are in the 'data/' folder.")
    exit()

print("Merging datasets...")
# Rename 'steam_appid' to 'appid' for easy merging
df_desc.rename(columns={'steam_appid': 'appid'}, inplace=True)
df_media.rename(columns={'steam_appid': 'appid'}, inplace=True)
df_reqs.rename(columns={'steam_appid': 'appid'}, inplace=True)

# Merge
df = df_main.merge(df_desc, on='appid', how='left')
df = df.merge(df_media, on='appid', how='left')
df = df.merge(df_reqs, on='appid', how='left')

print("Cleaning and Transforming...")

# 2. Standardize Column Names
df.rename(columns={
    'appid': 'id',
    'name': 'title',
    'short_description': 'overview',
    'header_image': 'poster',
}, inplace=True)

# 3. Process Dates
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
df['year'] = df['release_date'].dt.year.fillna(0).astype(int)

# 4. Calculate Vote Average & Count
df['total_votes'] = df['positive_ratings'] + df['negative_ratings']
df['vote_average'] = (df['positive_ratings'] / df['total_votes']) * 10
df['vote_average'] = df['vote_average'].fillna(0).round(1)
df.rename(columns={'total_votes': 'vote_count'}, inplace=True)

# --- NEW: POPULARITY FILTER ---
# This removes "Noise" (games with almost no players)
# Only keep games with at least 200 reviews
initial_count = len(df)
df = df[df['vote_count'] >= 200]
print(f"📉 Filtered dataset from {initial_count} -> {len(df)} High-Quality Games.")

# 5. Create "Tags" for the AI
def clean_tags(text):
    if pd.isna(text): return ""
    return text.replace(';', ' ')

df['genres_str'] = df['genres'].apply(clean_tags)
df['categories_str'] = df['categories'].apply(clean_tags)
df['tags_str'] = df['steamspy_tags'].apply(clean_tags)
df['developer'] = df['developer'].fillna('')

# Master Tag Field
df['tags'] = (
    df['overview'].fillna('') + " " + 
    df['genres_str'] + " " + 
    df['categories_str'] + " " + 
    df['tags_str'] + " " + 
    df['developer']
).str.lower()

# 6. Requirements
df['pc_requirements'] = df['minimum'].fillna("")

# 7. Select Final Columns
final_df = df[[
    'id', 
    'title', 
    'overview', 
    'tags',            
    'poster',          
    'year',            
    'vote_average',    
    'vote_count',
    'developer',       
    'publisher',
    'genres',          
    'pc_requirements'  
]]

# Remove bad data
final_df = final_df.dropna(subset=['title', 'overview'])

# Save
output_path = os.path.join(DATA_DIR, 'games.csv')
final_df.to_csv(output_path, index=False)

print(f"Success! Saved clean dataset to: {output_path}")