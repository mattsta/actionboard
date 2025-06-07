// Toast message handling
document.body.addEventListener('htmx:afterSwap', function(event) {
    const toastElement = document.getElementById('toast-message'); 
    if (toastElement && toastElement.classList.contains('show') && toastElement.textContent.trim() !== '') {
        setTimeout(() => {
            toastElement.classList.remove('show'); 
            setTimeout(() => {
                const currentToast = document.getElementById('toast-message');
                if (currentToast === toastElement && !currentToast.classList.contains('show')) {
                    currentToast.innerHTML = ''; 
                    currentToast.classList.remove('error'); 
                }
            }, 500); 
        }, 3000); 
    }
});

// WebSocket for live button updates
function connectWebSocket() {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/button_updates`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = function(event) {
        console.log("WebSocket connection established for live updates.");
    };

    socket.onmessage = function(event) {
        console.log("WebSocket message received:", event.data);
        try {
            const message = JSON.parse(event.data);
            if (message.type === "button_content_update" && message.payload) {
                updateButtonContent(message.payload);
            } else if (message.type === "navigation_update") {
                console.log("Navigation update message received. Refreshing navigation panel.");
                refreshNavigationPanel();
            }
        } catch (e) {
            console.error("Error parsing WebSocket message or invalid message format:", e);
        }
    };

    socket.onclose = function(event) {
        console.log("WebSocket connection closed. Attempting to reconnect in 5 seconds...");
        setTimeout(connectWebSocket, 5000); // Simple reconnect logic
    };

    socket.onerror = function(error) {
        console.error("WebSocket error:", error);
        // socket.close() will typically be called by the browser after an error, triggering onclose.
    };
}

function updateButtonContent(data) {
    const buttonId = data.button_id;
    if (!buttonId) {
        console.warn("Button update received without button_id:", data);
        return;
    }

    const buttonElement = document.getElementById(`btn-${buttonId}`);
    if (!buttonElement) {
        console.warn(`Button element with id 'btn-${buttonId}' not found for update.`);
        return;
    }

    // Update text
    if (typeof data.text === 'string') {
        const textElement = buttonElement.querySelector('[data-role="button-text"]');
        if (textElement) {
            textElement.textContent = data.text;
        } else {
            console.warn(`Text element not found for button 'btn-${buttonId}'.`);
        }
    }

    // Update icon
    const iconElement = buttonElement.querySelector('[data-role="button-icon"]');
    if (iconElement) {
        if (typeof data.icon_class === 'string') {
            if (data.icon_class) { // Non-empty string: set new icon
                iconElement.className = data.icon_class;
                iconElement.style.display = ''; // Ensure it's visible
            } else { // Empty string or null means remove/hide icon
                iconElement.className = '';
                iconElement.style.display = 'none'; // Hide it
            }
        }
    } else if (typeof data.icon_class === 'string' && data.icon_class) {
        // If icon element doesn't exist but new icon_class is provided, create it
        console.warn(`Icon element not found for button 'btn-${buttonId}', creating one.`);
        const newIcon = document.createElement('i');
        newIcon.setAttribute('data-role', 'button-icon');
        newIcon.className = data.icon_class;
        // Prepend to keep it before the text, similar to the template
        const textSpan = buttonElement.querySelector('[data-role="button-text"]');
        if (textSpan) {
            buttonElement.insertBefore(newIcon, textSpan);
        } else {
            buttonElement.prepend(newIcon);
        }
    }


    // Update style class
    if (typeof data.style_class === 'string') {
        const currentStyle = buttonElement.dataset.currentStyleClass;
        if (currentStyle && currentStyle !== "") {
            buttonElement.classList.remove(currentStyle);
        }
        if (data.style_class && data.style_class !== "") { // Non-empty string: add new style
            buttonElement.classList.add(data.style_class);
            buttonElement.dataset.currentStyleClass = data.style_class;
        } else { // Empty string or null means remove custom style (revert to default)
            buttonElement.dataset.currentStyleClass = ""; // Clear stored style
        }
    }
     // Update title attribute if text changed (useful for accessibility and tooltips)
    if (typeof data.text === 'string') {
        buttonElement.title = data.text;
    }
}

function refreshNavigationPanel() {
    const navElement = document.getElementById('page-navigation');
    if (!navElement) {
        console.error("Navigation element '#page-navigation' not found in DOM.");
        return;
    }

    let activePageId = '';
    const activeLink = navElement.querySelector('.nav-link.active');
    if (activeLink && activeLink.dataset.pageId) {
        activePageId = activeLink.dataset.pageId;
    }
    
    const refreshUrl = `/content/navigation_panel${activePageId ? '?active_page_id=' + encodeURIComponent(activePageId) : ''}`;
    
    console.log(`Requesting navigation refresh from: ${refreshUrl}`);
    
    // Use HTMX's JavaScript API to request and swap the navigation content
    htmx.ajax('GET', refreshUrl, {
        target: '#page-navigation',
        swap: 'outerHTML' // Replace the entire <nav> element
    }).catch(error => {
        console.error("Error refreshing navigation panel:", error);
    });
}

// Initialize WebSocket connection when the page loads
document.addEventListener('DOMContentLoaded', connectWebSocket);
