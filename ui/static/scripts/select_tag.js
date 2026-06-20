const TAGS_OVERLAY_TEMPLATE = document.getElementById('tags-overlay-template');

const FILTER_CONFIG = {
    genres: {
        url: '/api/all_genres',
        make: makeGenresTag,
        selected: queryParams.filters.genres,
        container: document.getElementById('genres-tags-container')
    },
    countries: {
        url: '/api/all_countries',
        make: makeCountryTag,
        selected: queryParams.filters.countries,
        container: document.getElementById('countries-tags-container')
    }
};

import { queryParams, updateQueryParams } from './state.js';
import { loadArtistPage } from './loading.js';
import { makeGenresTag, makeCountryTag } from './tags.js';

function initTagsButtons() {
    document
        .querySelectorAll('.tags-button')
        .forEach(button =>
            button.addEventListener('click', handleTagsButtonClick)
        );
}

async function handleTagsButtonClick(event) {
    const button = event.currentTarget;
    const config = FILTER_CONFIG[button.dataset.type];

    if (!config) {
        console.error('Неизвестный тип фильтра');
        return;
    }

    try {
        const response = await fetch(config.url);
        const data = await response.json();

        const tags = config.make(data);

        tags.querySelectorAll('.tag').forEach(tag => {
            const text = tag.textContent.trim();

            tag.classList.add('select-tag');
            tag.classList.remove('tag');

            if (config.selected.includes(text)) {
                tag.classList.add('selected');
            }

            tag.addEventListener('click', e => {
                tag.classList.add('selected');
                handleTagMenuClick(
                    e,
                    config.container,
                    config.selected
                );
            });
        });

        tags.classList.add('select-tags');

        createOverlay(button, tags);

    } catch (error) {
        console.error('Ошибка загрузки тегов:', error);
    }
}

function createOverlay(button, tags) {
    const overlay = TAGS_OVERLAY_TEMPLATE.content.cloneNode(true);
    const overlayElement = overlay.querySelector('.overlay');

    overlayElement.appendChild(tags);
    document.body.appendChild(overlayElement);

    const rect = button.getBoundingClientRect();
    const width = overlayElement.getBoundingClientRect().width;

    overlayElement.style.top = `${rect.top}px`;

    if (rect.left + width < window.innerWidth) {
        overlayElement.style.left = `${rect.left}px`;
    } else {
        overlayElement.style.right =
            `${window.innerWidth - rect.right}px`;
    }

    function handleOutsideClick(e) {
        if (
            !overlayElement.contains(e.target) &&
            !button.contains(e.target)
        ) {
            overlayElement.remove();
            document.removeEventListener('click', handleOutsideClick);
        }
    }

    setTimeout(() => {
        document.addEventListener('click', handleOutsideClick);
    });
}

function handleTagMenuClick(event, container, selected) {
    const tag = event.currentTarget;
    const value = tag.textContent.trim();

    if (selected.includes(value)) {
        return;
    }

    selected.push(value);

    const clonedTag = tag.cloneNode(true);

    clonedTag.addEventListener('click', e => {
        handleTagClick(e, selected);
        clonedTag.remove();
    });

    container.prepend(clonedTag);

    updateQueryParams({page: 1, has_more: true,});
    loadArtistPage(true);
}

function handleTagClick(event, selected) {
    const tag = event.currentTarget;
    const value = tag.textContent.trim();
    tag.classList.remove('selected');

    const index = selected.indexOf(value);

    if (index !== -1) {
        selected.splice(index, 1);
    }

    updateQueryParams({page: 1, has_more: true,});
    loadArtistPage(true);
}

initTagsButtons();