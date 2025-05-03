// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  // Navigation elements
  const newEntryBtn = document.getElementById('new-entry-btn');
  const viewEntriesBtn = document.getElementById('view-entries-btn');
  const searchBtn = document.getElementById('search-btn');
  const welcomeNewEntryBtn = document.getElementById('welcome-new-entry');

  // Sections
  const welcomeSection = document.getElementById('welcome');
  const entryFormSection = document.getElementById('entry-form');
  const entryListSection = document.getElementById('entry-list');
  const entryDetailSection = document.getElementById('entry-detail');
  const searchSection = document.getElementById('search-section');

  // Forms
  const journalForm = document.getElementById('journal-form');
  const searchForm = document.getElementById('search-form');

  // Navigation functions
  function showSection(section) {
    // Hide all sections
    [welcomeSection, entryFormSection, entryListSection, entryDetailSection, searchSection]
      .forEach(s => s.classList.remove('active'));
    [welcomeSection, entryFormSection, entryListSection, entryDetailSection, searchSection]
      .forEach(s => s.classList.add('hidden'));

    // Show the requested section
    section.classList.remove('hidden');
    section.classList.add('active');
  }

  // Event Listeners for Navigation
  newEntryBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showSection(entryFormSection);
  });

  viewEntriesBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showSection(entryListSection);
    // In the future: loadEntries();
  });

  searchBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showSection(searchSection);
  });

  welcomeNewEntryBtn.addEventListener('click', () => {
    showSection(entryFormSection);
  });

  // Form submissions - placeholders for now
  journalForm.addEventListener('submit', (e) => {
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
});
