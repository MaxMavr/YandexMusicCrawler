import { makeGenreTag, makeCountryTag, getTagsContainer } from './tags.js';
import { setupInfoLabelButton, initInfoLabelButtons } from './info.js';
import { getArtistUrl, getArtistAvatar } from './links.js';
import { handleTagMenuClick } from './select_tags.js';

const ROW_TEMPLATE = document.getElementById('row-template');
const CASCADE_DELAY = 0.05;
const DEFAULT_ARTIST_COVER_TEMPLATE = document.getElementById('default-artist-cover-template');
const COVER_IMAGE_SIZES = [50, 100, 200, 400, 800];


const formatNumber = value => value.toLocaleString('ru-RU');

function makeLoadingRow(index) {
    const row = ROW_TEMPLATE.content.cloneNode(true);
    const rowElement = row.querySelector('.table-row');
    rowElement.classList.add('loading');
    rowElement.style.setProperty('--cascade-delay', `${index * CASCADE_DELAY}s`);
    return rowElement;
}


function makeArtistRow(artist, index, rowNumber) {
    const row = ROW_TEMPLATE.content.cloneNode(true);
    const rowElement = row.querySelector('.table-row');
    rowElement.style.setProperty('--cascade-delay', `${index * CASCADE_DELAY}s`);

    const numberCell = row.querySelector('.row-number');
    numberCell.textContent = rowNumber;
    
    const nameCell = row.querySelector('.name-cell');
    nameCell.href = getArtistUrl(artist.id);

    const cover = nameCell.querySelector('.artist-cover');
    if (artist.cover_uri && artist.cover_uri.trim() !== '') {
        const img = document.createElement('img');
        img.srcset = COVER_IMAGE_SIZES.map(s => `${getArtistAvatar(artist.cover_uri, s)} ${s}w`).join(', ');
        img.src = getArtistAvatar(artist.cover_uri, 50);
        cover.appendChild(img);
    } else {
        cover.appendChild(DEFAULT_ARTIST_COVER_TEMPLATE.content.cloneNode(true));
    }

    const name = nameCell.querySelector('.artist-name');
    name.textContent = artist.name;

    row.querySelector('.tracks-title').textContent =
        formatNumber(artist.tracks_count);

    row.querySelector('.likes-title').textContent =
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

    row.querySelector('.crown-title').textContent =
        formatNumber(artist.ratings_month);

    const genresTagsContainer = getTagsContainer();
    artist.genres.forEach(tagCode => {
        const tag = makeGenreTag(tagCode);
        tag.addEventListener('click', e => {
            handleTagMenuClick(
                e,
                'genres'
            );
        });

        if (queryParams.filters.genres.includes(tagCode)) {
            setupInfoLabelButton(tag, 'Убрать жанр из сортировки');
        } else {
            setupInfoLabelButton(tag, 'Добавить жанр в сортировку');
        }
        genresTagsContainer.appendChild(tag);
    });
    const genresContainer = row.querySelector('.genres-cell');
    genresContainer.appendChild(genresTagsContainer);
    
    const countryTagsContainer = getTagsContainer();
    artist.countries.forEach(tagCode => {
        const tag = makeCountryTag(tagCode);
        tag.addEventListener('click', e => {
            handleTagMenuClick(
                e,
                'countries'
            );
        });

        if (queryParams.filters.countries.includes(tagCode)) {
            setupInfoLabelButton(tag, 'Убрать страну из сортировку');
        } else {
            setupInfoLabelButton(tag, 'Добавить страну в сортировку');
        }

        countryTagsContainer.appendChild(tag);
    });
    const countryContainer = row.querySelector('.countries-cell');
    countryContainer.appendChild(countryTagsContainer);

    initInfoLabelButtons(row);
    return row;
}

const TABLE_BODY = document.getElementById('table-body');
const ARTIST_TOTAL = document.getElementById('artist-total');
const EMPTY_TEMPLATE = document.getElementById('empty-template');
const RANDOM_BUTTON = document.getElementById('random-button');
const REFRESH_BUTTON = document.getElementById('refresh-button');
import { queryParams } from './state.js';
let controller;
export let isLoading = false;


export async function loadArtistPage(reset = false) {    
    if (isLoading && !reset) return;
    if (isLoading || !queryParams.has_more) return;

    if (reset) {
        controller?.abort();
        controller = new AbortController();
    }

    if (queryParams.page === 1) {
        TABLE_BODY.replaceChildren();
    }

    isLoading = true;
    ARTIST_TOTAL.textContent = '';
    REFRESH_BUTTON.classList.add('loading')

    const loadingRows = [];
    for (let i = 0; i < queryParams.pageSize; i++) {
        const row = makeLoadingRow(i);
        loadingRows.push(row);
        TABLE_BODY.appendChild(row);
    }

    try {
        const response = await fetch('/api/artists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(queryParams)
        });

        const data = await response.json();
        
        data.artists.forEach((artist, index) => {
            const rowNumber = ((data.page - 1) * data.page_size) + index + 1;
            const newRow = makeArtistRow(artist, index, rowNumber);

            if (loadingRows[index]) {
                loadingRows[index].replaceWith(
                    newRow.querySelector('.table-row')
                );
            } else {
                TABLE_BODY.appendChild(newRow);
            }
        });

        for (let i = data.artists.length; i < loadingRows.length; i++) {
            if (loadingRows[i]) {
                loadingRows[i].remove();
            }
        }
        
        if (data.total === 0) {
            TABLE_BODY.appendChild(EMPTY_TEMPLATE.content.cloneNode(true));
            RANDOM_BUTTON.disabled = true;
        } else {
            RANDOM_BUTTON.disabled = false;
        }

        REFRESH_BUTTON.classList.remove('loading')
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
    }
}

const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
        loadArtistPage();
    }
});

observer.observe(document.getElementById('load-trigger'));
