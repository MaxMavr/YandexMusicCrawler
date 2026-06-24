import { queryParams, resetPagination, updateQueryFilterParams } from './state.js';
import { loadArtistPage, isLoading } from './loading.js';

function initInput() { 
    const inputs = document.querySelectorAll('.input'); 
    
    inputs.forEach(input => {
        input.addEventListener('keyup', e => {
            if (e.key === 'Enter') handleInput(e);
        });

        input.addEventListener('blur', handleInput);
    });
}

function handleInput(event) {    
    event.preventDefault();
    
    if (isLoading) return;

    const input = event.currentTarget;
    const fieldName = input.id;
    const rawValue = input.value;

    const previousValue = queryParams.filters[fieldName];

    let value;
    if (rawValue === null) {
        value = null;
    } else if (input.type === 'text') {
        value = rawValue.trim();
    } else if (rawValue === '') {
        value = null;
    } else if (input.type === 'number') {
        const number = Number(rawValue);
        value = isNaN(number) ? null : number;
    } else {
        value = null;
    }

    if (value === previousValue) {
        return;
    }
    updateInputFilter(fieldName, value);
}

function updateInputFilter(fieldName, value) {
    resetPagination();
    updateQueryFilterParams(fieldName, value);
    loadArtistPage(true);
}

initInput();
