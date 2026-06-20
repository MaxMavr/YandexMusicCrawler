const ARTIST_ROW_TEMPLATE = document.getElementById('artist-row-template');
import { makeGenresTag, makeCountryTag } from './tags.js';
import { initInfoLabelButtons } from './info.js';
const CASCADE_DELAY = 0.05;


const formatNumber = value => value.toLocaleString('ru-RU');


function makeArtistRow(artist, index) {
    const row = ARTIST_ROW_TEMPLATE.content.cloneNode(true);
    const rowElement = row.querySelector('tr');

    rowElement.style.setProperty('--cascade-delay', `${index * CASCADE_DELAY}s`);

    const nameCell = row.querySelector('.name-cell');

    const link = nameCell.querySelector('.artist-link');
    link.href = `https://music.yandex.ru/artist/${artist.id}`;
    link.textContent = artist.name;

    row.querySelector('.tracks-cell').textContent =
        formatNumber(artist.tracks_count);

    row.querySelector('.likes-cell').textContent =
        formatNumber(artist.likes_count);

    row.querySelector('.listeners').textContent =
        formatNumber(artist.last_month_listeners);

    let deltaCell = row.querySelector('.listeners-delta');
    const deltaValue = artist.last_month_listeners_delta;
    if (deltaValue > 0) {
        deltaCell.classList.add('rise');
    } else if (deltaValue < 0) {
        deltaCell.classList.add('fall');
    }
    
    deltaCell.textContent =
        `${deltaValue >= 0 ? '+' : '−'}${formatNumber(Math.abs(deltaValue))}`;
    
    row.querySelector('.rating-month-cell').textContent =
        formatNumber(artist.ratings_month);

    const genresContainer = row.querySelector('.genres-cell');
    genresContainer.appendChild(
        makeGenresTag(artist.genres)
    );

    const countryContainer = row.querySelector('.countries-cell');
    countryContainer.appendChild(
        makeCountryTag(artist.countries)
    );

    initInfoLabelButtons(row);

    return row;
}

const SCROLL_THRESHOLD = 400;
const ARTIST_TBODY = document.getElementById('artist-table-body');
const LOADING_MESSAGE = document.getElementById('loading-message');
const EMPTY_MESSAGE = document.getElementById('empty-message');
const ARTIST_TOTAL = document.getElementById('artist-total');

import { queryParams } from './state.js';
let controller;
let isLoading = false;


export async function loadArtistPage(reset = false) {    
    if (isLoading && !reset) return;
    
    
    if (isLoading || !queryParams.has_more) return;

    if (reset) {
        controller?.abort();
        controller = new AbortController();
    }

    isLoading = true;
    LOADING_MESSAGE.classList.remove('not-visible');
    EMPTY_MESSAGE.classList.add('not-visible');

    try {
        if (queryParams.page === 1) {
            ARTIST_TBODY.replaceChildren();
        }

        const response = await fetch('/api/artists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(queryParams)
        });

        const data = await response.json();
        const fragment = document.createDocumentFragment();

        data.artists.forEach((artist, index) => {
            fragment.appendChild(makeArtistRow(artist, index));
        });

        ARTIST_TBODY.appendChild(fragment);

        if (data.total === 0) {
            EMPTY_MESSAGE.classList.remove('not-visible');
        }

        ARTIST_TOTAL.textContent =
            formatNumber(data.total);

        Object.assign(queryParams, {
            has_more: data.has_next,
            page: data.page + 1
        });

    } catch (error) {
        console.error('Ошибка загрузки:', error);
    } finally {
        isLoading = false;
        LOADING_MESSAGE.classList.add('not-visible');
    }
}

const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
        loadArtistPage();
    }
});

observer.observe(document.getElementById('load-trigger'));
