// Chat Interface JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatSessionsList = document.getElementById('chat-sessions-list');
    const currentChatTitle = document.getElementById('current-chat-title');
    const newChatBtn = document.getElementById('new-chat-btn');
    const renameChatBtn = document.getElementById('rename-chat-btn');
    const deleteChatBtn = document.getElementById('delete-chat-btn');

    // Modals
    const renameModal = document.getElementById('rename-modal');
    const renameInput = document.getElementById('rename-input');
    const renameCancel = document.getElementById('rename-cancel');
    const renameConfirm = document.getElementById('rename-confirm');

    const deleteModal = document.getElementById('delete-modal');
    const deleteCancel = document.getElementById('delete-cancel');
    const deleteConfirm = document.getElementById('delete-confirm');

    // State
    let currentChatId = null;
    let chatSessions = [];
    let isTyping = false;
    let eventSource = null;

    // Load existing chat sessions when page loads
    loadChatSessions();

    // Event listeners
    chatForm.addEventListener('submit', sendMessage);
    newChatBtn.addEventListener('click', createNewChat);
    renameChatBtn.addEventListener('click', openRenameModal);
    deleteChatBtn.addEventListener('click', openDeleteModal);

    renameCancel.addEventListener('click', closeRenameModal);
    renameConfirm.addEventListener('click', renameChatSession);

    deleteCancel.addEventListener('click', closeDeleteModal);
    deleteConfirm.addEventListener('click', deleteChatSession);

    // Auto resize textarea as user types
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
    });

    // Functions
    async function loadChatSessions() {
        try {
            const response = await fetch('/api/chat/sessions');

            if (!response.ok) {
                throw new Error('Failed to load chat sessions');
            }

            const data = await response.json();
            chatSessions = data.sessions || [];

            renderChatSessions();

            // If we have sessions, load the most recent one
            if (chatSessions.length > 0) {
                loadChatSession(chatSessions[0].id);
            } else {
                // Otherwise, create a new one
                createNewChat();
            }
        } catch (error) {
            showNotification('Error loading chat sessions: ' + error.message, 'error');
            chatSessionsList.innerHTML = '<p class="error-text">Failed to load chat sessions</p>';
        }
    }

    function renderChatSessions() {
        if (chatSessions.length === 0) {
            chatSessionsList.innerHTML = '<p class="subtle-text">No chat sessions yet</p>';
            return;
        }

        chatSessionsList.innerHTML = '';
        chatSessions.forEach(session => {
            const element = document.createElement('div');
            element.className = `chat-session-item ${session.id === currentChatId ? 'active' : ''}`;
            element.dataset.sessionId = session.id;

            const title = document.createElement('div');
            title.className = 'chat-session-title';
            title.textContent = session.title || 'Untitled Chat';

            const date = document.createElement('div');
            date.className = 'chat-session-date';
            date.textContent = formatDate(session.updated_at || session.created_at);

            element.appendChild(title);
            element.appendChild(date);

            element.addEventListener('click', () => {
                loadChatSession(session.id);
            });

            chatSessionsList.appendChild(element);
        });
    }

    async function loadChatSession(sessionId) {
        try {
            const response = await fetch(`/api/chat/sessions/${sessionId}/messages`);

            if (!response.ok) {
                throw new Error('Failed to load chat messages');
            }

            const data = await response.json();
            currentChatId = sessionId;

            // Update active state in sidebar
            const allSessions = document.querySelectorAll('.chat-session-item');
            allSessions.forEach(item => {
                if (item.dataset.sessionId === sessionId) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });

            // Update chat title
            const currentSession = chatSessions.find(s => s.id === sessionId);
            currentChatTitle.textContent = currentSession?.title || 'Untitled Chat';

            // Render messages
            chatMessages.innerHTML = '';
            data.messages.forEach(message => {
                addMessageToUI(message);
            });

            // Scroll to bottom
            scrollToBottom();
        } catch (error) {
            showNotification('Error loading chat: ' + error.message, 'error');
        }
    }

    async function createNewChat() {
        try {
            const response = await fetch('/api/chat/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: 'New Conversation',
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create new chat session');
            }

            const session = await response.json();

            // Add to our sessions list
            chatSessions.unshift(session);

            // Re-render sidebar
            renderChatSessions();

            // Switch to this session
            currentChatId = session.id;
            currentChatTitle.textContent = session.title || 'New Conversation';

            // Clear messages panel
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h3>Welcome to Journal Chat</h3>
                    <p>Ask questions about your journal entries or start a conversation about your thoughts and reflections.</p>
                </div>
            `;
        } catch (error) {
            showNotification('Error creating chat: ' + error.message, 'error');
        }
    }

    async function sendMessage(event) {
        event.preventDefault();

        const messageText = chatInput.value.trim();
        if (!messageText || !currentChatId) return;

        // Clear input and reset height
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Add user message to UI
        const userMessage = {
            content: messageText,
            role: 'user',
            timestamp: new Date().toISOString(),
        };
        addMessageToUI(userMessage);

        // Show typing indicator
        showTypingIndicator();

        try {
            // Send message to server
            const response = await fetch(`/api/chat/sessions/${currentChatId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: messageText,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            // If using SSE for streaming, connect to the stream
            connectToMessageStream();

        } catch (error) {
            hideTypingIndicator();
            showNotification('Error sending message: ' + error.message, 'error');

            // Show error message in chat
            const errorMessage = {
                content: 'Sorry, there was an error processing your request. Please try again.',
                role: 'assistant',
                timestamp: new Date().toISOString(),
                error: true,
            };
            addMessageToUI(errorMessage);
        }

        // Scroll to bottom
        scrollToBottom();
    }

    function connectToMessageStream() {
        // Close any existing stream
        if (eventSource) {
            eventSource.close();
        }

        // Connect to SSE stream
        eventSource = new EventSource(`/api/chat/sessions/${currentChatId}/stream`);

        let currentMessage = null;

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            // Handle different event types
            if (data.event === 'token') {
                // Add token to current message
                if (!currentMessage) {
                    // Hide typing indicator
                    hideTypingIndicator();

                    // Create new assistant message
                    currentMessage = {
                        id: data.message_id,
                        content: '',
                        role: 'assistant',
                        timestamp: new Date().toISOString(),
                    };

                    // Add to UI
                    addMessageToUI(currentMessage, true);
                }

                // Append token to message
                appendTokenToMessage(currentMessage.id, data.token);

            } else if (data.event === 'done') {
                // Message complete
                currentMessage = null;
                eventSource.close();
                eventSource = null;

                // Update message with citations if any
                if (data.citations && data.citations.length > 0) {
                    addCitationsToMessage(data.message_id, data.citations);
                }

                // Update session list to reflect latest activity
                const updatedSession = chatSessions.find(s => s.id === currentChatId);
                if (updatedSession) {
                    updatedSession.updated_at = new Date().toISOString();
                    renderChatSessions();
                }

            } else if (data.event === 'error') {
                // Handle error
                hideTypingIndicator();
                showNotification('Error: ' + data.error, 'error');
                eventSource.close();
                eventSource = null;
            }

            // Scroll to bottom
            scrollToBottom();
        };

        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            hideTypingIndicator();
            eventSource.close();
            eventSource = null;

            // Show error message
            showNotification('Connection error. Please try again.', 'error');
        };
    }

    function appendTokenToMessage(messageId, token) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (!messageElement) return;

        const messageContent = messageElement.querySelector('.message-text');
        if (messageContent) {
            messageContent.innerHTML += token;
        }
    }

    function addCitationsToMessage(messageId, citations) {
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (!messageElement || !citations || citations.length === 0) return;

        // Create citations container if it doesn't exist
        let citationsContainer = messageElement.querySelector('.message-citations');
        if (!citationsContainer) {
            citationsContainer = document.createElement('div');
            citationsContainer.className = 'message-citations';
            messageElement.querySelector('.message-content').appendChild(citationsContainer);
        }

        // Add citations heading
        citationsContainer.innerHTML = '<div class="citation-heading">Sources:</div>';

        // Create citation list
        const citationList = document.createElement('div');
        citationList.className = 'citation-list';

        // Add each citation
        citations.forEach((citation, index) => {
            const citationItem = document.createElement('a');
            citationItem.className = 'citation-item';
            citationItem.href = `/entry/${citation.entry_id}`;
            citationItem.target = '_blank';

            citationItem.innerHTML = `
                <div class="citation-number">${index + 1}</div>
                <div class="citation-content">
                    <div class="citation-title">${citation.title || 'Untitled Entry'}</div>
                    <div class="citation-date">${formatDate(citation.date)}</div>
                    <div class="citation-preview">${citation.snippet || ''}</div>
                </div>
            `;

            citationList.appendChild(citationItem);
        });

        // Add to container
        citationsContainer.appendChild(citationList);
    }

    function addMessageToUI(message, isStreaming = false) {
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.role}`;
        if (message.id) {
            messageElement.dataset.messageId = message.id;
        }

        // Add avatar based on role
        const avatarLetter = message.role === 'user' ? 'U' : 'J';

        // Build HTML
        messageElement.innerHTML = `
            <div class="message-avatar">${avatarLetter}</div>
            <div class="message-content">
                <div class="message-text">${isStreaming ? '' : message.content}</div>
            </div>
        `;

        // Add to chat container
        chatMessages.appendChild(messageElement);

        // Scroll to bottom
        scrollToBottom();
    }

    function showTypingIndicator() {
        if (isTyping) return;

        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';

        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;

        chatMessages.appendChild(indicator);
        isTyping = true;
        scrollToBottom();
    }

    function hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
        isTyping = false;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function openRenameModal() {
        if (!currentChatId) return;

        const currentSession = chatSessions.find(s => s.id === currentChatId);
        if (currentSession) {
            renameInput.value = currentSession.title || 'Untitled Chat';
        }

        renameModal.classList.remove('hidden');
        setTimeout(() => renameInput.focus(), 100);
    }

    function closeRenameModal() {
        renameModal.classList.add('hidden');
    }

    async function renameChatSession() {
        if (!currentChatId) {
            closeRenameModal();
            return;
        }

        const newTitle = renameInput.value.trim();
        if (!newTitle) {
            closeRenameModal();
            return;
        }

        try {
            const response = await fetch(`/api/chat/sessions/${currentChatId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: newTitle,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to rename chat session');
            }

            // Update local state
            const session = chatSessions.find(s => s.id === currentChatId);
            if (session) {
                session.title = newTitle;
                currentChatTitle.textContent = newTitle;
            }

            // Re-render sidebar
            renderChatSessions();
            closeRenameModal();

        } catch (error) {
            showNotification('Error renaming chat: ' + error.message, 'error');
        }
    }

    function openDeleteModal() {
        if (!currentChatId) return;
        deleteModal.classList.remove('hidden');
    }

    function closeDeleteModal() {
        deleteModal.classList.add('hidden');
    }

    async function deleteChatSession() {
        if (!currentChatId) {
            closeDeleteModal();
            return;
        }

        try {
            const response = await fetch(`/api/chat/sessions/${currentChatId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Failed to delete chat session');
            }

            // Remove from local state
            chatSessions = chatSessions.filter(s => s.id !== currentChatId);

            // Re-render sidebar
            renderChatSessions();

            // If we have another session, load it
            if (chatSessions.length > 0) {
                loadChatSession(chatSessions[0].id);
            } else {
                // Otherwise, create a new one
                createNewChat();
            }

            closeDeleteModal();

        } catch (error) {
            showNotification('Error deleting chat: ' + error.message, 'error');
        }
    }

    // Utility functions
    function formatDate(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();

        // If it's today, show the time
        if (date.toDateString() === now.toDateString()) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        // If it's this year, show month and day
        if (date.getFullYear() === now.getFullYear()) {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }

        // Otherwise, show full date
        return date.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification ${type}`;
        notificationElement.textContent = message;

        // Add to body
        document.body.appendChild(notificationElement);

        // Remove after delay
        setTimeout(() => {
            notificationElement.style.animation = 'fade-out 0.5s forwards';
            setTimeout(() => {
                notificationElement.remove();
            }, 500);
        }, 3000);
    }
});
