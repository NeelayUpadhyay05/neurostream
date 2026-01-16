# NeuroStream: Semantic Movies & Games Recommender

Discover movies and games by *vibe*, not just keywords. 

NeuroStream is a content-based recommendation system that uses transformer embeddings and FAISS similarity search to find titles that **feel** like your query.

**Live Demo:** https://neelayupadhyay-neurostream-live.hf.space/

---

## What This Project Does

- Recommends **movies** and **PC games** based on natural-language queries  
  - e.g., *"emotional sci‑fi space drama"* or *"open world RPG with rich story"*
- Uses **Sentence Transformers** (`all-MiniLM-L6-v2`) to encode titles, tags, and descriptions into dense embeddings
- Uses **FAISS** for fast similarity search over thousands of items
- Provides a clean Flask API + web UI for interactive exploration

---

## Under the Hood

| Layer          | Tech / Idea                                  |
|----------------|----------------------------------------------|
| Embeddings     | `sentence-transformers` (MiniLM)             |
| Similarity     | FAISS `IndexFlatL2` over content embeddings  |
| Data Sources   | TMDB 5000 Movie Dataset, Steam Store Games   |
| Frontend       | HTML/CSS/JS (single-page app)                |
| Backend        | Flask API (`/api/recommend`, `/api/details`) |

- **Movies pipeline:** TMDB metadata → cleaned text tags → transformer embeddings → FAISS index → top‑k similar movies.
- **Games pipeline:** Steam games (Nik Davis dataset) → genres/categories/tags/description → embeddings → FAISS index → top‑k similar games.

---

## 📂 Project Directory Structure

```text
├── .gitignore
├── Dockerfile
├── NeuroStream.ipynb                   # Main Jupyter Notebook
├── README.md                           # Project Documentation
├── backend/
│   ├── __init__.py
│   ├── nlp_engine.py                   # Core AI/NLP Logic ("The Brain")
│   └── routes.py                       # API Logic
├── data/
│   ├── games.csv                       # Steam Games Dataset
│   ├── movies.csv                      # TMDB Movies Dataset
│   ├── poster_cache.json               # Cached Movie Posters
│   ├── games_index.bin                 # FAISS similarity index for games embeddings
│   ├── movies_index.bin                # FAISS similarity index for movie embeddings
│   ├── steam.csv                       # Raw Steam games metadata
│   ├── tmdb_5000_movies.csv            # Raw TMDB 5000 movies metadata
│   ├── tmdb_5000_credits.csv           # TMDB cast/crew data used for movies
│   ├── steam_description_data.csv      # Extra text descriptions for Steam apps
│   ├── steam_media_data.csv            # Media and image metadata for Steam apps
│   └── steam_requirements_data.csv     # System requirements metadata for Steam apps
├── data_prep_movies.py                 # Script to clean, merge, and feature‑engineer the movies dataset
├── data_prep_games.py                  # Script to clean, merge, and feature‑engineer the games dataset
├── requirements.txt                    # Python Dependencies
├── run.py                              # Application Entry Point
├── static/
│   ├── css/
│   │   └── style.css                   # Frontend Styling
│   └── js/
│       └── main.js                     # Frontend Logic
└── templates/
    └── index.html                      # Main Web Interface

```
---

## Getting Started (Local)

1. **Clone \& install**
```bash
git clone https://github.com/your-username/neurostream.git
cd neurostream
pip install -r requirements.txt
```

2. **Prepare data**

Place the Kaggle datasets in `data/` and run the preprocessing notebook:

```bash
jupyter notebook notebook/neurostream.ipynb
```

This will generate `movies.csv`, `games.csv`, and the FAISS indexes.

3. **Run the app**
```bash
python run.py
```

Then open `http://localhost:7860` in your browser.

---

## Datasets \& Limitations

- **Movies:** [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata)
- **Games:** [Steam Store Games (Clean dataset)](https://www.kaggle.com/datasets/nikdavis/steam-store-games)

Limitations:

- Datasets are **historical** (mostly pre‑2019), so very recent releases are not covered.
- Game coverage is **Steam‑only**; titles exclusive to consoles or other stores are missing.
- Recommendations are purely **content‑based** (no user history), so they capture semantic similarity but not personal taste.

---

## Responsible Use

This project is intended for educational and entertainment purposes:

- Recommendations may reflect popularity and representation biases present in TMDB and Steam.
- It should *not* be used for any high‑stakes or sensitive decision-making.
- Any real deployment should clearly communicate dataset coverage and limitations to users.

---

## About This Project

This project was built using a mix of **AI assistance** and **human supervision**:

- Core ideas, dataset choices, and integration were designed, tested, and validated by **Neelay Upadhyay**.
- Large parts of the boilerplate code, refactoring, and documentation were generated with the help of AI coding tools and language models, then reviewed and adjusted manually.

If you explore or extend this repo, consider it a starting point for building richer, more personalized recommender systems on top of modern embedding-based search.
