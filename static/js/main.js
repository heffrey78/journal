// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Navigation elements
    const navHome = document.getElementById('nav-home');
    const navNew = document.getElementById('nav-new');
    const navList = document.getElementById('nav-list');
    const navSearch = document.getElementById('nav-search');
    const startButton = document.getElementById('start-button');

    // Sections
    const welcomeSection = document.getElementById('welcome');
    const newEntrySection = document.getElementById('new-entry');
    const entryListSection = document.getElementById('entry-list');
    const entryDetailSection = document.getElementById('entry-detail');
    const searchSection = document.getElementById('search');

    // Forms
    const entryForm = document.getElementById('entry-form');
    const searchForm = document.getElementById('search-form');

    // Navigation functions
    function showSection(section) {
        // Hide all sections
        [welcomeSection, newEntrySection, entryListSection, entryDetailSection, searchSection]
            .forEach(s => s.classList.remove('active'));

        // Show the requested section
        section.classList.add('active');
    }

    // Event Listeners for Navigation
    navHome.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(welcomeSection);
    });

    navNew.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(newEntrySection);
    });

    navList.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(entryListSection);
        // In the future: loadEntries();
    });

    navSearch.addEventListener('click', (e) => {
        e.preventDefault();
        showSection(searchSection);
    });

    startButton.addEventListener('click', () => {
        showSection(newEntrySection);
    });

    // Form submissions - placeholders for now
    entryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Entry submission will be implemented in the next phase');
        // In the future: saveEntry(formData);
    });

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Search functionality will be implemented in the next phase');
        // In the future: performSearch(searchQuery, isSemanticSearch);
    });

    // Entry Detail Navigation
    document.getElementById('back-to-list').addEventListener('click', () => {
        showSection(entryListSection);
    });

    document.getElementById('summarize-entry').addEventListener('click', () => {
        alert('Summarize functionality will be implemented in a future phase');
        // In the future: summarizeEntry(currentEntryId);
    });
});
