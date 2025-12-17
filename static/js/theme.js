// Theme Switcher
// Handles dark/light theme toggling and persistence

(function () {
    'use strict';

    // Get saved theme or default to 'dark'
    const savedTheme = localStorage.getItem('theme') || 'dark';

    // Apply theme immediately to prevent flash
    document.documentElement.setAttribute('data-theme', savedTheme);

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function () {
        const themeToggle = document.getElementById('themeToggle');

        if (!themeToggle) {
            console.warn('Theme toggle button not found');
            return;
        }

        // Update icon based on current theme
        updateThemeIcon(savedTheme);

        // Theme toggle click handler
        themeToggle.addEventListener('click', function () {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            // Apply new theme
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            // Update icon
            updateThemeIcon(newTheme);

            console.log('Theme switched to:', newTheme);
        });
    });

    function updateThemeIcon(theme) {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;

        if (theme === 'light') {
            // Show moon icon (for switching to dark)
            themeToggle.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M17 10.5C16.4 12.7 14.4 14.3 12 14.3C9.1 14.3 6.7 11.9 6.7 9C6.7 6.6 8.3 4.6 10.5 4C10.2 4 9.9 4 9.7 4C6.2 4 3.3 6.9 3.3 10.4C3.3 13.9 6.2 16.8 9.7 16.8C13.2 16.8 16.1 13.9 16.1 10.4C16.1 10.1 16.1 10.8 17 10.5Z" 
                          fill="currentColor"/>
                </svg>
            `;
        } else {
            // Show sun icon (for switching to light)
            themeToggle.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="3" stroke="currentColor" stroke-width="2"/>
                    <path d="M10 2V4M10 16V18M18 10H16M4 10H2M15.66 15.66L14.24 14.24M5.76 5.76L4.34 4.34M15.66 4.34L14.24 5.76M5.76 14.24L4.34 15.66" 
                          stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            `;
        }
    }
})();
