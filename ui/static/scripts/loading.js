const SCROLL_THRESHOLD = 200;
const ARTIST_TBODY = document.getElementById('artist-table-body');


const LOADING_MESSAGE = document.getElementById('loading-message');
const EMPTY_MESSAGE = document.getElementById('empty-message');
const ARTIST_ROW_TEMPLATE = document.getElementById('artist-row-template');

import { queryParams } from './state.js';

let isLoading = false;
let hasMore = true;


function make_artist_row(artist) {
    const row = ARTIST_ROW_TEMPLATE.content.cloneNode(true);

    const artistCell = row.querySelector('.artist');
    const link = document.createElement('a');
    link.href = `https://music.yandex.ru/artist/${artist.id}`;
    link.target = '_blank';
    link.textContent = artist.name;
    artistCell.appendChild(link);

    row.querySelector('.tracks').textContent =
        artist.tracks_count.toLocaleString('ru-RU');

    row.querySelector('.likes').textContent =
        artist.likes_count.toLocaleString('ru-RU');

    row.querySelector('.listeners').textContent =
        artist.last_month_listeners.toLocaleString('ru-RU');

    let deltaCell = row.querySelector('.listeners-delta');
    const deltaValue = artist.last_month_listeners_delta;
    const isPositive = deltaValue > 0;
    const absValue = Math.abs(deltaValue);
    deltaCell.classList.add(isPositive ? 'rise' : 'fall');
    deltaCell.textContent = `${isPositive ? '+' : '−'}${absValue.toLocaleString('ru-RU')}`;



    row.querySelector('.rating-day').textContent =
        artist.ratings_day;

    row.querySelector('.rating-month').textContent =
        artist.ratings_month;

    row.querySelector('.rating-week').textContent =
        artist.ratings_week;

    row.querySelector('.genres').textContent =
        artist.genres.join(', ');

    row.querySelector('.countries').textContent =
        artist.countries.join(', ');

    return row;
}

async function loadMore() {
    if (isLoading || !hasMore) return;

    isLoading = true;
    LOADING_MESSAGE.style.display = 'block';
    EMPTY_MESSAGE.style.display = 'none';

    try {
        const response = await fetch('/api/artists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(queryParams)
        });

        const data = await response.json();

        if (queryParams.page === 1) {
            ARTIST_TBODY.innerHTML = '';
        }

        data.artists.forEach(artist => {
            let artist_row = make_artist_row(artist);

            console.log(artist_row);

            ARTIST_TBODY.appendChild(artist_row);
        });

        if (data.total === 0) {
            EMPTY_MESSAGE.style.display = 'block';
        }

        hasMore = data.has_next;
        queryParams.page = data.page + 1;

    } catch (error) {
        console.error('Ошибка загрузки:', error);
    } finally {
        isLoading = false;
        LOADING_MESSAGE.style.display = 'none';
    }
}

window.addEventListener('scroll', () => {
    const scrollTop = document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;

    if (scrollTop + clientHeight >= scrollHeight - SCROLL_THRESHOLD) {
        loadMore();
    }
});

loadMore();
