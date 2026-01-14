import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os

# --- GLOBAL SHARED MODEL ---
# We load this outside the class so it's only created ONCE in memory.
_shared_model = None

class NeuroBrain:
    def __init__(self, media_type='movies'):
        global _shared_model
        
        self.media_type = media_type
        self.data_path = f'data/{media_type}.csv'
        self.index_path = f'data/{media_type}_index.bin'
        self.model_name = 'all-MiniLM-L6-v2'
        self.df = pd.DataFrame()
        
        print(f"🧠 Initializing NeuroBrain for {self.media_type.upper()}...")
        
        # 1. Load Data
        if os.path.exists(self.data_path):
            try:
                self.df = pd.read_csv(self.data_path)
                
                # ID Cleanup
                if 'id' in self.df.columns: self.df['id'] = self.df['id'].astype(str)
                elif 'movie_id' in self.df.columns: self.df['id'] = self.df['movie_id'].astype(str)
                elif 'appid' in self.df.columns: self.df['id'] = self.df['appid'].astype(str)
                else: self.df['id'] = self.df.index.astype(str)

                # Year Cleanup
                if 'release_date' in self.df.columns:
                    self.df['release_date'] = pd.to_datetime(self.df['release_date'], errors='coerce')
                    self.df['year'] = self.df['release_date'].dt.year.fillna(0).astype(int)
                elif 'year' in self.df.columns:
                    self.df['year'] = self.df['year'].fillna(0).astype(int)
                else: self.df['year'] = 0

                # Ensure columns exist
                for col in ['vote_average', 'overview', 'title', 'tags']:
                    if col not in self.df.columns: self.df[col] = ""
                    
            except Exception as e:
                print(f"❌ Error reading CSV: {e}")
                return
        else:
            print(f"❌ Data file missing: {self.data_path}")
            return

        # 2. Load AI Model (SINGLETON PATTERN)
        # This checks if the model is already loaded. If yes, it reuses it.
        if _shared_model is None:
            print(f"   - Loading Neural Model into Memory (Once)...")
            _shared_model = SentenceTransformer(self.model_name)
        self.model = _shared_model

        # 3. Load Index
        if not self.df.empty:
            if os.path.exists(self.index_path):
                print(f"   - Loading Index from {self.index_path}...")
                self.index = faiss.read_index(self.index_path)
            else:
                print(f"   - ⚠️ No index found. Building new Vector Index...")
                self.build_index()

        print(f"✅ {self.media_type.upper()} Brain Online.")

    def build_index(self):
        if self.df.empty: return
        text_data = (self.df['title'].astype(str) + " " + self.df['tags'].astype(str)).tolist()
        embeddings = self.model.encode(text_data, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        faiss.write_index(self.index, self.index_path)
        print(f"   - Index saved.")

    def search(self, query, top_k=20, filters=None):
        if self.df.empty or not hasattr(self, 'index'): return []
        query_vector = self.model.encode([query]).astype('float32')
        fetch_k = min(top_k * 5, len(self.df))
        distances, indices = self.index.search(query_vector, fetch_k)
        
        results = []
        for idx in indices[0]:
            if idx == -1: continue
            item = self.df.iloc[idx]
            
            # REMOVED: Era/Time Travel filter logic was here
            # Logic for filtering by 'era' (80s, 90s, etc.) has been deleted.

            results.append(self._format_item(item))
            if len(results) >= top_k: break
        return results

    def get_random(self, top_k=10):
        if self.df.empty: return []
        n = min(top_k, len(self.df))
        samples = self.df.sample(n=n).to_dict(orient='records')
        return [self._format_item(item) for item in samples]

    def _format_item(self, item):
        obj = {
            'id': str(item.get('id', '')),
            'title': str(item.get('title', 'Unknown')),
            'year': int(item.get('year', 0)),
            'overview': str(item.get('overview', '')),
            'vote_average': float(item.get('vote_average', 0.0)),
            'type': self.media_type
        }
        if 'developer' in item: obj['developer'] = str(item['developer'])
        if 'publisher' in item: obj['publisher'] = str(item['publisher'])
        if 'poster' in item: obj['poster'] = str(item['poster'])
        if self.media_type == 'movies': obj['poster'] = "https://via.placeholder.com/300x450?text=No+Poster"
        return obj