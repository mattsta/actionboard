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

function renderSparkline(svgElement, sparklinePayload) {
    if (!svgElement || !sparklinePayload || !sparklinePayload.data || sparklinePayload.data.length < 2) {
        svgElement.innerHTML = ''; // Clear if no data or not enough data
        return;
    }

    const data = sparklinePayload.data;
    const color = sparklinePayload.color || "currentColor";
    const strokeWidth = sparklinePayload.stroke_width || 1.5;
    
    // Use the viewBox from the SVG element itself (e.g., "0 0 100 25")
    const viewBoxParts = svgElement.getAttribute('viewBox').split(' ').map(Number);
    const vbX = viewBoxParts[0];
    const vbY = viewBoxParts[1];
    const vbWidth = viewBoxParts[2];
    const vbHeight = viewBoxParts[3];

    const minVal = Math.min(...data);
    const maxVal = Math.max(...data);
    const range = maxVal - minVal;

    // Handle case where all data points are the same (range is 0)
    const yNormalizer = range === 0 
        ? (val) => vbY + vbHeight / 2  // Draw a flat line in the middle
        : (val) => vbY + vbHeight - ((val - minVal) / range) * vbHeight; // Invert Y for SVG

    const points = data.map((val, index) => {
        const x = vbX + (index / (data.length - 1)) * vbWidth;
        const y = yNormalizer(val);
        return `${x},${y}`;
    });

    const pathD = "M " + points.join(" L ");

    // Clear previous paths
    svgElement.innerHTML = ''; 

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pathD);
    path.setAttribute("stroke", color);
    path.setAttribute("stroke-width", strokeWidth.toString());
    path.setAttribute("fill", "none");
    path.setAttribute("vector-effect", "non-scaling-stroke"); // Keeps stroke width consistent on resize

    svgElement.appendChild(path);
}


function updateButtonContent(data) {
    const buttonId = data.button_id;
    if (!buttonId) {
        console.warn("Button update received without button_id:", data);
        return;
    }

    const buttonElement = document.getElementById(`btn-${buttonId}`);
    if (!buttonElement) {
        // This is an expected scenario if the button is on a page that is not currently visible.
        // The warning is removed to avoid cluttering the console for this normal behavior.
        // console.warn(`Button element with id 'btn-${buttonId}' not found for update.`); 
        return;
    }

    const iconElement = buttonElement.querySelector('[data-role="button-icon"]');
    const sparklineElement = buttonElement.querySelector('[data-role="button-sparkline"]');

    // Handle Sparkline or Icon update (mutually exclusive)
    if (data.sparkline && data.sparkline.data && data.sparkline.data.length > 0) {
        if (iconElement) iconElement.style.display = 'none';
        if (sparklineElement) {
            sparklineElement.style.display = '';
            renderSparkline(sparklineElement, data.sparkline);
        }
    } else if (typeof data.icon_class === 'string') {
        if (sparklineElement) sparklineElement.style.display = 'none';
        if (iconElement) {
            if (data.icon_class) { // Non-empty string: set new icon
                iconElement.className = data.icon_class; // Resets all classes then sets the new one
                iconElement.style.display = ''; 
            } else { // Empty string means remove/hide icon
                iconElement.className = '';
                iconElement.style.display = 'none'; 
            }
        }
    } else if (data.hasOwnProperty('sparkline') && (data.sparkline === null || (data.sparkline.data && data.sparkline.data.length === 0))) {
        // Explicitly clearing sparkline (e.g. by sending sparkline: null or sparkline: {data:[]})
        if (sparklineElement) {
            sparklineElement.style.display = 'none';
            sparklineElement.innerHTML = ''; // Clear its content
        }
        // Optionally, restore a default icon or ensure icon is visible if no icon_class was provided to hide it
        if (iconElement && !iconElement.className) { // If icon has no class, it might be hidden
             // iconElement.style.display = 'none'; // Or set a default icon here
        }
    }


    // Update text (independent of icon/sparkline)
    if (typeof data.text === 'string') {
        const textElement = buttonElement.querySelector('[data-role="button-text"]');
        if (textElement) {
            textElement.textContent = data.text;
        } else {
            console.warn(`Text element not found for button 'btn-${buttonId}'.`);
        }
        buttonElement.title = data.text; // Update title attribute for accessibility
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
}

function refreshNavigationPanel() {
    const navElement = document.getElementById('page-navigation');
    if (!navElement) {
        console.error("Navigation element '#page-navigation' not found in DOM for refresh trigger.");
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
        target: '#page-navigation', // The element to be replaced
        swap: 'outerHTML'          // Replace the entire <nav> element
    }).then(() => {
        // After the swap, the original #page-navigation element is gone, 
        // and a new one (from the response) has taken its place.
        // We need to tell HTMX to process this new element.
        const newNavElement = document.getElementById('page-navigation');
        if (newNavElement) {
            htmx.process(newNavElement);
            console.log("Explicitly processed new #page-navigation element with HTMX.");
        } else {
            // This case should ideally not happen if the server correctly returns a <nav id="page-navigation">...</nav>
            console.error("#page-navigation element not found after outerHTML swap. This is unexpected.");
        }
    }).catch(error => {
        console.error("Error refreshing navigation panel:", error);
    });
}

// Initialize WebSocket connection when the page loads
document.addEventListener('DOMContentLoaded', connectWebSocket);
