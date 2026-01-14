let currentMediaType = 'movies';
let currentView = 'grid'; 
let movies = [];
let players = {}; 
let observer = null;
let currentModalMovie = null;

// --- REQUEST TRACKING (Prevents Ghost Data) ---
let activeRequestId = 0; 

// --- TAB MEMORY (Saves state per tab) ---
const contextState = {
    movies: { data: [], page: 1, hasMore: true, query: '' },
    games:  { data: [], page: 1, hasMore: true, query: '' }
};

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    currentMediaType = params.get('type') || 'movies';
    setupUI();
    
    // FIX: Show Empty State immediately. Do NOT trigger random.
    renderEmptyState();
});

// --- UI & STATE ---
function switchContext(type) {
    if (currentMediaType === type) return; 
    
    // 1. INVALIDATE OLD REQUESTS
    activeRequestId++;
    isFetching = false;

    // 2. SAVE Current Tab State
    contextState[currentMediaType] = {
        data: movies,
        page: currentPage,
        hasMore: hasMore,
        query: document.getElementById('moodInput').value
    };

    // 3. SWITCH Context
    currentMediaType = type;
    setupUI();

    // 4. RESTORE New Tab State
    const saved = contextState[currentMediaType];
    movies = saved.data;
    currentPage = saved.page;
    hasMore = saved.hasMore;
    document.getElementById('moodInput').value = saved.query;

    // 5. RENDER
    // Clear views first
    document.getElementById('gridView').innerHTML = '';
    document.getElementById('reelView').innerHTML = '';

    if (movies.length > 0) {
        renderApp(movies, false);
    } else {
        // FIX: If no saved data, show empty state (No Auto-Search)
        renderEmptyState();
    }
}

function setupUI() {
    const title = document.getElementById('heroTitle');
    const tags = document.getElementById('quickTags');
    const input = document.getElementById('moodInput');
    const logo = document.getElementById('logoSuffix');
    
    document.body.setAttribute('data-context', currentMediaType);
    
    document.getElementById('ctxMovies').classList.toggle('active', currentMediaType === 'movies');
    document.getElementById('ctxGames').classList.toggle('active', currentMediaType === 'games');

    if (currentMediaType === 'games') {
        if(logo) logo.style.color = "#00ffcc";
        title.innerText = "What are we playing today?";
        input.placeholder = "E.g., 'Open world RPG with story'...";
        
        // ADDED: Surprise Me button at the end
        tags.innerHTML = `
            <span>Try:</span>
            <button onclick="quickSearch('Relaxing puzzle')">Puzzle</button>
            <button onclick="quickSearch('Fast paced FPS')">Shooters</button>
            <button onclick="quickSearch('Story driven RPG')">RPG</button>
            <button class="surprise-btn" onclick="triggerRandom()"> Surprise Me</button>
        `;
        document.documentElement.style.setProperty('--accent', '#00ffcc');
    } else {
        if(logo) logo.style.color = "#e50914";
        title.innerText = "Find your next obsession.";
        input.placeholder = "Describe the vibe (e.g. 'Dark sci-fi')...";
        
        // ADDED: Surprise Me button at the end
        tags.innerHTML = `
            <span>Try:</span>
            <button onclick="quickSearch('Dark psychological thriller')">Dark Thriller</button>
            <button onclick="quickSearch('Feel good 80s comedy')">80s Comedy</button>
            <button onclick="quickSearch('Cyberpunk action')">Cyberpunk</button>
            <button class="surprise-btn" onclick="triggerRandom()"> Surprise Me</button>
        `;
        document.documentElement.style.setProperty('--accent', '#e50914');
    }
}

// --- SEARCH ---
function handleEnter(e) { if(e.key === 'Enter') triggerSearch(); }
function quickSearch(q) { document.getElementById('moodInput').value = q; triggerSearch(); }
// Optional: Kept function if needed, but not called automatically
function triggerRandom() { document.getElementById('moodInput').value = ""; triggerSearch('random'); }

function triggerSearch(modeOverride) {
    const query = document.getElementById('moodInput').value;
    const mode = modeOverride || 'search';
    
    // STRICT FIX: Don't search if empty and not random mode
    if(mode === 'search' && !query) return;
    
    // Reset State
    currentPage = 1; 
    movies = []; 
    hasMore = true;
    isFetching = false;
    activeRequestId++; // Invalidate previous searches

    document.getElementById('gridView').innerHTML = ''; 
    document.getElementById('reelView').innerHTML = '';
    
    fetchMovies({ type: currentMediaType, mode: mode, query: query, page: 1 });
}

// --- FETCHING ---
let currentPage = 1; let isFetching = false; let hasMore = true;

function fetchMovies(payload) {
    if (isFetching || !hasMore) return;
    
    isFetching = true; 
    
    // Only show loader for the FIRST page
    if (currentPage === 1) {
        document.getElementById('loader').style.display = 'block';
    }
    
    payload.page = currentPage;
    const thisRequestId = activeRequestId; // Capture ID

    fetch('/api/recommend', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(payload) 
    })
    .then(res => res.json())
    .then(data => {
        // Discard if ID mismatch
        if (thisRequestId !== activeRequestId) return;

        isFetching = false; 
        document.getElementById('loader').style.display = 'none';
        
        if (!data || data.length === 0) { 
            hasMore = false; 
            if (currentPage === 1) renderEmptyState(); 
            return; 
        }

        movies = movies.concat(data); 
        renderApp(data, currentPage > 1);
    })
    .catch(err => { 
        if (thisRequestId === activeRequestId) {
            isFetching = false; 
            console.error(err); 
            document.getElementById('loader').innerText = "Error connecting to Brain."; 
        }
    });
}

function renderEmptyState() { 
    const msg = currentMediaType === 'movies' ? "Enter a mood above to start streaming." : "Enter a game vibe to start.";
    document.getElementById('gridView').innerHTML = `<div class="empty-state" style="grid-column: 1/-1; text-align: center; margin-top: 50px; color: #666; font-size: 18px;">${msg}</div>`; 
}

// --- INFINITE SCROLL ---
window.addEventListener('scroll', () => {
    if (currentView === 'grid') {
        const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
        if (scrollTop + clientHeight >= scrollHeight - 1000) loadMore();
    }
});

function loadMore() {
    // FIX: Don't auto-load if we haven't started a search yet
    if (movies.length === 0) return;
    
    if (isFetching || !hasMore) return;
    currentPage++;
    const query = document.getElementById('moodInput').value;
    // If input empty but movies exist, assume random mode
    const mode = query ? 'search' : 'random';
    
    fetchMovies({ type: currentMediaType, mode: mode, query: query, page: currentPage });
}

// --- VIEW SWITCHING ---
function switchView(view) {
    currentView = view;
    document.getElementById('btnGrid').classList.toggle('active', view === 'grid');
    document.getElementById('btnReel').classList.toggle('active', view === 'reel');
    
    if(view === 'grid') {
        document.getElementById('gridView').style.display = 'grid';
        document.getElementById('reelView').style.display = 'none';
        stopAllVideos();
        // Restore grid if needed
        if (document.getElementById('gridView').children.length === 0 && movies.length > 0) {
            renderGrid(movies, false);
        }
    } else {
        document.getElementById('gridView').style.display = 'none';
        document.getElementById('reelView').style.display = 'block';
        
        const rc = document.getElementById('reelView');
        rc.onscroll = () => { 
            if (rc.scrollTop + rc.clientHeight >= rc.scrollHeight - 1000) loadMore(); 
        };
        
        if (document.getElementById('reelView').children.length === 0 && movies.length > 0) {
            renderReels(movies, false);
        }
    }
}

function renderApp(batch, isAppend) {
    if(currentView === 'grid') renderGrid(batch, isAppend);
    else renderReels(batch, isAppend);
}

// --- RENDER GRID ---
function renderGrid(batch, isAppend) {
    const grid = document.getElementById('gridView');
    if (!isAppend) grid.innerHTML = '';
    
    batch.forEach((item, index) => {
        const card = document.createElement('div'); 
        card.className = 'poster-card';
        // Animation
        card.style.animation = `fadeInUp 0.5s ease forwards ${index * 0.05}s`;
        card.style.opacity = '0';
        
        let imgHTML = '';
        if (item.poster && !item.poster.includes("placeholder")) {
            imgHTML = `<img src="${item.poster}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`;
        }
        
        const grad = getRandomGradient();
        const yearDisplay = (item.year && item.year > 0) ? item.year : "";

        card.innerHTML = `
            ${imgHTML}
            <div class="poster-placeholder" style="${imgHTML ? 'display:none;' : ''} background:${grad}">
                ${item.title}
            </div>
            <div class="poster-info"><h3>${item.title}</h3><span>${yearDisplay}</span></div>
        `;
        
        card.onclick = function() { openModal(item); };
        grid.appendChild(card);
    });
}

// --- RENDER REELS ---
function renderReels(batch, isAppend) {
    const container = document.getElementById('reelView');
    if (!isAppend) { container.innerHTML = ''; players = {}; }
    
    const start = isAppend ? movies.length - batch.length : 0;

    batch.forEach((item, i) => {
        const index = start + i;
        const div = document.createElement('div');
        div.className = 'reel-item'; div.id = `reel-${index}`;
        div.dataset.title = item.title; 
        div.dataset.year = item.year;
        
        div.innerHTML = `
            <div id="yt-player-${index}" class="video-layer"></div>
            <div class="reel-overlay">
                <h2>${item.title}</h2>
                <p>${item.overview}</p>
            </div>
        `;
        container.appendChild(div);
    });
    initObserver();
}

// --- MODAL ---
function openModal(item) {
    currentModalMovie = item;
    const modal = document.getElementById('movieModal');
    if(!modal) return;

    // LOCK SCROLL
    document.body.style.overflow = 'hidden';

    document.getElementById('modalTitle').innerText = item.title;
    document.getElementById('modalYear').innerText = (item.year && item.year > 0) ? item.year : "N/A";
    document.getElementById('modalDesc').innerText = item.overview;
    document.getElementById('modalRating').innerText = `★ ...`;
    
    // Clear dynamic fields
    ['modalGenres','valCredit1','valCredit2','modalProviders'].forEach(id => {
        const el = document.getElementById(id); if(el) el.innerHTML = "";
    });
    ['valStat1','valStat2','valStat3','valStat4','modalTagline','modalRuntime','modalStatus'].forEach(id => {
        const el = document.getElementById(id); if(el) el.innerText = "--";
    });
    
    document.getElementById('modalCollectionBox').style.display = 'none';
    document.getElementById('modalLink').style.display = 'none';
    document.getElementById('modalRuntime').style.display = 'none';

    // Hero
    const hero = document.getElementById('modalHero');
    hero.style.backgroundImage = 'none';
    hero.style.backgroundColor = '#1a1a1a';
    if(currentMediaType === 'games' && item.poster && !item.poster.includes("placeholder")) {
        hero.style.backgroundImage = `url('${item.poster}')`;
    }

    modal.style.display = 'flex';

    // Fetch Details
    const fetchId = item.id || item.tmdb_id; 
    
    fetch(`/api/details/${currentMediaType}/${fetchId}`)
    .then(res => res.json())
    .then(data => {
        if(data.error) return; 
        
        if(data.overview) document.getElementById('modalDesc').innerText = data.overview;
        if(data.year > 0) document.getElementById('modalYear').innerText = data.year;
        document.getElementById('modalRating').innerText = `★ ${data.vote_average}`;

        const gl = document.getElementById('modalGenres');
        (data.genres || []).forEach(g => {
            const s = document.createElement('span'); s.className = 'genre-tag'; s.innerText = g; gl.appendChild(s);
        });

        if (currentMediaType === 'movies') {
            // MOVIE MODE
            if(data.backdrop) hero.style.backgroundImage = `url('${data.backdrop}')`;
            if(data.tagline) document.getElementById('modalTagline').innerText = `"${data.tagline}"`;
            if(data.runtime) {
                document.getElementById('modalRuntime').style.display = 'inline';
                document.getElementById('modalRuntime').innerText = `${Math.floor(data.runtime/60)}h ${data.runtime%60}m`;
            }
            document.getElementById('modalStatus').innerText = data.status || "Released";
            
            document.getElementById('lblStat1').innerText = "Budget"; document.getElementById('valStat1').innerText = formatMoney(data.budget);
            document.getElementById('lblStat2').innerText = "Revenue"; document.getElementById('valStat2').innerText = formatMoney(data.revenue);
            document.getElementById('lblStat3').innerText = "Language"; document.getElementById('valStat3').innerText = data.original_language;
            document.getElementById('lblStat4').innerText = "Production"; document.getElementById('valStat4').innerText = data.companies?.[0] || '-';
            
            document.getElementById('crewSection').style.display = 'flex';
            document.getElementById('castSection').style.display = 'block';
            document.getElementById('lblCredit1').innerText = "Director"; fillPills('valCredit1', data.director || []);
            document.getElementById('lblCredit2').innerText = "Music"; fillPills('valCredit2', data.music || []);
            document.getElementById('modalCast').innerText = data.cast && data.cast.length > 0 ? data.cast.join(", ") : "Unavailable";
            
            if(data.collection) {
                document.getElementById('modalCollectionBox').style.display = 'flex';
                document.getElementById('modalCollectionName').innerText = data.collection;
            }
            if(data.providers) {
                document.getElementById('providersSection').style.display = 'block';
                const pl = document.getElementById('modalProviders');
                data.providers.forEach(p => { const l=document.createElement('li'); l.innerText=p; pl.appendChild(l); });
            }

        } else {
            // GAME MODE
            document.getElementById('lblStat1').innerText = "Developer"; document.getElementById('valStat1').innerText = data.developer || "Unknown";
            document.getElementById('lblStat2').innerText = "Publisher"; document.getElementById('valStat2').innerText = data.publisher || "Unknown";
            document.getElementById('lblStat3').innerText = "Rating"; document.getElementById('valStat3').innerText = data.vote_average;
            document.getElementById('lblStat4').innerText = ""; document.getElementById('valStat4').innerText = "";
            
            document.getElementById('crewSection').style.display = 'none';
            document.getElementById('castSection').style.display = 'none';
            document.getElementById('providersSection').style.display = 'none';
            document.getElementById('modalCollectionBox').style.display = 'none';
            document.getElementById('modalStatus').style.display = 'none'; 
        }

        if(data.link) {
            const btn = document.getElementById('modalLink');
            btn.href = data.link; btn.style.display = 'block';
        }
    });
}

function closeModal() { 
    document.getElementById('movieModal').style.display = 'none';
    // UNLOCK SCROLL
    document.body.style.overflow = '';
}
window.onclick = (e) => { if(e.target == document.getElementById('movieModal')) closeModal(); }

// --- UTILS ---
function fillPills(id, list) {
    const c = document.getElementById(id);
    if(!c) return;
    list.forEach(n => { const s=document.createElement('span'); s.className='crew-pill'; s.innerText=n; c.appendChild(s); });
}
function getRandomGradient() {
    const c = [['#4158D0', '#C850C0'], ['#0093E9', '#80D0C7'], ['#e50914', '#222']];
    const r = c[Math.floor(Math.random() * c.length)];
    return `linear-gradient(135deg, ${r[0]}, ${r[1]})`;
}
const formatMoney = (n) => n > 0 ? `$${(n/1000000).toFixed(1)}M` : 'N/A';

// --- VIDEO OBSERVER ---
function initObserver() {
    const options = { threshold: 0.6 };
    if (observer) observer.disconnect();
    const loadingStates = {}; 
    observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const index = entry.target.id.split('-')[1];
            const title = entry.target.dataset.title;
            const year = entry.target.dataset.year;
            
            if(entry.isIntersecting) {
                entry.target.classList.add('currently-viewing');
                if(!players[index] && !loadingStates[index]) {
                    loadingStates[index] = true;
                    loadTrailer(title, year, index, loadingStates);
                } else if (players[index]) {
                    players[index].playVideo();
                }
            } else {
                entry.target.classList.remove('currently-viewing');
                if(players[index]) players[index].pauseVideo();
            }
        });
    }, options);
    document.querySelectorAll('.reel-item').forEach(el => observer.observe(el));
}

function loadTrailer(title, year, index, loadingStates) {
    const cleanTitle = title.replace(/[^\w\s]/gi, '');
    fetch(`/api/trailer/${encodeURIComponent(cleanTitle)}?year=${year}&type=${currentMediaType}`)
    .then(res => res.json())
    .then(data => {
        if(data.key) {
            players[index] = new YT.Player(`yt-player-${index}`, {
                height: '100%', width: '100%',
                videoId: data.key,
                playerVars: { 'autoplay': 0, 'controls': 0, 'mute': 0, 'loop': 1, 'playlist': data.key },
                events: { 
                    'onReady': (e) => {
                        const el = document.getElementById(`reel-${index}`);
                        if(el && el.classList.contains('currently-viewing')) e.target.playVideo();
                    } 
                }
            });
        }
    }).finally(() => {
        if(loadingStates) delete loadingStates[index];
    });
}

function searchTrailerFromModal() {
    if(!currentModalMovie) return;
    const q = `${currentModalMovie.title} ${currentModalMovie.year} ${currentMediaType} trailer`;
    window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`, '_blank');
}

function stopAllVideos() { Object.values(players).forEach(p => { if(p.pauseVideo) p.pauseVideo(); }); }

if (!window.YT) {
    var tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
}