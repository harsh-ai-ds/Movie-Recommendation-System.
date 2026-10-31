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

async function getMovieRecommendations() {
    const movieName = document.getElementById('movieSelect').value;
    fetchData('/recommend_movie', { movie_name: movieName });
}

async function getMoodRecommendations() {
    const queryText = document.getElementById('moodInput').value;
    if (!queryText.trim()) {
        alert("Please describe your mood or search terms first!");
        return;
    }
    fetchData('/recommend_mood', { query: queryText });
}

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
        alert("Server connection failed. Make sure Flask is running.");
    }
}

function renderCards(movies) {
    const resultsGrid = document.getElementById('resultsGrid');
    resultsGrid.innerHTML = '';

    movies.forEach((movie, index) => {
        const card = document.createElement('div');
        card.className = 'card';

        let scoreBadge = movie.score ? `<span class="badge">Match: ${movie.score}%</span>` : '';

        // Added style="display: none;" directly here to force it hidden by default
        let trailerHtml = movie.trailer
            ? `<div class="trailer-container" style="display: none; margin-top: 10px;">
                   <iframe src="${movie.trailer}" style="width: 100%; height: 180px; border: none; border-radius: 6px;" allowfullscreen></iframe>
               </div>
               <div class="trailer-hint" style="font-size: 0.75rem; color: #94a3b8; text-align: center; margin-top: 5px; cursor: pointer;">🎬 Click poster to play trailer</div>`
            : `<div style="font-size: 0.8rem; color: #64748b; margin-top: 10px;">Trailer unavailable</div>`;

        card.innerHTML = `
            <img src="${movie.poster}" alt="${movie.title}" class="poster-img" style="width: 100%; height: 320px; object-fit: cover; cursor: pointer;">
            <div class="card-body" style="padding: 15px; display: flex; flex-direction: column; flex-grow: 1;">
                ${scoreBadge}
                <div class="card-title" style="font-size: 1.1rem; margin-bottom: 8px; font-weight: 600;">${index + 1}. ${movie.title}</div>
                ${trailerHtml}
            </div>
        `;

        // Add click event to the poster image to toggle trailer visibility
        const posterImg = card.querySelector('.poster-img');
        const trailerContainer = card.querySelector('.trailer-container');

        if (posterImg && trailerContainer) {
            posterImg.addEventListener('click', () => {
                // Toggle display between none and block
                if (trailerContainer.style.display === 'none') {
                    trailerContainer.style.display = 'block';
                } else {
                    trailerContainer.style.display = 'none';
                }
            });
        }

        resultsGrid.appendChild(card);
    });
}