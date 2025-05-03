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

  // Content containers
  const entriesContainer = document.getElementById('entries-container');
  const entryContent = document.getElementById('entry-content');

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

  // API Functions
  async function fetchEntries(limit = 10, offset = 0) {
    try {
      const response = await fetch(`/entries/?limit=${limit}&offset=${offset}`);
      if (!response.ok) {
        throw new Error(`Error fetching entries: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch entries:', error);
      return [];
    }
  }

  async function fetchEntry(entryId) {
    try {
      const response = await fetch(`/entries/${entryId}`);
      if (!response.ok) {
        throw new Error(`Error fetching entry: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch entry ${entryId}:`, error);
      return null;
    }
  }

  async function createEntry(entryData) {
    try {
      const response = await fetch('/entries/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entryData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error creating entry: ${errorData.detail || response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create entry:', error);
      return null;
    }
  }

  // UI Functions
  function renderEntries(entries) {
    entriesContainer.innerHTML = '';

    if (!entries || entries.length === 0) {
      entriesContainer.innerHTML = '<p>No journal entries found.</p>';
      return;
    }

    entries.forEach(entry => {
      // Format the date
      const date = new Date(entry.created_at);
      const formattedDate = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
      });

      // Create a preview of the content (first 100 chars)
      const contentPreview = entry.content.length > 100
        ? `${entry.content.substring(0, 100)}...`
        : entry.content;

      // Create tags HTML
      const tagsHtml = entry.tags && entry.tags.length
        ? entry.tags.map(tag => `<span class="tag">${tag}</span>`).join('')
        : '';

      const entryCard = document.createElement('div');
      entryCard.className = 'entry-card';
      entryCard.dataset.entryId = entry.id;

      entryCard.innerHTML = `
        <h3 class="entry-title">${entry.title}</h3>
        <div class="entry-meta">${formattedDate}</div>
        <div class="entry-preview">${contentPreview}</div>
        <div class="entry-tags">${tagsHtml}</div>
      `;

      entryCard.addEventListener('click', () => {
        showEntryDetail(entry.id);
      });

      entriesContainer.appendChild(entryCard);
    });
  }

  async function loadEntries() {
    entriesContainer.innerHTML = '<p class="loading-placeholder">Loading entries...</p>';
    const entries = await fetchEntries();
    renderEntries(entries);
  }

  async function showEntryDetail(entryId) {
    entryContent.innerHTML = '<p class="loading-placeholder">Loading entry...</p>';
    showSection(entryDetailSection);

    const entry = await fetchEntry(entryId);
    if (!entry) {
      entryContent.innerHTML = '<p>Error loading entry. Please try again.</p>';
      return;
    }

    // Format the date
    const date = new Date(entry.created_at);
    const formattedDate = date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric'
    });

    // Create tags HTML
    const tagsHtml = entry.tags && entry.tags.length
      ? entry.tags.map(tag => `<span class="tag">${tag}</span>`).join('')
      : '';

    entryContent.innerHTML = `
      <h2>${entry.title}</h2>
      <div id="detail-meta">
        <p>${formattedDate}</p>
        <div class="entry-tags">${tagsHtml}</div>
      </div>
      <div id="detail-content">${entry.content.replace(/\n/g, '<br>')}</div>
    `;
  }

  // Event Listeners for Navigation
  newEntryBtn.addEventListener('click', (e) => {
    e.preventDefault();
    // Reset the form when showing it
    journalForm.reset();
    showSection(entryFormSection);
  });

  viewEntriesBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showSection(entryListSection);
    loadEntries();
  });

  searchBtn.addEventListener('click', (e) => {
    e.preventDefault();
    showSection(searchSection);
  });

  welcomeNewEntryBtn.addEventListener('click', () => {
    // Reset the form when showing it
    journalForm.reset();
    showSection(entryFormSection);
  });

  // Form submissions
  journalForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const titleInput = document.getElementById('title');
    const contentInput = document.getElementById('content');
    const tagsInput = document.getElementById('tags');

    // Validate input
    if (!titleInput.value.trim()) {
      alert('Please enter a title for your journal entry.');
      titleInput.focus();
      return;
    }

    if (!contentInput.value.trim()) {
      alert('Please enter content for your journal entry.');
      contentInput.focus();
      return;
    }

    // Parse tags
    const tags = tagsInput.value.trim()
      ? tagsInput.value.split(',').map(tag => tag.trim())
      : [];

    const entryData = {
      title: titleInput.value.trim(),
      content: contentInput.value.trim(),
      tags: tags
    };

    // Disable form during submission
    const submitButton = journalForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'Saving...';

    try {
      const result = await createEntry(entryData);
      if (result) {
        alert('Journal entry created successfully!');
        journalForm.reset();
        showSection(entryListSection);
        loadEntries();
      } else {
        alert('Failed to create journal entry. Please try again.');
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = 'Save Entry';
    }
  });

  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    alert('Search functionality will be implemented in the next phase');
    // In the future: performSearch(searchQuery, isSemanticSearch);
  });

  // Entry Detail Navigation
  document.getElementById('back-to-list').addEventListener('click', () => {
    showSection(entryListSection);
    loadEntries();
  });
});
