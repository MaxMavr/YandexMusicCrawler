const TAGS_CONTAINER_TEMPLATE = document.getElementById('tags-container-template');
const TAG_TEMPLATE = document.getElementById('tag-template');

const genreColors = [
    {
        match: [
            'rap',
            'rusrap',
            'foreignrap',
            'turkishrap',
            'arabicrap',
            'moroccanrap',
            'kazakhrap',
            'uzbekrap',
            'israelirap',
            'levantrap'
        ],
        class: 'rap'
    },

    {
        match: [
            'rock',
            'metal',
            'punk',
            'hardcore',
            'posthardcore',
            'numetal'
        ],
        class: 'rock'
    },

    {
        match: [
            'electronic',
            'electronics',
            'edm',
            'techno',
            'house',
            'trance',
            'dubstep',
            'dnb',
            'breakbeat',
            'garage',
            'dance',
            'idm',
            'phonk'
        ],
        class: 'electronic'
    },

    {
        match: [
            'pop',
            'hyperpop',
            'kpop',
            'estrada'
        ],
        class: 'pop'
    },

    {
        match: [
            'jazz',
            'blues',
            'soul',
            'funk',
            'rnb',
            'bebop',
            'bigbands'
        ],
        class: 'rnb'
    },

    {
        match: [
            'folk',
            'country',
            'celtic',
            'african',
            'balkan',
            'armenian',
            'georgian',
            'tatar',
            'jewish'
        ],
        class: 'folk'
    },

    {
        match: [
            'classical',
            'ambient',
            'newage',
            'meditation',
            'relax'
        ],
        class: 'classical'
    },

    {
        match: [
            'audiobook',
            'fiction',
            'literature',
            'memoirs',
            'poetry',
            'podcast'
        ],
        class: 'podcast'
    },

    {
        match: [
            'anime',
            'videogame',
            'soundtrack',
            'films',
            'tvseries',
            'animated'
        ],
        class: 'soundtrack'
    }
];

function getGenreClass(genre) {
    genre = genre.toLowerCase();

    const found = genreColors.find(group =>
        group.match.some(keyword => genre.includes(keyword))
    );

    return found?.class || '';
}

export function makeGenresTag(genres) {
    const container = TAGS_CONTAINER_TEMPLATE.content.cloneNode(true);
    const tagsContainer = container.querySelector('.tags-container');

    genres.forEach(genre => {
        const tag = TAG_TEMPLATE.content.cloneNode(true);
        const element = tag.querySelector('.tag');
        element.textContent = genre;

        const cleanGenre = getGenreClass(genre) ?? '';
        if (cleanGenre) {
            element.classList.add(cleanGenre);
        }

        tagsContainer.appendChild(tag);
    });

    return tagsContainer;
}


export function makeCountryTag(countries) {
    const container = TAGS_CONTAINER_TEMPLATE.content.cloneNode(true);
    const tagsContainer = container.querySelector('.tags-container');

    countries.forEach(country => {
        const tag = TAG_TEMPLATE.content.cloneNode(true);
        const element = tag.querySelector('.tag');
        element.textContent = country;
        tagsContainer.appendChild(tag);
    });

    return tagsContainer;
}
