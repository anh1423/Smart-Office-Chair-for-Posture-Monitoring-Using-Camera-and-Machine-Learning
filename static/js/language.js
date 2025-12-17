// Language Switcher
// Handles English/Vietnamese language toggling and persistence

(function () {
    'use strict';

    // Get saved language or default to 'en'
    const savedLang = localStorage.getItem('language') || 'en';

    // Apply language immediately
    applyLanguage(savedLang);

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function () {
        const languageToggle = document.getElementById('languageToggle');

        if (!languageToggle) {
            console.warn('Language toggle button not found');
            return;
        }

        // Update flag icon based on current language
        updateLanguageIcon(savedLang);

        // Language toggle click handler
        languageToggle.addEventListener('click', function () {
            const currentLang = localStorage.getItem('language') || 'en';
            const newLang = currentLang === 'en' ? 'vi' : 'en';

            // Apply new language
            applyLanguage(newLang);
            localStorage.setItem('language', newLang);

            // Update icon
            updateLanguageIcon(newLang);

            console.log('Language switched to:', newLang);
        });
    });

    function applyLanguage(lang) {
        if (typeof translations === 'undefined') {
            console.error('Translations not loaded');
            return;
        }

        const langData = translations[lang];
        if (!langData) {
            console.error('Language not found:', lang);
            return;
        }

        // Find all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = langData[key];

            if (translation) {
                // Check if element has data-i18n-attr to translate attribute instead of text
                const attr = element.getAttribute('data-i18n-attr');
                if (attr) {
                    element.setAttribute(attr, translation);
                } else {
                    element.textContent = translation;
                }
            }
        });
    }

    function updateLanguageIcon(lang) {
        const languageToggle = document.getElementById('languageToggle');
        if (!languageToggle) return;

        if (lang === 'vi') {
            // Show US flag (for switching to English)
            languageToggle.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <rect width="20" height="20" rx="2" fill="#B22234"/>
                    <path d="M0 2.5H20M0 5H20M0 7.5H20M0 10H20M0 12.5H20M0 15H20M0 17.5H20" stroke="white" stroke-width="1.5"/>
                    <rect width="8" height="8.5" fill="#3C3B6E"/>
                    <text x="4" y="5.5" fill="white" font-size="3" text-anchor="middle">EN</text>
                </svg>
            `;
            languageToggle.title = 'Switch to English';
        } else {
            // Show Vietnam flag (for switching to Vietnamese)
            languageToggle.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <rect width="20" height="20" rx="2" fill="#DA251D"/>
                    <path d="M10 4L11.5 8.5H16L12.5 11.5L14 16L10 13L6 16L7.5 11.5L4 8.5H8.5L10 4Z" fill="#FFFF00"/>
                </svg>
            `;
            languageToggle.title = 'Chuyển sang Tiếng Việt';
        }
    }

    // Expose applyLanguage globally for dynamic content
    window.applyLanguage = applyLanguage;
})();
