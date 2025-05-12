'use client';

import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import EntryReferences from './EntryReferences';
import { Message, EntryReference } from './types';
import { AlertCircle } from 'lucide-react';

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentMessageReferences, setCurrentMessageReferences] = useState<EntryReference[]>([]);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState<boolean>(true);
  // New state to track the session ID
  const [sessionId, setSessionId] = useState<string | null>(null);

  // On component mount, check for valid session ID
  useEffect(() => {
    const storedSessionId = sessionStorage.getItem('chatSessionId');

    // Check if the session ID starts with "mock_" - if so, clear it
    if (storedSessionId && storedSessionId.startsWith('mock_')) {
      console.log('Clearing mock session ID:', storedSessionId);
      sessionStorage.removeItem('chatSessionId');
      setSessionId(null);
    } else if (storedSessionId) {
      console.log('Using existing session ID:', storedSessionId);
      setSessionId(storedSessionId);
    }
  }, []);

  // Auto-scroll to the bottom when messages change or during streaming
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Function to generate a unique ID for messages
  const generateMessageId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  };

  // Function to handle sending a new message
  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Clear any previous API errors
    setApiError(null);

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
    try {
      setIsStreaming(true);
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          sessionId: sessionId,
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
          } catch (e) {
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
    };

    setMessages((prevMessages) => [...prevMessages, assistantMessage]);
    setStreamingMessage('');
    setIsStreaming(false);
  };

  // Send a non-streaming message (fallback or direct use)
  const sendNonStreamingMessage = async (content: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: content,
        sessionId: sessionId,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || data.details || 'Failed to get response');
    }

    // Store session ID if provided
    if (data.sessionId) {
      sessionStorage.setItem('chatSessionId', data.sessionId);
      setSessionId(data.sessionId);
      console.log('Updated session ID from regular response:', data.sessionId);
    }

    // Add assistant response to the chat
    const assistantMessage: Message = {
      id: data.messageId || generateMessageId(),
      content: data.response,
      role: 'assistant',
      timestamp: new Date(),
      references: data.references || [],
    };

    setMessages((prevMessages) => [...prevMessages, assistantMessage]);
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

  // Toggle between streaming and non-streaming mode
  const toggleStreamingMode = () => {
    setUseStreaming(!useStreaming);
  };

  // Reset chat session
  const resetChatSession = () => {
    // Clear session storage
    sessionStorage.removeItem('chatSessionId');
    // Clear state
    setSessionId(null);
    setMessages([]);
    setApiError(null);
    console.log('Chat session reset');
  };

  return (
    <div className="flex flex-col h-[70vh] border rounded-lg shadow-sm bg-white">
      {/* API Error Banner */}
      {apiError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
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

      {/* Streaming Mode Toggle */}
      <div className="px-4 py-2 flex justify-between">
        <div>
          {sessionId && (
            <button
              onClick={resetChatSession}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              New chat
            </button>
          )}
        </div>
        <div className="flex items-center">
          <span className="text-sm mr-2">Streaming mode:</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={useStreaming}
              onChange={toggleStreamingMode}
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </div>

      {/* Chat messages container */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !isStreaming ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <p>Start chatting with your journal. Ask about entries, trends, or memories.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="space-y-2">
                <ChatMessage message={message} />
                {/* Remove duplicate EntryReferences since ChatMessage now handles this */}
              </div>
            ))}

            {/* Streaming Message */}
            {isStreaming && streamingMessage && (
              <div className="space-y-2">
                <ChatMessage
                  message={{
                    id: 'streaming',
                    content: streamingMessage,
                    role: 'assistant',
                    timestamp: new Date(),
                    references: currentMessageReferences,
                  }}
                />
                {/* Remove duplicate EntryReferences since ChatMessage now handles this */}
              </div>
            )}

            {/* Loading indicator */}
            {loading && !isStreaming && (
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="text-sm">Thinking...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t p-4">
        <ChatInput onSendMessage={handleSendMessage} isLoading={loading} />
      </div>
    </div>
  );
}
