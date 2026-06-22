const TAGS_OVERLAY_TEMPLATE = document.getElementById('tags-overlay-template');

const FILTER_CONFIG = {
    genres: {
        url: '/api/all_genres',
        make: makeGenreTag,
        selected: queryParams.filters.genres,
        container: document.getElementById('genres-tags-container'),
        info_label_delete: 'Убрать жанр из сортировки'
    },
    countries: {
        url: '/api/all_countries',
        make: makeCountryTag,
        selected: queryParams.filters.countries,
        container: document.getElementById('countries-tags-container'),
        info_label_delete: 'Убрать страну из сортировки'
    }
};

import { queryParams, resetPagination } from './state.js';
import { loadArtistPage } from './loading.js';
import { makeGenreTag, makeCountryTag, getTagsContainer } from './tags.js';
import { setupInfoLabelButton, initInfoLabelButtons } from './info.js';


function initTagsButtons() {
    document
        .querySelectorAll('.tags-button')
        .forEach(button =>
            button.addEventListener('click', handleTagsButtonClick)
        );
}

async function handleTagsButtonClick(event) {
    const button = event.currentTarget;
    const type = button.dataset.type;
    const config = FILTER_CONFIG[type];

    if (!config) {
        console.error('Неизвестный тип фильтра');
        return;
    }

    try {
        const response = await fetch(config.url);
        const data = await response.json();
        const tagsContainer = getTagsContainer();
        tagsContainer.classList.add('overlay-tags-container');

        data.forEach(tagCode => {
            const tag = config.make(tagCode);

            if (config.selected.includes(tagCode)) {
                tag.classList.add('selected');
            }

            tag.addEventListener('click', e => {
                handleTagMenuClick(
                    e,
                    type
                );
            });

            tagsContainer.appendChild(tag);
        });

        tagsContainer.classList.add('select-tags');
        createOverlay(button, tagsContainer);

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

export function handleTagMenuClick(event, type) {
    const tag = event.currentTarget;
    const tagCode = tag.dataset.tagCode;
    const selected = FILTER_CONFIG[type].selected;

    if (selected.includes(tagCode)) {
        tag.classList.remove('selected');
        removeTag(tagCode, selected);
    } else {
        tag.classList.add('selected');
        addTag(tagCode, selected);
    }

    updateTagFilter();
}

function handleTagClick(event, selected) {
    const tag = event.currentTarget;
    const tagCode = tag.dataset.tagCode;
    
    removeTag(tagCode, selected);
    updateTagFilter();
}

function updateTagFilter() {
    resetPagination();
    renderSelectedTags();
    loadArtistPage(true);
}


function addTag(tagCode, selected) {    
    selected.push(tagCode);
}

function removeTag(tagCode, selected) {
    const index = selected.indexOf(tagCode);
    if (index !== -1) { selected.splice(index, 1); }
}

function renderSelectedTags() {
    Object.values(FILTER_CONFIG).forEach(config => {
        config.container.replaceChildren();

        config.selected.forEach(tagCode => {
            const tag = config.make(tagCode);
            tag.classList.add('selected');
            setupInfoLabelButton(tag, config.info_label_delete)

            tag.addEventListener('click', (e) => {
                handleTagClick(e, config.selected)
            });

            config.container.append(tag);
        });

        initInfoLabelButtons(config.container);
    });
}

initTagsButtons();