'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ModelSelector from './ModelSelector';
import PersonaDropdown from './PersonaDropdown';
import PersonaIndicator from './PersonaIndicator';
import SaveConversationDialog from '../dialogs/SaveConversationDialog';
import InConversationSearch from './InConversationSearch';
import { Message, EntryReference } from './types';
import { AlertCircle, Download, Search } from 'lucide-react';
import { ToolActivityIndicator } from './ToolUsageIndicator';
import { CHAT_API, CONFIG_API } from '@/config/api';
import { updateChatMessage, deleteChatMessage, updateChatSessionPersona } from '@/api/chat';

interface ChatInterfaceProps {
  sessionId?: string | null;
  onFirstMessage?: (content: string, personaId?: string) => Promise<void>;
  isCreatingSession?: boolean;
  defaultPersona?: any;
}

export default function ChatInterface({
  sessionId: propSessionId,
  onFirstMessage,
  isCreatingSession = false,
  defaultPersona
}: ChatInterfaceProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentMessageReferences, setCurrentMessageReferences] = useState<EntryReference[]>([]);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState<boolean>(true);
  // Session state that can be provided via prop or stored in sessionStorage
  const [sessionId, setSessionId] = useState<string | null>(propSessionId || null);
  // Model selection state
  const [currentSessionModel, setCurrentSessionModel] = useState<string | null>(null);
  // Save conversation dialog state
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [sessionTitle, setSessionTitle] = useState<string>('');
  // Persona state - Initialize with default persona for new chats
  const [sessionPersonaId, setSessionPersonaId] = useState<string | null>(
    propSessionId === 'new' && defaultPersona ? defaultPersona.id : null
  );
  // Tool activity state
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [currentStreamingToolResults, setCurrentStreamingToolResults] = useState<any[]>([]);
  // In-conversation search state
  const [showInConversationSearch, setShowInConversationSearch] = useState(false);

  // React to changes in session ID (from props or storage)
  useEffect(() => {
    // If we have a prop sessionId, use that
    if (propSessionId) {
      // Only update if the sessionId actually changed to avoid unnecessary rerenders
      if (sessionId !== propSessionId) {
        setSessionId(propSessionId);
        console.log('Using provided session ID from props:', propSessionId);
      }
    } else {
      // Otherwise check sessionStorage
      const storedSessionId = sessionStorage.getItem('chatSessionId');

      // Check if the session ID starts with "mock_" - if so, clear it
      if (storedSessionId && storedSessionId.startsWith('mock_')) {
        console.log('Clearing mock session ID:', storedSessionId);
        sessionStorage.removeItem('chatSessionId');
        setSessionId(null);
      } else if (storedSessionId && sessionId !== storedSessionId) {
        console.log('Using existing session ID from storage:', storedSessionId);
        setSessionId(storedSessionId);
      } else if (!storedSessionId && !propSessionId && sessionId) {
        // Clear sessionId if there's no prop or stored ID
        setSessionId(null);
      }
    }
  }, [propSessionId, sessionId]);

  // Load default LLM configuration
  useEffect(() => {
    const fetchDefaultModel = async () => {
      try {
        const response = await fetch(CONFIG_API.LLM);

        if (response.ok) {
          const config = await response.json();
          if (config && config.model_name) {
            // Only set current session model if it's not already set
            if (!currentSessionModel) {
              setCurrentSessionModel(config.model_name);
            }
          }
        } else {
          console.error('Failed to fetch LLM configuration');
        }
      } catch (error) {
        console.error('Error fetching LLM configuration:', error);
      }
    };

    fetchDefaultModel();
  }, [currentSessionModel]);

   // Load messages when session ID changes
  useEffect(() => {
    const loadMessages = async () => {
      if (!sessionId || sessionId === 'new') return;

      try {
        setLoading(true);
        console.log('Loading messages for session:', sessionId);

        // Load session details first
        try {
          const sessionResponse = await fetch(CHAT_API.SESSION(sessionId));
          if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            setSessionTitle(sessionData.title || 'Chat Session');
            setSessionPersonaId(sessionData.persona_id || null);
            console.log('Loaded session:', sessionData.title, 'with persona:', sessionData.persona_id);
          }
        } catch (sessionError) {
          console.error('Error loading session details:', sessionError);
        }

        // Use direct connection to backend rather than through Next.js API route
        // This avoids IPv6/IPv4 connection issues
        const response = await fetch(CHAT_API.MESSAGES(sessionId));

        if (!response.ok) {
          throw new Error('Failed to load chat history');
        }

        const data = await response.json();

        if (Array.isArray(data)) {
          console.log('Received messages:', data.length);
          // Log the structure of the first message for debugging
          if (data.length > 0) {
            console.log('First message structure:', JSON.stringify(data[0], null, 2));
          }

          // First, transform the basic message data
          const formattedMessages = data.map(msg => {
            // Initialize empty references array
            const references: EntryReference[] = [];

            // Check if we need to fetch references separately
            const hasReferences = msg.metadata && typeof msg.metadata === 'object' && msg.metadata.has_references === true;

            // Extract tool usage information from metadata
            const toolsUsed = msg.metadata && typeof msg.metadata === 'object' && msg.metadata.tools_used ?
              msg.metadata.tools_used : [];

            return {
              id: msg.id,
              content: msg.content,
              role: msg.role,
              timestamp: new Date(msg.created_at),
              references,
              has_references: hasReferences,
              tools_used: toolsUsed,
              metadata: msg.metadata
            };
          });

          setMessages(formattedMessages);

          // Now, for messages with has_references=true, fetch the actual references
          // This is done separately to avoid delaying the initial message display
          const messagesWithReferences = formattedMessages.filter(msg => msg.has_references);

          if (messagesWithReferences.length > 0) {
            console.log(`Found ${messagesWithReferences.length} messages with references to fetch`);

            // For each message with references, fetch them
            const fetchReferencesPromises = messagesWithReferences.map(async (msg) => {
              try {
                const refResponse = await fetch(CHAT_API.MESSAGE(sessionId, msg.id));

                if (refResponse.ok) {
                  const responseData = await refResponse.json();
                  // The backend returns a structure with message and references fields
                  const referencesData = responseData.references || [];

                  console.log(`Fetched ${referencesData.length} references for message ${msg.id}`);

                  // Update this specific message with its references
                  setMessages(currentMessages =>
                    currentMessages.map(currentMsg =>
                      currentMsg.id === msg.id
                        ? { ...currentMsg, references: referencesData }
                        : currentMsg
                    )
                  );

                } else {
                  console.warn(`Failed to fetch references for message ${msg.id}`);
                }
              } catch (refError) {
                console.error(`Error fetching references for message ${msg.id}:`, refError);
              }
            });

            // Don't await these promises to avoid delaying the UI
            // They will resolve in the background and update the messages state as they complete
            Promise.all(fetchReferencesPromises).catch(err => {
              console.error('Error fetching references:', err);
            });
          }
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
        // Log more detailed error information to help with debugging
        if (error instanceof Error) {
          console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            sessionId
          });
        }
        setApiError('Failed to load chat history. Try refreshing the page.');
      } finally {
        setLoading(false);
      }
    };

    if (sessionId) {
      loadMessages();
    } else {
      // Clear messages if no session ID
      setMessages([]);
    }
  }, [sessionId]);

  // Auto-scroll to the bottom when messages change or during streaming
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+F or Cmd+F to open search
      if ((event.ctrlKey || event.metaKey) && event.key === 'f' && sessionId && messages.length > 0) {
        event.preventDefault();
        setShowInConversationSearch(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [sessionId, messages.length]);

  // Function to generate a unique ID for messages
  const generateMessageId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  };

  // Function to handle sending a new message
  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Clear any previous API errors
    setApiError(null);

    // Handle lazy session creation (when sessionId is null or "new")
    if ((!sessionId || sessionId === 'new') && onFirstMessage) {
      try {
        setLoading(true);
        await onFirstMessage(content, sessionPersonaId || undefined);
        return; // The parent component will handle navigation to the new session
      } catch (error) {
        console.error('Error creating session with first message:', error);
        setApiError(error instanceof Error ? error.message : 'Failed to create chat session');
        setLoading(false);
        return;
      }
    }

    // Add user message to the chat
    const userMessage: Message = {
      id: generateMessageId(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setLoading(true);

    // Reset streaming state
    setStreamingMessage('');
    setIsStreaming(false);
    setCurrentMessageReferences([]);
    setCurrentMessageId(null);
    setActiveTools([]);
    setCurrentStreamingToolResults([]);

    if (useStreaming) {
      // Use the streaming API
      try {
        await streamChatResponse(content);
      } catch (error) {
        console.error('Error with streaming chat response:', error);
        setApiError(error instanceof Error ? error.message : 'An unknown error occurred with streaming');

        // Fallback to non-streaming if streaming fails
        try {
          await sendNonStreamingMessage(content);
        } catch (fallbackError) {
          console.error('Fallback chat request also failed:', fallbackError);

          // Add error message if both methods fail
          addErrorMessage();
        }
      } finally {
        setLoading(false);
        setIsStreaming(false);
      }
    } else {
      // Use the non-streaming API directly
      try {
        await sendNonStreamingMessage(content);
      } catch (error) {
        console.error('Error getting chat response:', error);
        setApiError(error instanceof Error ? error.message : 'An unknown error occurred');
        addErrorMessage();
      } finally {
        setLoading(false);
      }
    }
  };

  // Stream chat response using EventSource
  const streamChatResponse = async (content: string) => {
    if (!sessionId) {
      throw new Error('Session ID is required for streaming');
    }

    try {
      setIsStreaming(true);
      // Connect directly to backend streaming endpoint
      const response = await fetch(CHAT_API.STREAM(sessionId), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content,  // Backend expects 'content' not 'message'
          model_name: currentSessionModel, // Include current model if set
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || errorData.details || 'Failed to get streaming response');
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedResponse = '';
      let receivedMetadata = false;

      // Process the streamed response
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;

          const data = line.replace('data: ', '');

          // Handle the metadata which comes in the first event
          if (!receivedMetadata && data.includes('message_id')) {
            try {
              const metadata = JSON.parse(data);
              // Store the session ID if provided
              if (metadata.sessionId) {
                sessionStorage.setItem('chatSessionId', metadata.sessionId);
                setSessionId(metadata.sessionId);
                console.log('Updated session ID from stream:', metadata.sessionId);
              }
              // Store message ID and references
              if (metadata.message_id) {
                setCurrentMessageId(metadata.message_id);
              }
              if (metadata.references) {
                setCurrentMessageReferences(metadata.references);
              }
              // Handle tool results for real-time indicators
              if (metadata.tool_results) {
                console.log('Received tool results in stream metadata:', metadata.tool_results);

                // Format tool results to match ToolUsage interface
                const formattedToolResults = metadata.tool_results.map((tool: any) => ({
                  tool_name: tool.tool_name || 'unknown',
                  success: tool.success || false,
                  execution_time_ms: tool.metadata?.execution_time_ms,
                  result_count: tool.metadata?.result_count,
                  error: tool.success ? undefined : (tool.error || 'Tool execution failed'),
                }));

                setCurrentStreamingToolResults(formattedToolResults);
                // Extract active tool names for indicators
                const toolNames = metadata.tool_results.map((tool: any) => tool.tool_name);
                setActiveTools(toolNames);
              }
              receivedMetadata = true;
              continue;
            } catch (e) {
              console.error('Error parsing metadata:', e);
            }
          }

          // Handle the end of stream marker
          if (data === '[DONE]') {
            // Finalize the message when the stream ends
            finalizeStreamingMessage(accumulatedResponse);
            break;
          }

          try {
            // Try to parse the data as JSON - our new format sends {"text": "content"}
            const parsedData = JSON.parse(data);
            if (parsedData.text) {
              accumulatedResponse += parsedData.text;
              setStreamingMessage(accumulatedResponse);
              continue;
            }

            // Handle error messages
            if (parsedData.error) {
              console.error('Error from server stream:', parsedData.error);
              setApiError(parsedData.error);
              break;
            }
          } catch {
            // If parsing fails, use the raw data (backward compatibility)
            console.warn('Failed to parse streaming data as JSON, using raw text:', data);
            accumulatedResponse += data;
            setStreamingMessage(accumulatedResponse);
          }
        }
      }

    } catch (error) {
      console.error('Error in streaming chat response:', error);
      throw error;
    }
  };

  // Finalize the streaming message and add it to the message list
  const finalizeStreamingMessage = (content: string) => {
    const assistantMessage: Message = {
      id: currentMessageId || generateMessageId(),
      content: content.trim(),
      role: 'assistant',
      timestamp: new Date(),
      references: currentMessageReferences,
      tools_used: currentStreamingToolResults,
    };

    setMessages((prevMessages) => [...prevMessages, assistantMessage]);
    setStreamingMessage('');
    setIsStreaming(false);
    // Clear active tools and streaming tool results
    setActiveTools([]);
    setCurrentStreamingToolResults([]);
  };

  // Send a non-streaming message (fallback or direct use)
  const sendNonStreamingMessage = async (content: string) => {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }

    // Connect directly to backend non-streaming endpoint
    const response = await fetch(CHAT_API.MESSAGES(sessionId), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: content,  // Note: backend expects 'content' not 'message'
        model_name: currentSessionModel, // Include current model if set
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || data.details || 'Failed to get response');
    }

    // The backend doesn't return the session ID in this response, we already have it
    console.log('Non-streaming message sent successfully for session:', sessionId);

    // Add assistant response to the chat
    // The backend will return a message object with structure like:
    // { id: '...', content: '...', role: 'assistant', created_at: '...', metadata: {...} }
    const assistantMessage: Message = {
      id: data.id || generateMessageId(),
      content: data.content,
      role: data.role || 'assistant',
      timestamp: new Date(data.created_at || Date.now()),
      references: [],  // References need to be fetched separately if needed
      has_references: data.metadata?.has_references === true,
    };

    setMessages((prevMessages) => [...prevMessages, assistantMessage]);    // If the message has references, fetch them separately
    if (assistantMessage.has_references && assistantMessage.id && sessionId) {
      try {
        const refResponse = await fetch(CHAT_API.MESSAGE(sessionId, assistantMessage.id));

        if (refResponse.ok) {
          const responseData = await refResponse.json();
          // The backend returns a structure with message and references fields
          const referencesData = responseData.references || [];

          console.log(`Fetched ${referencesData.length} references for new message ${assistantMessage.id}`);

          // Update this specific message with its references
          setMessages(currentMessages =>
            currentMessages.map(currentMsg =>
              currentMsg.id === assistantMessage.id
                ? { ...currentMsg, references: referencesData }
                : currentMsg
            )
          );
        }
      } catch (refError) {
        console.error(`Error fetching references for new message:`, refError);
      }
    }
  };

  // Add an error message when chat fails
  const addErrorMessage = () => {
    const errorMessage: Message = {
      id: generateMessageId(),
      content: 'Sorry, I encountered an error while processing your request. Please check that the backend server is running.',
      role: 'assistant',
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, errorMessage]);
  };

  // Clear error and try again
  const tryAgain = () => {
    setApiError(null);
  };

  // Handle model change
  const handleModelChange = (model: string) => {
    setCurrentSessionModel(model);
    // Note: This only affects the current session, not the default model
    console.log(`Changed model for current session to: ${model}`);
  };

  // Handle persona change
  const handlePersonaChange = async (personaId: string) => {
    if (!sessionId || sessionId === 'new') {
      // For new chats, just update the local state
      setSessionPersonaId(personaId);
      console.log(`Set persona for new chat to: ${personaId}`);
      return;
    }

    try {
      console.log(`Changing persona for session ${sessionId} to: ${personaId}`);
      await updateChatSessionPersona(sessionId, personaId);
      setSessionPersonaId(personaId);
      console.log(`Successfully changed persona to: ${personaId}`);
    } catch (error) {
      console.error('Failed to update session persona:', error);
      // Optionally show user-facing error message
    }
  };

  // Toggle between streaming and non-streaming mode
  const toggleStreamingMode = () => {
    setUseStreaming(!useStreaming);
  };

  // Reset chat session - redirect to persona selection
  const resetChatSession = () => {
    router.push('/chat/new');
  };

  // Handle message edit
  const handleEditMessage = async (messageId: string, newContent: string) => {
    if (!sessionId) return;

    try {
      // Update message locally (optimistic update)
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === messageId
            ? { ...msg, content: newContent, metadata: { ...msg.metadata, edited: true } }
            : msg
        )
      );

      // Call API to update message
      await updateChatMessage(sessionId, messageId, newContent);
      console.log(`Message ${messageId} updated successfully`);
    } catch (error) {
      console.error('Failed to update message:', error);
      // Revert on error - reload messages
      const loadMessages = async () => {
        try {
          const response = await fetch(CHAT_API.MESSAGES(sessionId));
          if (response.ok) {
            const data = await response.json();
            const formattedMessages = data.map((msg: Message & { created_at: string; metadata?: Record<string, unknown> }) => ({
              id: msg.id,
              content: msg.content,
              role: msg.role,
              timestamp: new Date(msg.created_at),
              references: [],
              has_references: msg.metadata?.has_references === true,
              metadata: msg.metadata
            }));
            setMessages(formattedMessages);
          }
        } catch (err) {
          console.error('Failed to reload messages:', err);
        }
      };
      loadMessages();
      throw error;
    }
  };

  // Handle message delete
  const handleDeleteMessage = async (messageId: string) => {
    if (!sessionId) return;

    try {
      // Remove message locally (optimistic update)
      setMessages(prevMessages => prevMessages.filter(msg => msg.id !== messageId));

      // Call API to delete message
      await deleteChatMessage(sessionId, messageId);
      console.log(`Message ${messageId} deleted successfully`);
    } catch (error) {
      console.error('Failed to delete message:', error);
      // Revert on error - reload messages
      const loadMessages = async () => {
        try {
          const response = await fetch(CHAT_API.MESSAGES(sessionId));
          if (response.ok) {
            const data = await response.json();
            const formattedMessages = data.map((msg: Message & { created_at: string; metadata?: Record<string, unknown> }) => ({
              id: msg.id,
              content: msg.content,
              role: msg.role,
              timestamp: new Date(msg.created_at),
              references: [],
              has_references: msg.metadata?.has_references === true,
              metadata: msg.metadata
            }));
            setMessages(formattedMessages);
          }
        } catch (err) {
          console.error('Failed to reload messages:', err);
        }
      };
      loadMessages();
      throw error;
    }
  };

  // Handle message found via in-conversation search
  const handleMessageFound = (messageId: string) => {
    const messageElement = document.getElementById(`message-${messageId}`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Add temporary highlight
      messageElement.classList.add('bg-yellow-100', 'dark:bg-yellow-900', 'transition-colors');
      setTimeout(() => {
        messageElement.classList.remove('bg-yellow-100', 'dark:bg-yellow-900', 'transition-colors');
      }, 2000);
    }
  };

  return (
    <div className="flex flex-col h-[70vh] border rounded-lg shadow-sm bg-background mx-6 w-auto mt-6 mb-2 p-0">
      {/* API Error Banner */}
      {apiError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Backend Connection Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{apiError}</p>
                <p className="mt-1">Make sure your Python backend server is running at the correct address.</p>
              </div>
              <div className="mt-3 flex space-x-4">
                <button
                  onClick={tryAgain}
                  className="text-sm font-medium text-red-700 hover:text-red-600"
                >
                  Try again
                </button>
                <button
                  onClick={resetChatSession}
                  className="text-sm font-medium text-red-700 hover:text-red-600"
                >
                  Reset session
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="px-6 py-3 flex justify-between border-b">
        <div className="flex items-center space-x-4">
          {sessionId && (
            <button
              onClick={resetChatSession}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              New chat
            </button>
          )}
          {sessionPersonaId && (
            <PersonaIndicator
              personaId={sessionPersonaId}
              className="border-l pl-4 ml-4"
            />
          )}
        </div>
        <div className="flex items-center space-x-4">
          {/* Search in conversation button */}
          {sessionId && sessionId !== 'new' && messages.length > 0 && (
            <button
              onClick={() => setShowInConversationSearch(true)}
              disabled={loading || isStreaming}
              className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Search in conversation (Ctrl+F)"
            >
              <Search className="h-4 w-4" />
              <span>Search</span>
            </button>
          )}

          {/* Save Conversation Button */}
          {sessionId && sessionId !== 'new' && messages.length > 0 && (
            <button
              onClick={() => setShowSaveDialog(true)}
              disabled={loading || isStreaming}
              className="flex items-center space-x-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Save conversation as journal entry"
            >
              <Download className="h-4 w-4" />
              <span>Save</span>
            </button>
          )}

          {/* Persona and Model Selectors */}
          {sessionId && (
            <div className="flex items-center space-x-4">
              <PersonaDropdown
                currentPersonaId={sessionPersonaId}
                onPersonaChange={handlePersonaChange}
                disabled={loading || isStreaming}
              />
              <ModelSelector
                currentModel={currentSessionModel}
                onModelChange={handleModelChange}
                disabled={loading || isStreaming}
              />
            </div>
          )}
          <span className="text-sm mr-2 text-foreground">Streaming mode:</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={useStreaming}
              onChange={toggleStreamingMode}
            />
            <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-muted after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>
      </div>

      {/* Chat messages container */}
      <div className="flex-1 overflow-y-auto p-6 bg-background">
        {messages.length === 0 && !isStreaming ? (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <p>Start chatting with your journal. Ask about entries, trends, or memories.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} id={`message-${message.id}`} className="space-y-2">
                <ChatMessage
                  message={message}
                  sessionId={sessionId || undefined}
                  sessionTitle={sessionTitle}
                  canSave={true}
                  onEdit={handleEditMessage}
                  onDelete={handleDeleteMessage}
                />
                {/* Remove duplicate EntryReferences since ChatMessage now handles this */}
              </div>
            ))}

            {/* Streaming Message */}
            {isStreaming && streamingMessage && (
              <div className="space-y-2 mb-6">
                <ChatMessage
                  message={{
                    id: 'streaming',
                    content: streamingMessage,
                    role: 'assistant',
                    timestamp: new Date(),
                    references: currentMessageReferences,
                  }}
                  sessionId={sessionId || undefined}
                  sessionTitle={sessionTitle}
                  canSave={false}
                />
                {/* Remove duplicate EntryReferences since ChatMessage now handles this */}
              </div>
            )}

            {/* Loading indicator */}
            {loading && !isStreaming && (
              <div className="space-y-4 mt-6">
                {/* Tool activity indicators */}
                {activeTools.length > 0 && (
                  <div className="space-y-2">
                    {activeTools.map((toolName, index) => (
                      <ToolActivityIndicator
                        key={index}
                        isActive={true}
                        toolName={toolName}
                      />
                    ))}
                  </div>
                )}

                {/* Loading indicator */}
                <div className="flex items-center space-x-3 text-gray-500">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="text-sm">
                    {activeTools.length > 0 ? 'Processing...' : 'Thinking...'}
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t p-6 bg-background">
        <ChatInput onSendMessage={handleSendMessage} isLoading={loading || isCreatingSession} />
      </div>

      {/* Save Conversation Dialog */}
      <SaveConversationDialog
        isOpen={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        sessionId={sessionId || ''}
        sessionTitle={sessionTitle}
        messages={messages}
      />

      {/* In-conversation search */}
      {sessionId && (
        <InConversationSearch
          sessionId={sessionId}
          isOpen={showInConversationSearch}
          onClose={() => setShowInConversationSearch(false)}
          onMessageFound={handleMessageFound}
        />
      )}
    </div>
  );
}
