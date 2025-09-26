document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    const contentSections = document.querySelectorAll('.main-content .content-section');
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // MAP & CHART VARIABLES
    let dashboardMap, geofenceMap, incidentChartInstance, nationalityChartInstance;
    let dashboardMapInitialized = false;
    let geofenceMapInitialized = false;
    let chartsInitialized = false;

    // --- THEME SWITCHER ---
    const applySavedTheme = () => {
        const savedTheme = localStorage.getItem('theme') || 'light';
        body.setAttribute('data-theme', savedTheme);
    };

    themeToggle.addEventListener('click', () => {
        let currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        if (chartsInitialized) {
            destroyCharts();
            initCharts();
        }
    });

    // --- NAVIGATION ---
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
            
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');

            if (targetId === 'reports' && !chartsInitialized) initCharts();
            if (targetId === 'dashboard' && !dashboardMapInitialized) initDashboardMap();
            if (targetId === 'geofence' && !geofenceMapInitialized) initGeofenceMap();
        });
    });

    // --- MAP INITIALIZATION ---
    function initDashboardMap() {
        if (dashboardMapInitialized) return;
        dashboardMap = L.map('dashboard-map').setView([27.0410, 88.2663], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(dashboardMap);

        const alertIcon = L.icon({ iconUrl: 'https://cdn-icons-png.flaticon.com/512/786/786205.png', iconSize: [38, 38], iconAnchor: [19, 38], popupAnchor: [0, -40] });
        L.marker([27.0460, 88.2630], { icon: alertIcon }).addTo(dashboardMap).bindPopup('<b>PANIC BUTTON ALERT</b><br>Anjali Sharma');
        
        const policeIcon = L.icon({ iconUrl: 'https://cdn-icons-png.flaticon.com/512/3079/3079459.png', iconSize: [35, 35], iconAnchor: [17, 35], popupAnchor: [0, -35] });
        L.marker([27.0425, 88.2685], { icon: policeIcon }).addTo(dashboardMap).bindPopup('<b>Police Unit 101</b>');

        L.circle([27.0350, 88.2650], { color: 'blue', fillColor: '#30f', fillOpacity: 0.3, radius: 200 }).addTo(dashboardMap).bindPopup('Tourist Cluster: Chowrasta Mall');
        dashboardMapInitialized = true;

        const fullscreenBtn = document.getElementById('fullscreen-btn');
        const mapContainer = document.querySelector('.map-container');
        fullscreenBtn.addEventListener('click', () => {
            mapContainer.classList.toggle('fullscreen-active');
            setTimeout(() => { dashboardMap.invalidateSize(); }, 200);
        });
    }

    function initGeofenceMap() {
        if (geofenceMapInitialized) return;
        geofenceMap = L.map('geofence-map').setView([27.3389, 88.6065], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap' }).addTo(geofenceMap);
        const restrictedZone = [[27.34, 88.61], [27.35, 88.62], [27.34, 88.63], [27.33, 88.62]];
        L.polygon(restrictedZone, { color: 'red', fillColor: '#f03', fillOpacity: 0.5 }).addTo(geofenceMap).bindPopup('<b>Restricted Forest Area</b>');
        geofenceMapInitialized = true;
    }

    // --- CHART INITIALIZATION ---
    const destroyCharts = () => {
        if (incidentChartInstance) incidentChartInstance.destroy();
        if (nationalityChartInstance) nationalityChartInstance.destroy();
        chartsInitialized = false;
    };

    function initCharts() {
        if (chartsInitialized) return;
        const currentTheme = body.getAttribute('data-theme');
        const gridColor = currentTheme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        const textColor = currentTheme === 'dark' ? '#e1e1e1' : '#333';
        const cardBgColor = currentTheme === 'dark' ? '#222235' : '#fff';
        const barBgColor = currentTheme === 'dark' ? 'rgba(76, 154, 255, 0.7)' : 'rgba(0, 82, 204, 0.7)';
        const barBorderColor = currentTheme === 'dark' ? '#4c9aff' : '#0052cc';

        incidentChartInstance = new Chart(document.getElementById('incidentTypeChart').getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Geo-Fence Breach', 'Panic Button', 'Route Deviation', 'Prolonged Inactivity'],
                datasets: [{ data: [45, 25, 15, 10], backgroundColor: ['#ffab00', '#de350b', '#0052cc', '#777'], borderColor: cardBgColor, borderWidth: 3 }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: textColor } } } }
        });

        nationalityChartInstance = new Chart(document.getElementById('touristNationalityChart').getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['India', 'USA', 'UK', 'Germany', 'France', 'Japan'],
                datasets: [{ label: 'Number of Tourists', data: [1200, 750, 600, 450, 300, 250], backgroundColor: barBgColor, borderColor: barBorderColor, borderWidth: 1, borderRadius: 4 }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: textColor } }, x: { grid: { display: false }, ticks: { color: textColor } } },
                plugins: { legend: { display: false } }
            }
        });
        chartsInitialized = true;
    }

    // --- INITIAL LOAD ---
    applySavedTheme();
    initDashboardMap();
});