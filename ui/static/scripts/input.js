import { updateQueryParams, updateQueryFilterParams, queryParams, resetPagination } from './state.js';
import { loadArtistPage } from './loading.js';


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


function initSortingButtons() {
    document.querySelectorAll('.sorting-button').forEach(button => {
        button.removeEventListener('click', handleSortClick);
        button.addEventListener('click', handleSortClick);
        updateButtonIcon(button);
    });
}

function handleSortClick(event) {
    const button = event.currentTarget;
    const isActive = button.classList.contains('activated');

    document.querySelectorAll('.sorting-button.activated')
        .forEach(btn => {
            if (btn !== button) {
                btn.classList.remove('activated');
                btn.dataset.sortOrder = 'ASC';
                updateButtonIcon(btn);
            }
        });

    if (!isActive) {
        button.classList.add('activated');
        button.dataset.sortOrder = 'ASC';
    } else {
        button.dataset.sortOrder =
            button.dataset.sortOrder === 'ASC' ? 'DESC' : 'ASC';
    }

    updateButtonIcon(button);

    updateQueryParams({
        sortBy: button.dataset.sortBy,
        sortOrder: button.dataset.sortOrder,
    });

    resetPagination();
    loadArtistPage(true);
}

function updateButtonIcon(button) {
    const state = !button.classList.contains('activated')
        ? 'none'
        : button.dataset.sortOrder.toLowerCase();

    button.querySelector(`.anim-${state}-upper`)?.beginElement();
    button.querySelector(`.anim-${state}-lower`)?.beginElement();
}


function initRefreshButtons() {
    const button = document.getElementById('refresh-button');
    const anim = button.querySelector('.refresh-animation');
    
    button.addEventListener('click', () => {
        resetPagination();
        anim.beginElement();
        loadArtistPage(true);
    });
}


initRefreshButtons();
initSortingButtons();
initInput();
