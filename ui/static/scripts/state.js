export let queryParams = {
    filters: {
        is_available: null,
        is_listened: null,
        name_contains: '',

        min_listeners: null,
        max_listeners: null,
        min_listeners_delta: null,
        max_listeners_delta: null,

        min_likes: null,
        max_likes: null,
        min_tracks: 1,
        max_tracks: null,
        min_ratings_month: null,
        max_ratings_month: null,

        genres: [],
        countries: [],
    },
    has_more: true,
    page: 1,
    pageSize: 20,
    sortBy: 'id',
    sortOrder: 'asc', // desc
};

export function updateQueryParams(newParams) {
    queryParams = { ...queryParams, ...newParams };
}

export function updateQueryFilterParams(filterName, value) {
    queryParams = {
        ...queryParams,
        filters: {
            ...queryParams.filters,
            [filterName]: value
        }
    };
}