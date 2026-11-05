// --- TAB SWITCHING LOGIC ---
function switchTab(mode) {
    document.getElementById('classicSection').classList.remove('active');
    document.getElementById('moodSection').classList.remove('active');
    document.getElementById('tabClassicBtn').classList.remove('active');
    document.getElementById('tabMoodBtn').classList.remove('active');

    if (mode === 'classic') {
        document.getElementById('classicSection').classList.add('active');
        document.getElementById('tabClassicBtn').classList.add('active');
    } else {
        document.getElementById('moodSection').classList.add('active');
        document.getElementById('tabMoodBtn').classList.add('active');
    }
}

// --- RECOMMENDATION API CALLS ---
async function getMovieRecommendations() {
    const movieName = document.getElementById('movieSelect').value;
    if (!movieName.trim()) {
        alert("Please select or type a movie name first!");
        return;
    }
    fetchData('/recommend_movie', { movie_name: movieName });
}

async function getMoodRecommendations() {
    const queryText = document.getElementById('moodInput').value;
    if (!queryText.trim()) {
        alert("Please describe your mood or story preference first!");
        return;
    }
    fetchData('/recommend_mood', { query: queryText });
}

// --- FETCH HELPER ---
async function fetchData(url, payload) {
    const loading = document.getElementById('loading');
    const resultsGrid = document.getElementById('resultsGrid');

    resultsGrid.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        loading.classList.add('hidden');

        if (data.status === 'success') {
            renderCards(data.recommendations);
        } else {
            alert(data.message || 'Error getting recommendations.');
        }
    } catch (err) {
        loading.classList.add('hidden');
        alert("Server connection failed. Please ensure Flask server is running.");
    }
}

// --- CLICK TO RECOMMEND SPECIFIC MOVIE ---
function selectMovie(title) {
    // Switch to Classic mode if in AI mode
    switchTab('classic');

    // Set search box value and fetch recommendations
    document.getElementById('movieSelect').value = title;
    getMovieRecommendations();

    // Smooth scroll down to view results
    window.scrollTo({ top: 350, behavior: 'smooth' });
}

// --- RENDER MOVIE CARDS GRID ---
function renderCards(movies) {
    const resultsGrid = document.getElementById('resultsGrid');
    resultsGrid.innerHTML = '';

    movies.forEach((movie, index) => {
        const card = document.createElement('div');
        card.className = 'card';

        let scoreBadge = movie.score ? `<span class="badge" style="background-color: #e50914; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; width: fit-content; margin-bottom: 6px;">Match: ${movie.score}%</span>` : '';

        let watchHintHtml = movie.trailer
            ? `<div class="watch-hint" style="font-size: 0.8rem; color: #e50914; text-align: center; margin-top: auto; padding-top: 10px; cursor: pointer; font-weight: 600;">🎬 Click poster to watch full movie</div>`
            : `<div style="font-size: 0.8rem; color: #64748b; margin-top: auto; padding-top: 10px; text-align: center;">Stream unavailable</div>`;

        card.innerHTML = `
            <img src="${movie.poster}" alt="${movie.title}" class="poster-img" style="width: 100%; height: 320px; object-fit: cover; border-radius: 6px 6px 0 0; cursor: pointer;" title="Click poster to watch full movie">
            <div class="card-body" style="padding: 15px; background-color: #1f1f1f; border-radius: 0 0 6px 6px; display: flex; flex-direction: column; flex-grow: 1;">
                ${scoreBadge}
                <div class="card-title" style="font-size: 1.05rem; margin-bottom: 8px; font-weight: 700; color: #ffffff; cursor: pointer; transition: color 0.2s;" title="Click title to search recommendations for this movie">${index + 1}. ${movie.title}</div>
                ${watchHintHtml}
            </div>
        `;

        // Interactive Event Listeners
        const posterImg = card.querySelector('.poster-img');
        const hintText = card.querySelector('.watch-hint');
        const titleText = card.querySelector('.card-title');

        // 1. Poster / Hint Click -> Opens full movie stream in new tab safely
        if (movie.trailer) {
            const openStream = () => {
                window.open(movie.trailer, '_blank');
            };
            posterImg.addEventListener('click', openStream);
            if (hintText) hintText.addEventListener('click', openStream);
        }

        // 2. Title Click -> Recommends that specific movie & related titles
        titleText.addEventListener('click', () => {
            selectMovie(movie.title);
        });

        // Hover style for title
        titleText.addEventListener('mouseenter', () => { titleText.style.color = '#e50914'; });
        titleText.addEventListener('mouseleave', () => { titleText.style.color = '#ffffff'; });

        resultsGrid.appendChild(card);
    });
}