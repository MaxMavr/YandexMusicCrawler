const INFO_LABEL_TEMPLATE = document.getElementById('info-label-template');
const HOVER_DELAY = 1000;
const INFO_LABEL_OFFSET = 10;

let hoverTimeout = null;
let currentInfoLabel = null;

let mouseX = 0;
let mouseY = 0;
document.addEventListener('mousemove', function(event) {
    mouseX = event.clientX;
    mouseY = event.clientY;
});


export function setupInfoLabelButton(element, text) {
    element.classList.add('info-label-button');
    if (text !== undefined && text !== null) {
        element.dataset.text = text;
    }

    return element;
}

export function initInfoLabelButtons(context = document) { 
    const infoLabelButtons = context.querySelectorAll('.info-label-button'); 

    infoLabelButtons.forEach(button => {
        button.addEventListener('mouseenter', function(event) {
            clearTimeout(hoverTimeout);
            removeInfoLabel();
            
            const targetButton = event.currentTarget;
            hoverTimeout = setTimeout(() => {
                handleInfoLabel(targetButton);
            }, HOVER_DELAY);
        });

        button.addEventListener('click', function() {
            clearTimeout(hoverTimeout);
            removeInfoLabel();
        });

        button.addEventListener('mouseleave', function() {
            clearTimeout(hoverTimeout);
            removeInfoLabel();
        });
        });
}

function handleInfoLabel(button) { 
    const text = button.dataset.text;

    const infoLabel = INFO_LABEL_TEMPLATE.content.cloneNode(true);
    const element = infoLabel.querySelector('.info-label');
    document.body.appendChild(element);
    element.textContent = text;

    const labelRect = element.getBoundingClientRect();
    const labelWidth = labelRect.width;
    const labelHeight = labelRect.height;

    let left = mouseX + INFO_LABEL_OFFSET;
    let top = mouseY + INFO_LABEL_OFFSET;
    
    if (left + labelWidth > window.innerWidth) {
        left = mouseX - labelWidth - INFO_LABEL_OFFSET;
    }
    
    if (top + labelHeight > window.innerHeight) {
        top = mouseY - labelHeight - INFO_LABEL_OFFSET;
    }

    element.style.left = left + 'px';
    element.style.top = top + 'px';

    currentInfoLabel = element;
}

function removeInfoLabel() {
    if (currentInfoLabel && currentInfoLabel.parentNode) {
        currentInfoLabel.parentNode.removeChild(currentInfoLabel);
        currentInfoLabel = null;
    }
}

initInfoLabelButtons();