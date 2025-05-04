// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
  // Navigation elements
  const newEntryBtn = document.getElementById('new-entry-btn');
  const viewEntriesBtn = document.getElementById('view-entries-btn');
  const searchBtn = document.getElementById('search-btn');
  const welcomeNewEntryBtn = document.getElementById('welcome-new-entry');
  const newEntryLink = document.getElementById('new-entry-link');
  const searchLink = document.getElementById('search-link');

  // Markdown editor instance
  let markdownEditor = null;

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

  // Check hash fragment immediately
  const handleHashNavigation = () => {
    console.log("Checking URL hash:", window.location.hash);
    const hash = window.location.hash;

    if (hash === '#new-entry' && entryFormSection) {
      console.log("Hash navigation: displaying new entry form");
      if (journalForm) journalForm.reset();
      showSection(entryFormSection);
      return true;
    } else if (hash === '#search' && searchSection) {
      console.log("Hash navigation: displaying search section");
      showSection(searchSection);
      return true;
    }
    return false;
  };

  // Handle hash changes
  window.addEventListener('hashchange', handleHashNavigation);

  // Process hash on initial load
  const hashHandled = handleHashNavigation();

  // Notification & dialog utility functions
  const notifications = {
    show(message, type = 'info', duration = 5000) {
      // Create notification element
      const notification = document.createElement('div');
      notification.className = `notification ${type}`;
      notification.textContent = message;

      // Add to DOM
      document.body.appendChild(notification);

      // Auto remove after duration
      setTimeout(() => {
        notification.style.animation = 'fade-out 0.5s forwards';
        setTimeout(() => notification.remove(), 500);
      }, duration);

      return notification;
    },

    success(message, duration = 5000) {
      return this.show(message, 'success', duration);
    },

    error(message, duration = 7000) {
      return this.show(message, 'error', duration);
    },

    info(message, duration = 5000) {
      return this.show(message, 'info', duration);
    },

    warning(message, duration = 6000) {
      return this.show(message, 'warning', duration);
    }
  };

  // Confirmation dialog utility
  function showConfirmDialog(options) {
    return new Promise((resolve) => {
      const defaults = {
        title: 'Confirm Action',
        message: 'Are you sure you want to proceed?',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        confirmClass: 'btn',
        cancelClass: 'btn'
      };

      const settings = { ...defaults, ...options };

      // Create overlay and modal
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay';

      const modal = document.createElement('div');
      modal.className = 'modal';

      // Modal content
      modal.innerHTML = `
        <div class="modal-header">
          <h3 class="modal-title">${settings.title}</h3>
        </div>
        <div class="modal-body">
          <p>${settings.message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel ${settings.cancelClass}">${settings.cancelText}</button>
          <button class="btn-confirm ${settings.confirmClass}">${settings.confirmText}</button>
        </div>
      `;

      // Add to DOM
      overlay.appendChild(modal);
      document.body.appendChild(overlay);

      // Handle button clicks
      const confirmBtn = modal.querySelector('.btn-confirm');
      const cancelBtn = modal.querySelector('.btn-cancel');

      confirmBtn.addEventListener('click', () => {
        overlay.remove();
        resolve(true);
      });

      cancelBtn.addEventListener('click', () => {
        overlay.remove();
        resolve(false);
      });
    });
  }

  // Enhanced loading indicator
  function showLoadingIndicator(container, message = 'Loading...') {
    container.innerHTML = `
      <div class="loading-container">
        <div class="loading-spinner"></div>
        <span class="loading-text">${message}</span>
      </div>
    `;
  }

  // Hide loading indicator
  function hideLoadingIndicator(container) {
    const loadingContainer = container.querySelector('.loading-container');
    if (loadingContainer) {
      container.removeChild(loadingContainer);
    }
  }

  // Expose these utilities to make them available to other scripts like settings.js
  // This needs to happen AFTER the functions are defined
  window.showLoadingIndicator = showLoadingIndicator;
  window.hideLoadingIndicator = hideLoadingIndicator;
  window.showConfirmDialog = showConfirmDialog;
  window.notifications = notifications;

  // Navigation functions
  function showSection(section) {
    if (!section) return;

    // Hide all sections if they exist
    [welcomeSection, entryFormSection, entryListSection, entryDetailSection, searchSection]
      .filter(s => s) // Filter out null elements
      .forEach(s => {
        s.classList.remove('active');
        s.classList.add('hidden');
      });

    // Show the requested section
    section.classList.remove('hidden');
    section.classList.add('active');

    // Initialize markdown editor when showing the form
    if (section === entryFormSection) {
      initMarkdownEditor();
    }
  }

  // Initialize Markdown Editor
  function initMarkdownEditor() {
    const contentInput = document.getElementById('content');
    if (!contentInput) return;

    // If editor is already initialized, don't recreate it
    if (markdownEditor) return;

    // Initialize EasyMDE with configuration options
    markdownEditor = new EasyMDE({
      element: contentInput,
      spellChecker: true,
      autosave: {
        enabled: true,
        delay: 5000,
        uniqueId: 'journal-entry-content'
      },
      placeholder: 'Write your journal entry here...',
      toolbar: [
        'bold', 'italic', 'heading', '|',
        'quote', 'unordered-list', 'ordered-list', '|',
        'link', 'image', 'code', '|',
        'preview', 'side-by-side', 'fullscreen', '|',
        'guide'
      ],
      status: ['autosave', 'lines', 'words', 'cursor'],
      previewRender: function(plainText) {
        // Custom preview rendering that matches the app's markdown formatting
        return formatContent(plainText);
      }
    });
  }

  // Improved format content function to better handle markdown
  function formatContent(content) {
    // If we're in a browser environment, use the marked library for advanced markdown rendering
    if (typeof marked !== 'undefined') {
      try {
        // Configure marked options for advanced markdown features
        marked.setOptions({
          gfm: true, // GitHub Flavored Markdown
          breaks: true, // Convert line breaks to <br>
          headerIds: true, // Generate IDs for headers
          mangle: false, // Don't escape HTML
          tables: true, // Enable GFM tables
          taskLists: true, // Enable task lists
          smartLists: true, // Better list behavior
          smartypants: true, // Prettier quotes and dashes
          highlight: function(code, lang) {
            // Use highlight.js for syntax highlighting if available
            if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
              try {
                return hljs.highlight(code, { language: lang }).value;
              } catch (e) {
                console.error('Highlight.js error:', e);
              }
            }
            return code; // Fallback to no highlighting
          }
        });

        // Parse content with marked
        const parsed = marked.parse(content);

        // Apply syntax highlighting to any code blocks that might not have language specified
        if (typeof hljs !== 'undefined') {
          setTimeout(() => {
            document.querySelectorAll('pre code').forEach((block) => {
              if (!block.className.includes('hljs')) {
                hljs.highlightElement(block);
              }
            });
          }, 0);
        }

        return parsed;
      } catch (error) {
        console.error('Failed to use markdown parser:', error);
        // Fall back to basic formatting if parser fails
      }
    }

    // Basic formatting (fallback) - convert newlines to <br> and handle basic markdown
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

  // API Functions with improved error handling
  async function fetchEntries(limit = 10, offset = 0) {
    try {
      const response = await fetch(`/entries/?limit=${limit}&offset=${offset}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error ${response.status}: Failed to fetch entries`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch entries:', error);
      notifications.error(`Failed to load entries: ${error.message}`);
      return [];
    }
  }

  async function fetchEntry(entryId) {
    try {
      const response = await fetch(`/entries/${entryId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error ${response.status}: Entry not found`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to fetch entry ${entryId}:`, error);
      notifications.error(`Failed to load entry: ${error.message}`);
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
        throw new Error(errorData.message || `Error ${response.status}: Failed to create entry`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create entry:', error);
      notifications.error(`Failed to create entry: ${error.message}`);
      return null;
    }
  }

  async function deleteEntry(entryId) {
    try {
      const response = await fetch(`/entries/${entryId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error ${response.status}: Failed to delete entry`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to delete entry ${entryId}:`, error);
      notifications.error(`Failed to delete entry: ${error.message}`);
      return null;
    }
  }

  async function updateEntry(entryId, updateData) {
    try {
      const response = await fetch(`/entries/${entryId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error ${response.status}: Failed to update entry`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to update entry ${entryId}:`, error);
      notifications.error(`Failed to update entry: ${error.message}`);
      return null;
    }
  }

  // Update the existing searchEntries function with improved error handling
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
          const errorData = await response.json();
          throw new Error(errorData.message || `Error ${response.status}: Search failed`);
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
          const errorData = await response.json();
          throw new Error(errorData.message || `Error ${response.status}: Search failed`);
        }

        return await response.json();
      }
    } catch (error) {
      console.error('Failed to search entries:', error);

      // Specific error message for semantic search when Ollama might not be running
      if (options.semantic && error.message.includes('500')) {
        notifications.error('Semantic search failed. Please ensure Ollama is running on your system.');
      } else {
        notifications.error(`Search failed: ${error.message}`);
      }

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
      notifications.error(`Failed to fetch tags: ${error.message}`);
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
    showLoadingIndicator(entriesContainer, 'Loading your journal entries...');

    const entries = await fetchEntries();
    renderEntries(entries);

    if (entries.length === 0) {
      notifications.info('No journal entries found. Create your first entry to get started!');
    }
  }

  async function showEntryDetail(entryId) {
    showLoadingIndicator(entryContent, 'Loading entry details...');
    showSection(entryDetailSection);

    const entry = await fetchEntry(entryId);
    if (!entry) {
      entryContent.innerHTML = `
        <div class="error-container">
          <p>Failed to load this journal entry.</p>
          <button class="btn" id="retry-load-entry">Retry</button>
        </div>
      `;

      document.getElementById('retry-load-entry').addEventListener('click', () => {
        showEntryDetail(entryId);
      });

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
      : '<em>No tags</em>';

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
        <button id="delete-entry" class="btn btn-danger" data-id="${entry.id}">Delete</button>
      </div>
      <div id="entry-summary" class="hidden">
        <h3>Entry Summary</h3>
        <div id="summary-content"></div>
      </div>
    `;

    // Add event listeners for the entry action buttons
    document.getElementById('edit-entry').addEventListener('click', () => {
      editEntry(entry);
    });

    document.getElementById('summarize-entry').addEventListener('click', () => {
      summarizeEntry(entry.id);
    });

    document.getElementById('delete-entry').addEventListener('click', async () => {
      const confirmed = await showConfirmDialog({
        title: 'Delete Entry',
        message: 'Are you sure you want to delete this journal entry? This action cannot be undone.',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        confirmClass: 'btn btn-danger',
      });

      if (confirmed) {
        const result = await deleteEntry(entry.id);
        if (result) {
          notifications.success('Journal entry deleted successfully');
          showSection(entryListSection);
          loadEntries();
        }
      }
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
    // If EasyMDE is available and we're in a browser environment, use its markdown conversion
    if (typeof EasyMDE !== 'undefined') {
      try {
        // Use EasyMDE's built-in markdown parser if available
        return EasyMDE.prototype.markdown(content);
      } catch (error) {
        console.error('Failed to use EasyMDE markdown parser:', error);
        // Fall back to basic formatting if EasyMDE parser fails
      }
    }

    // Basic formatting (fallback) - convert newlines to <br> and handle basic markdown
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
    const tagsInput = document.getElementById('tags');

    titleInput.value = entry.title;
    tagsInput.value = entry.tags.join(', ');

    // Switch to the form view
    showSection(entryFormSection);

    // After the section is shown, the markdown editor should be initialized
    // Set the content to the editor instead of directly to the textarea
    if (markdownEditor) {
      markdownEditor.value(entry.content);
    } else {
      // Fallback in case the editor isn't initialized yet
      document.getElementById('content').value = entry.content;
    }

    // Add hidden input for entry ID to track that we're editing an existing entry
    let entryIdInput = document.getElementById('entry-id');
    if (!entryIdInput) {
      entryIdInput = document.createElement('input');
      entryIdInput.type = 'hidden';
      entryIdInput.id = 'entry-id';
      journalForm.appendChild(entryIdInput);
    }
    entryIdInput.value = entry.id;

    // Update submit button text to indicate we're editing
    const submitButton = journalForm.querySelector('button[type="submit"]');
    submitButton.textContent = 'Update Entry';
  }

  async function summarizeEntry(entryId) {
    const summarySection = document.getElementById('entry-summary');
    const summaryContent = document.getElementById('summary-content');

    summarySection.classList.remove('hidden');
    showLoadingIndicator(summaryContent, 'Generating summary with AI...');

    try {
      const response = await fetch(`/entries/${entryId}/summarize`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `Error ${response.status}: Failed to generate summary`);
      }

      const summary = await response.json();

      // Display the summary
      summaryContent.innerHTML = `
        <p><strong>Summary:</strong> ${summary.summary}</p>
        <p><strong>Key Topics:</strong> ${summary.key_topics.join(', ')}</p>
        <p><strong>Detected Mood:</strong> ${summary.mood}</p>
      `;

      notifications.success('Summary generated successfully');
    } catch (error) {
      console.error('Summary error:', error);

      // Specific error message for Ollama connection issues
      if (error.message.includes('500')) {
        summaryContent.innerHTML = `
          <div class="error-container">
            <p>Failed to generate summary. Please ensure Ollama is running on your system.</p>
            <button class="btn" id="retry-summary">Retry</button>
          </div>
        `;
        notifications.error('Failed to generate summary: Ollama service may not be available');
      } else {
        summaryContent.innerHTML = `
          <div class="error-container">
            <p>Failed to generate summary: ${error.message}</p>
            <button class="btn" id="retry-summary">Retry</button>
          </div>
        `;
        notifications.error(`Failed to generate summary: ${error.message}`);
      }

      // Add retry button functionality
      document.getElementById('retry-summary')?.addEventListener('click', () => {
        summarizeEntry(entryId);
      });
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

  // Event Listeners for Navigation - Only add if elements exist
  if (newEntryBtn) {
    newEntryBtn.addEventListener('click', (e) => {
      e.preventDefault();
      // Reset the form when showing it
      if (journalForm) journalForm.reset();
      showSection(entryFormSection);
    });
  }

  if (viewEntriesBtn) {
    viewEntriesBtn.addEventListener('click', (e) => {
      e.preventDefault();
      showSection(entryListSection);
      loadEntries();
    });
  }

  if (searchBtn) {
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
  }

  // Handle navigation links on settings page
  if (newEntryLink) {
    newEntryLink.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = '/?action=new';
    });
  }

  if (searchLink) {
    searchLink.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = '/?action=search';
    });
  }

  if (welcomeNewEntryBtn) {
    welcomeNewEntryBtn.addEventListener('click', () => {
      // Reset the form when showing it
      if (journalForm) journalForm.reset();
      showSection(entryFormSection);
    });
  }

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

  // Form submissions with improved error handling
  if (journalForm) {
    journalForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const titleInput = document.getElementById('title');
      const tagsInput = document.getElementById('tags');
      const entryIdInput = document.getElementById('entry-id');

      // Get content from markdown editor if available, otherwise from the textarea
      let content = '';
      if (markdownEditor) {
        content = markdownEditor.value();
      } else {
        const contentInput = document.getElementById('content');
        content = contentInput.value;
      }

      // Validate input
      if (!titleInput.value.trim()) {
        notifications.warning('Please enter a title for your journal entry.');
        titleInput.focus();
        return;
      }

      if (!content.trim()) {
        notifications.warning('Please enter content for your journal entry.');
        // Focus the markdown editor if available
        if (markdownEditor) {
          try {
            // Give time for the UI to update before focusing
            setTimeout(() => {
              if (markdownEditor.codemirror) {
                markdownEditor.codemirror.focus();
                // Move cursor to beginning of editor
                markdownEditor.codemirror.setCursor(0, 0);
              }
            }, 100);
          } catch (e) {
            console.error('Failed to focus editor:', e);
          }
        }
        return;
      }

      // Parse tags
      const tags = tagsInput.value.trim()
        ? tagsInput.value.split(',').map(tag => tag.trim())
        : [];

      const entryData = {
        title: titleInput.value.trim(),
        content: content.trim(),
        tags: tags
      };

      // Disable form during submission
      const submitButton = journalForm.querySelector('button[type="submit"]');
      const isUpdate = entryIdInput && entryIdInput.value;
      const originalButtonText = submitButton.textContent;
      submitButton.disabled = true;
      submitButton.innerHTML = `<div class="loading-spinner"></div> ${isUpdate ? 'Updating' : 'Saving'}...`;

      try {
        let result;

        if (isUpdate) {
          // Update existing entry
          result = await updateEntry(entryIdInput.value, entryData);
          if (result) {
            notifications.success('Journal entry updated successfully!');
            // Reset the form and remove the entry ID
            journalForm.reset();
            entryIdInput.remove();

            // Show the updated entry
            showEntryDetail(result.id);
          }
        } else {
          // Create new entry
          result = await createEntry(entryData);
          if (result) {
            notifications.success('Journal entry created successfully!');
            journalForm.reset();
            showSection(entryListSection);
            loadEntries();
          }
        }

        if (!result) {
          throw new Error(`Failed to ${isUpdate ? 'update' : 'create'} journal entry.`);
        }

        // Clear the markdown editor content
        if (markdownEditor) {
          markdownEditor.value('');
          // Also clear autosave data
          if (typeof localStorage !== 'undefined') {
            localStorage.removeItem('journal-entry-content');
          }
        }
      } catch (error) {
        notifications.error(`Error: ${error.message}`);
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
      }
    });
  }

  // Enhanced search form submission
  if (searchForm) {
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

      // Validate date range if both dates are provided
      if (dateFrom && dateTo && new Date(dateFrom) > new Date(dateTo)) {
        notifications.warning("The 'from date' cannot be after the 'to date'. Please adjust your date range.");
        return;
      }

      // If using semantic search, warn user if Ollama might not be running
      if (isSemanticSearch) {
        const warning = document.createElement('div');
        warning.classList.add('info-banner');
        warning.innerHTML = 'Using semantic search - this requires Ollama to be running.';
        searchResults.innerHTML = '';
        searchResults.appendChild(warning);

        setTimeout(() => {
          performSearch(searchQuery, searchOptions);
        }, 500);
      } else {
        performSearch(searchQuery, searchOptions);
      }
    });
  }

  // Entry Detail Navigation
  const backToListBtn = document.getElementById('back-to-list');
  if (backToListBtn) {
    backToListBtn.addEventListener('click', () => {
      showSection(entryListSection);
      loadEntries();
    });
  }

  // API Connection Status Check
  async function checkApiConnection() {
    try {
      const response = await fetch('/api/info', {
        method: 'GET',
        headers: { 'Cache-Control': 'no-cache' }
      });

      if (!response.ok) {
        throw new Error('API connection failed');
      }

      return true;
    } catch (error) {
      console.error('API connection check failed:', error);

      // Show a persistent connection error message
      const connectionError = document.createElement('div');
      connectionError.className = 'connection-error';
      connectionError.innerHTML = `
        <div class="connection-error-content">
          <h3>Connection Error</h3>
          <p>Cannot connect to the journal API. Please ensure the server is running.</p>
          <button id="retry-connection" class="btn">Retry Connection</button>
        </div>
      `;
      document.body.appendChild(connectionError);

      // Add retry button functionality
      document.getElementById('retry-connection').addEventListener('click', async () => {
        connectionError.innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><span>Checking connection...</span></div>';

        const isConnected = await checkApiConnection();
        if (isConnected) {
          connectionError.remove();
          notifications.success('Connection restored');
          loadEntries();
        } else {
          // If still not connected, restore the error message
          connectionError.innerHTML = `
            <div class="connection-error-content">
              <h3>Connection Error</h3>
              <p>Cannot connect to the journal API. Please ensure the server is running.</p>
              <button id="retry-connection" class="btn">Retry Connection</button>
            </div>
          `;

          // Re-attach event listener to new button
          document.getElementById('retry-connection').addEventListener('click', () => {
            checkApiConnection();
          });
        }
      });

      return false;
    }
  }

  // Check API connection when the app starts (only if we're on the main journal page)
  if (welcomeSection || entryListSection || entryFormSection) {
    checkApiConnection().then(isConnected => {
      if (isConnected && entryListSection) {
        // Initialize the application
        loadEntries();
      }
    });
  }

  // Check if we need to handle URL actions (e.g., from settings page navigation)
  const urlParams = new URLSearchParams(window.location.search);
  const action = urlParams.get('action');
  const hash = window.location.hash;

  if (action === 'new' && entryFormSection) {
    if (journalForm) journalForm.reset();
    showSection(entryFormSection);
  } else if (action === 'search' && searchSection) {
    showSection(searchSection);
  } else if (hash === '#new-entry' && entryFormSection) {
    // Handle hash-based navigation from settings page
    if (journalForm) journalForm.reset();
    showSection(entryFormSection);
  } else if (hash === '#search' && searchSection) {
    // Handle hash-based navigation from settings page
    showSection(searchSection);
  }
});
