/**
 * Settings page functionality for Journal App
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Settings page loaded");

    // Initialize tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            console.log("Tab clicked:", button.dataset.target);
            // Deactivate all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Activate the clicked tab
            button.classList.add('active');
            const targetId = button.dataset.target;
            document.getElementById(targetId).classList.add('active');
        });
    });

    // Initialize settings form
    const llmConfigForm = document.getElementById('llm-config-form');
    console.log("Form element found:", !!llmConfigForm);

    const modelNameSelect = document.getElementById('model-name');
    const embeddingModelSelect = document.getElementById('embedding-model');
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = temperatureSlider.nextElementSibling;
    const maxTokensInput = document.getElementById('max-tokens');
    const maxRetriesInput = document.getElementById('max-retries');
    const retryDelayInput = document.getElementById('retry-delay');
    const systemPromptInput = document.getElementById('system-prompt');
    const testConnectionBtn = document.getElementById('test-connection');
    const resetDefaultsBtn = document.getElementById('reset-defaults');

    // Update temperature display when slider changes
    temperatureSlider.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });

    // Load available models
    async function loadAvailableModels() {
        try {
            console.log("Loading available models...");
            // Create a custom loading indicator we can see
            const loadingMessage = document.createElement('div');
            loadingMessage.className = 'loading-message';
            loadingMessage.style.background = '#f5f5f5';
            loadingMessage.style.padding = '10px';
            loadingMessage.style.margin = '10px 0';
            loadingMessage.style.borderRadius = '4px';
            loadingMessage.textContent = 'Loading available models...';
            llmConfigForm.prepend(loadingMessage);

            const response = await fetch('/config/available-models');
            console.log("API response status:", response.status);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to load models');
            }

            const data = await response.json();
            console.log("Available models data:", data);
            const models = data.models || [];

            if (models.length === 0) {
                console.log("No models returned from API");
                loadingMessage.textContent = 'No models found. Using defaults.';
                setTimeout(() => {
                    loadingMessage.remove();
                }, 3000);

                // Add a default option for fallback
                addDefaultModelOption(modelNameSelect);
                addDefaultModelOption(embeddingModelSelect);
                return;
            }

            // Populate model dropdowns
            populateModelOptions(modelNameSelect, models);
            populateModelOptions(embeddingModelSelect, models);

            console.log("Model dropdowns populated");
            loadingMessage.remove();
        } catch (error) {
            console.error("Error loading models:", error);
            alert('Failed to load models: ' + error.message);

            // Add a default option for fallback
            addDefaultModelOption(modelNameSelect);
            addDefaultModelOption(embeddingModelSelect);
        }
    }

    function populateModelOptions(selectElement, models) {
        console.log(`Populating ${selectElement.id} with ${models.length} models`);

        // Clear existing options
        selectElement.innerHTML = '';

        // Add models to dropdown
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            selectElement.appendChild(option);
        });

        // Log the resulting HTML for debugging
        console.log(`${selectElement.id} HTML:`, selectElement.innerHTML);
    }

    function addDefaultModelOption(selectElement) {
        selectElement.innerHTML = '';
        const defaultModels = [
            'qwen3:latest',
            'llama3:latest',
            'mistral:latest',
            'nomic-embed-text:latest'
        ];

        defaultModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model + ' (recommended)';
            selectElement.appendChild(option);
        });
    }

    // Load current configuration
    async function loadCurrentConfig() {
        try {
            console.log("Loading current configuration...");
            const response = await fetch('/config/llm');
            console.log("Config API response status:", response.status);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to load configuration');
            }

            const config = await response.json();
            console.log("Current config data:", config);

            // Store the config globally so we can access prompt_types later
            window.currentConfig = config;

            // Populate form with current values
            populateFormWithConfig(config);
        } catch (error) {
            console.error("Error loading configuration:", error);
            alert('Failed to load configuration: ' + error.message);
        }
    }

    function populateFormWithConfig(config) {
        console.log("Populating form with config:", config);

        // Set form values from config
        if (modelNameSelect.querySelector(`option[value="${config.model_name}"]`)) {
            modelNameSelect.value = config.model_name;
        } else {
            // Add the current model if it's not in the list
            const option = document.createElement('option');
            option.value = config.model_name;
            option.textContent = config.model_name;
            modelNameSelect.appendChild(option);
            modelNameSelect.value = config.model_name;
        }

        if (embeddingModelSelect.querySelector(`option[value="${config.embedding_model}"]`)) {
            embeddingModelSelect.value = config.embedding_model;
        } else {
            // Add the current model if it's not in the list
            const option = document.createElement('option');
            option.value = config.embedding_model;
            option.textContent = config.embedding_model;
            embeddingModelSelect.appendChild(option);
            embeddingModelSelect.value = config.embedding_model;
        }

        temperatureSlider.value = config.temperature;
        temperatureValue.textContent = config.temperature;
        maxTokensInput.value = config.max_tokens;
        maxRetriesInput.value = config.max_retries;
        retryDelayInput.value = config.retry_delay;
        systemPromptInput.value = config.system_prompt || '';

        console.log("Form populated with configuration");
    }

    // Save configuration
    async function saveConfig(event) {
        event.preventDefault();
        console.log("Saving configuration...");

        // Show saving indicator
        const saveButton = llmConfigForm.querySelector('button[type="submit"]');
        const originalText = saveButton.textContent;
        saveButton.disabled = true;
        saveButton.textContent = "Saving...";

        try {
            // Build configuration object from form
            const config = {
                model_name: modelNameSelect.value,
                embedding_model: embeddingModelSelect.value,
                temperature: parseFloat(temperatureSlider.value),
                max_tokens: parseInt(maxTokensInput.value),
                max_retries: parseInt(maxRetriesInput.value),
                retry_delay: parseFloat(retryDelayInput.value),
                system_prompt: systemPromptInput.value || null
            };

            // Add prompt types if they exist in the current data
            if (window.currentConfig && window.currentConfig.prompt_types) {
                config.prompt_types = window.currentConfig.prompt_types;
            }

            console.log("Config to save:", config);

            // Include the skip_validation parameter to avoid timeouts
            const response = await fetch('/config/llm?skip_validation=true', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config),
                // Set a longer timeout for the request
                signal: AbortSignal.timeout(30000) // 30 second timeout
            });

            console.log("Save config response status:", response.status);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to save configuration');
            }

            // Store the current config for future reference
            window.currentConfig = await response.json();

            // Show success message
            const successMsg = document.createElement('div');
            successMsg.className = 'success-message';
            successMsg.style.background = '#dff0d8';
            successMsg.style.color = '#3c763d';
            successMsg.style.padding = '10px';
            successMsg.style.margin = '10px 0';
            successMsg.style.borderRadius = '4px';
            successMsg.textContent = 'Configuration saved successfully!';

            // Insert after form and automatically remove after 3 seconds
            llmConfigForm.insertAdjacentElement('afterend', successMsg);
            setTimeout(() => {
                successMsg.remove();
            }, 3000);
        } catch (error) {
            console.error("Error saving configuration:", error);

            // Show error message
            const errorMsg = document.createElement('div');
            errorMsg.className = 'error-message';
            errorMsg.style.background = '#f2dede';
            errorMsg.style.color = '#a94442';
            errorMsg.style.padding = '10px';
            errorMsg.style.margin = '10px 0';
            errorMsg.style.borderRadius = '4px';
            errorMsg.textContent = 'Failed to save configuration: ' + error.message;

            // Insert after form
            llmConfigForm.insertAdjacentElement('afterend', errorMsg);
            setTimeout(() => {
                errorMsg.remove();
            }, 5000);
        } finally {
            // Restore button state
            saveButton.disabled = false;
            saveButton.textContent = originalText;
        }
    }

    // Test connection with current settings
    async function testConnection() {
        console.log("Testing connection...");

        // Build configuration object from form
        const config = {
            model_name: modelNameSelect.value,
            embedding_model: embeddingModelSelect.value
        };

        console.log("Testing with config:", config);

        try {
            alert('Testing connection to Ollama models...');

            // Make a simple test request to the model
            const response = await fetch('/config/llm', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            console.log("Test connection response status:", response.status);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Connection test failed');
            }

            alert('Connection successful! Models are working properly.');
        } catch (error) {
            console.error("Error testing connection:", error);
            alert('Connection test failed: ' + error.message);
        }
    }

    // Reset form to default values
    function resetToDefaults() {
        console.log("Resetting to defaults...");

        const confirmed = confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.');

        if (confirmed) {
            const defaultConfig = {
                model_name: 'qwen3:latest',
                embedding_model: 'nomic-embed-text:latest',
                temperature: 0.7,
                max_tokens: 1000,
                max_retries: 2,
                retry_delay: 1.0,
                system_prompt: null
            };

            populateFormWithConfig(defaultConfig);
            alert('Settings reset to defaults. Click Save to apply changes.');
        }
    }

    // Handle form submission
    llmConfigForm.addEventListener('submit', saveConfig);
    console.log("Form submit handler registered");

    // Handle test connection button
    testConnectionBtn.addEventListener('click', testConnection);
    console.log("Test connection handler registered");

    // Handle reset defaults button
    resetDefaultsBtn.addEventListener('click', resetToDefaults);
    console.log("Reset defaults handler registered");

    // Handle navigation links on settings page
    const newEntryLink = document.getElementById('new-entry-link');
    const searchLink = document.getElementById('search-link');

    if (newEntryLink) {
        newEntryLink.addEventListener('click', (e) => {
            e.preventDefault();
            // Redirect to index.html with section parameter that will be used by main.js
            window.location.href = '/static/index.html#new-entry';
        });
    }

    if (searchLink) {
        searchLink.addEventListener('click', (e) => {
            e.preventDefault();
            // Redirect to index.html with section parameter that will be used by main.js
            window.location.href = '/static/index.html#search';
        });
    }

    // Start loading data
    console.log("Initial data loading started");
    loadAvailableModels();
    loadCurrentConfig();
});
