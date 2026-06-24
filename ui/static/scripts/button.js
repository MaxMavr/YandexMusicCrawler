import { updateQueryParams, resetPagination, queryParams } from './state.js';
import { loadArtistPage, isLoading } from './loading.js';
import { getArtistUrl } from './links.js';

function initSortingButtons() {
    document.querySelectorAll('.sorting-button').forEach(button => {
        button.removeEventListener('click', handleSortClick);
        button.addEventListener('click', handleSortClick);
        updateButtonIcon(button);
    });
}

function handleSortClick(event) {
    if (isLoading) return;
    
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
    if (isLoading) return;
    
    const button = document.getElementById('refresh-button');
    const anim = button.querySelector('.refresh-animation');
    
    button.addEventListener('click', () => {
        resetPagination();
        anim.beginElement();
        loadArtistPage(true);
    });
}

async function initRandomButtons() {
    const button = document.getElementById('random-button');

    button.addEventListener('click', async () => {
        if (button.disabled) return;

        try {
            const response = await fetch('/api/random_artist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(queryParams)
            });
    
            const artist = await response.json();
            const url = getArtistUrl(artist.id);
            window.open(url, '_blank');
        } catch (error) {
            console.error('Ошибка загрузки:', error);
        }
    });
}

const TABLE_HEAD = document.getElementById('table-head');

function initSortingMenuButtons() {
    const button = document.getElementById('sorting-menu-button');
    let isVisible = false;

    function handleOutsideClick(e) {
        if (!TABLE_HEAD.contains(e.target)) {
            hideTableHead();
            document.removeEventListener('click', handleOutsideClick);
        }
    }

    function showTableHead() {
        TABLE_HEAD.classList.remove('hidden');
        TABLE_HEAD.classList.add('visible');
        TABLE_HEAD.style.display = 'flex';
        isVisible = true;
    }

    function hideTableHead() {
        TABLE_HEAD.classList.remove('visible');
        TABLE_HEAD.classList.add('hidden');
        isVisible = false;
        
        setTimeout(() => {
            TABLE_HEAD.style.display = 'none';
        }, 200);
    }

    button.addEventListener('click', async () => {
        if (isVisible) {
            hideTableHead();
            document.removeEventListener('click', handleOutsideClick);
        } else {
            showTableHead();
            setTimeout(() => {
                document.addEventListener('click', handleOutsideClick);
            }, 10);
        }
    });
}

initSortingMenuButtons();
initRandomButtons();
initRefreshButtons();
initSortingButtons();