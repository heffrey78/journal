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
  const searchResults = document.getElementById('search-results');

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

  async function searchEntries(query, options = {}) {
    try {
      // Handle empty query when using filters
      const hasFilters = options.date_from || options.date_to || (options.tags && options.tags.length > 0);
      const queryParam = query.trim() ? query : hasFilters ? "" : " "; // Use empty string for filter-only searches

      // Handle basic search vs advanced search
      if (Object.keys(options).length <= 1 && options.semantic !== undefined) {
        // Simple search with only semantic option
        const url = options.semantic
          ? `/entries/search/?query=${encodeURIComponent(queryParam)}&semantic=true`
          : `/entries/search/?query=${encodeURIComponent(queryParam)}`;

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Error searching entries: ${response.status}`);
        }
        return await response.json();
      } else {
        // Advanced search with POST
        const searchParams = {
          query: queryParam,
          ...options
        };

        const response = await fetch('/entries/search/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(searchParams),
        });

        if (!response.ok) {
          throw new Error(`Error searching entries: ${response.status}`);
        }
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to search entries:', error);
      return [];
    }
  }

  async function fetchAllTags() {
    try {
      const response = await fetch('/tags/');
      if (!response.ok) {
        throw new Error(`Error fetching tags: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch tags:', error);
      return [];
    }
  }

  // UI Functions
  function renderEntries(entries, container = entriesContainer) {
    container.innerHTML = '';

    if (!entries || entries.length === 0) {
      container.innerHTML = '<p>No journal entries found.</p>';
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

      container.appendChild(entryCard);
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

    // Format content - respect newlines and markdown-style formatting
    const formattedContent = formatContent(entry.content);

    // Create tags HTML with clickable tags for filtering
    const tagsHtml = entry.tags && entry.tags.length
      ? entry.tags.map(tag => `<span class="tag clickable-tag" data-tag="${tag}">${tag}</span>`).join('')
      : '';

    entryContent.innerHTML = `
      <h2>${entry.title}</h2>
      <div id="detail-meta">
        <p>Created: ${formattedDate}</p>
        ${entry.updated_at ? `<p>Updated: ${formatDate(entry.updated_at)}</p>` : ''}
        <div class="entry-tags">${tagsHtml}</div>
      </div>
      <div id="detail-content">${formattedContent}</div>
      <div class="entry-actions detail-actions">
        <button id="edit-entry" class="btn" data-id="${entry.id}">Edit Entry</button>
        <button id="summarize-entry" class="btn" data-id="${entry.id}">Summarize</button>
      </div>
      <div id="entry-summary" class="hidden">
        <h3>Entry Summary</h3>
        <div id="summary-content"></div>
      </div>
    `;

    // Add event listeners for the new buttons
    document.getElementById('edit-entry').addEventListener('click', () => {
      editEntry(entry);
    });

    document.getElementById('summarize-entry').addEventListener('click', () => {
      summarizeEntry(entry.id);
    });

    // Make tags clickable to filter by tag
    entryContent.querySelectorAll('.clickable-tag').forEach(tagElement => {
      tagElement.addEventListener('click', () => {
        const tag = tagElement.dataset.tag;
        showTaggedEntries(tag);
      });
    });
  }

  function formatContent(content) {
    // Basic formatting - convert newlines to <br> and handle basic markdown
    let formatted = content
      .replace(/\n/g, '<br>')
      // Format headings (# Heading)
      .replace(/^# (.+)$/gm, '<h2>$1</h2>')
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      .replace(/^### (.+)$/gm, '<h4>$1</h4>')
      // Format bold (**bold**)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Format italic (*italic*)
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Format code blocks (```code```)
      .replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>');

    return formatted;
  }

  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric'
    });
  }

  async function editEntry(entry) {
    // Populate the form with entry data
    const titleInput = document.getElementById('title');
    const contentInput = document.getElementById('content');
    const tagsInput = document.getElementById('tags');

    titleInput.value = entry.title;
    contentInput.value = entry.content;
    tagsInput.value = entry.tags.join(', ');

    // Switch to the form view
    showSection(entryFormSection);

    // Note: In future commits, this would be extended to handle updating existing entries
    // rather than creating new ones
  }

  async function summarizeEntry(entryId) {
    const summarySection = document.getElementById('entry-summary');
    const summaryContent = document.getElementById('summary-content');

    summaryContent.innerHTML = '<p>Generating summary...</p>';
    summarySection.classList.remove('hidden');

    try {
      const response = await fetch(`/entries/${entryId}/summarize`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Error generating summary: ${response.status}`);
      }

      const summary = await response.json();

      // Display the summary
      summaryContent.innerHTML = `
        <p><strong>Summary:</strong> ${summary.summary}</p>
        <p><strong>Key Topics:</strong> ${summary.key_topics.join(', ')}</p>
        <p><strong>Detected Mood:</strong> ${summary.mood}</p>
      `;
    } catch (error) {
      summaryContent.innerHTML = `<p>Failed to generate summary: ${error.message}</p>`;
      console.error('Summary error:', error);
    }
  }

  async function performSearch(query, options = {}) {
    searchResults.innerHTML = '<p class="loading-placeholder">Searching...</p>';

    // Check if we have any search criteria (either query or filters)
    const hasFilters = options.date_from || options.date_to || (options.tags && options.tags.length > 0);

    // If no query and no filters, show error
    if (!query.trim() && !hasFilters) {
      searchResults.innerHTML = '<p>Please enter search terms or select filters.</p>';
      return;
    }

    const results = await searchEntries(query, options);

    // Create appropriate heading based on search criteria
    let headingText = '';
    if (query.trim()) {
      // If there's a query, show it in the heading
      const searchTypeText = options.semantic ? 'semantic search' : 'text search';
      headingText = `Search Results for "${query}" (${searchTypeText})`;
    } else {
      // If only using filters, show that in the heading
      headingText = "Filtered Journal Entries";
    }

    // Generate filter information display
    let filterInfo = '';
    if (options.date_from || options.date_to) {
      const dateRange = [];
      if (options.date_from) dateRange.push(`from ${options.date_from}`);
      if (options.date_to) dateRange.push(`to ${options.date_to}`);
      filterInfo += `<p>Date range: ${dateRange.join(' ')}</p>`;
    }

    if (options.tags && options.tags.length) {
      filterInfo += `<p>Tags: ${options.tags.join(', ')}</p>`;
    }

    searchResults.innerHTML = `
      <h3>${headingText}</h3>
      ${filterInfo}
      <div id="search-entries-container"></div>
    `;

    const searchEntriesContainer = document.getElementById('search-entries-container');
    renderEntries(results, searchEntriesContainer);
  }

  async function showTaggedEntries(tag) {
    showSection(entryListSection);
    entriesContainer.innerHTML = `<p class="loading-placeholder">Loading entries tagged with "${tag}"...</p>`;

    try {
      const response = await fetch(`/tags/${encodeURIComponent(tag)}/entries`);
      if (!response.ok) {
        throw new Error(`Error fetching entries with tag ${tag}: ${response.status}`);
      }
      const entries = await response.json();

      // Add heading to show we're filtering by tag
      entriesContainer.innerHTML = `<h3>Entries tagged with "${tag}"</h3><div id="tagged-entries"></div>`;
      const taggedEntriesContainer = document.getElementById('tagged-entries');
      renderEntries(entries, taggedEntriesContainer);
    } catch (error) {
      entriesContainer.innerHTML = `<p>Error loading entries with tag "${tag}": ${error.message}</p>`;
      console.error('Error fetching tagged entries:', error);
    }
  }

  // Load tags for search dropdown
  async function loadSearchTags() {
    const tagSelect = document.getElementById('search-tags');
    if (!tagSelect) return;

    // Clear existing options
    tagSelect.innerHTML = '';

    // Add loading option
    const loadingOption = document.createElement('option');
    loadingOption.textContent = 'Loading tags...';
    loadingOption.disabled = true;
    loadingOption.selected = true;
    tagSelect.appendChild(loadingOption);

    // Fetch tags
    const tags = await fetchAllTags();

    // Remove loading option
    tagSelect.removeChild(loadingOption);

    // Add tags as options
    if (tags.length === 0) {
      const noTagsOption = document.createElement('option');
      noTagsOption.textContent = 'No tags available';
      noTagsOption.disabled = true;
      tagSelect.appendChild(noTagsOption);
    } else {
      tags.forEach(tag => {
        const option = document.createElement('option');
        option.value = tag;
        option.textContent = tag;
        tagSelect.appendChild(option);
      });
    }
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

    // If advanced search is visible and we haven't loaded tags yet
    const advancedSearchOptions = document.getElementById('advanced-search-options');
    const tagSelect = document.getElementById('search-tags');

    if (advancedSearchOptions && !advancedSearchOptions.classList.contains('hidden') &&
        tagSelect && tagSelect.options.length <= 1) {
      loadSearchTags();
    }
  });

  welcomeNewEntryBtn.addEventListener('click', () => {
    // Reset the form when showing it
    journalForm.reset();
    showSection(entryFormSection);
  });

  // Advanced search toggle
  const toggleAdvancedSearch = document.getElementById('toggle-advanced-search');
  const advancedSearchOptions = document.getElementById('advanced-search-options');

  if (toggleAdvancedSearch && advancedSearchOptions) {
    toggleAdvancedSearch.addEventListener('click', (e) => {
      e.preventDefault();
      const isHidden = advancedSearchOptions.classList.contains('hidden');

      if (isHidden) {
        advancedSearchOptions.classList.remove('hidden');
        toggleAdvancedSearch.textContent = 'Hide advanced options';
        // Load tags when showing advanced options
        loadSearchTags();
      } else {
        advancedSearchOptions.classList.add('hidden');
        toggleAdvancedSearch.textContent = 'Show advanced options';
      }
    });
  }

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

  // Enhanced search form submission
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const searchQuery = document.getElementById('search-query').value;
    const isSemanticSearch = document.getElementById('semantic-search')?.checked || false;

    // Get advanced search options
    const dateFrom = document.getElementById('date-from')?.value || null;
    const dateTo = document.getElementById('date-to')?.value || null;

    // Get selected tags (multiple select)
    const tagsSelect = document.getElementById('search-tags');
    const selectedTags = tagsSelect ?
      Array.from(tagsSelect.selectedOptions).map(option => option.value) :
      [];

    // Build search options
    const searchOptions = {
      semantic: isSemanticSearch
    };

    if (dateFrom) searchOptions.date_from = dateFrom;
    if (dateTo) searchOptions.date_to = dateTo;
    if (selectedTags.length > 0) searchOptions.tags = selectedTags;

    performSearch(searchQuery, searchOptions);
  });

  // Entry Detail Navigation
  document.getElementById('back-to-list').addEventListener('click', () => {
    showSection(entryListSection);
    loadEntries();
  });
});
