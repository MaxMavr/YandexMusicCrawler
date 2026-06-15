const SCROLL_THRESHOLD = 200;
const ARTIST_TBODY = document.getElementById('artist-table-body');


let LOADING_MESSAGE = document.getElementById('loading-message');
let EMPTY_MESSAGE = document.getElementById('empty-message');

import { queryParams } from './state.js';

let isLoading = false;
let hasMore = true;

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
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${artist.id}</td>
                <td>${artist.name}</td>
                <td>${artist.is_available ? 'Доступен' : 'Недоступен'}</td>
                <td>${artist.likes_count.toLocaleString('ru-RU')}</td>
            `;

            ARTIST_TBODY.appendChild(row);
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
