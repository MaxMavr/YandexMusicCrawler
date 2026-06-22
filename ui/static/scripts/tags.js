const TAGS_CONTAINER_TEMPLATE = document.getElementById('tags-container-template');
const TAG_TEMPLATE = document.getElementById('tag-template');

let genreColors = {};
let genreDisplayName = [];

async function loadData() {
    try {
        const [colorsRes, displayRes] = await Promise.all([
            fetch('/api/genre_colors'),
            fetch('/api/genre_display_name')
        ]);
        
        genreColors = await colorsRes.json();
        genreDisplayName = await displayRes.json();

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

function getGenreClass(genreCode) {
    genreCode = genreCode.toLowerCase();

    const found = genreColors.find(group =>
        group.match.some(keyword => genreCode.includes(keyword))
    );

    return found?.class || '';
}

function getGenreDisplayName(genreCode) {
    genreCode = genreCode.toLowerCase();
    
    return genreDisplayName[genreCode] || genreCode;
}

export function getTagsContainer() {
    const container = TAGS_CONTAINER_TEMPLATE.content.cloneNode(true);
    return container.querySelector('.tags-container');
}

export function makeGenreTag(genreCode) {
    const tag = TAG_TEMPLATE.content.cloneNode(true);
    const element = tag.querySelector('.tag');
    element.textContent = getGenreDisplayName(genreCode);
    element.dataset.tagCode = genreCode;

    const cleanGenre = getGenreClass(genreCode) ?? '';
    if (cleanGenre) {
        element.classList.add(cleanGenre);
    }

    return element;
}

export function makeCountryTag(countryCode) {
    const tag = TAG_TEMPLATE.content.cloneNode(true);
    const element = tag.querySelector('.tag');
    element.textContent = countryCode;
    element.dataset.tagCode = countryCode;

    return element;
}

loadData();
