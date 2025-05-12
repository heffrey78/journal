import { NextRequest } from 'next/server';

// Define the backend API base URL - configurable via environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { message, sessionId } = body;

  console.log("Chat stream request:", { messageLength: message?.length, sessionId });

  // If no sessionId is provided, create a new session first
  let currentSessionId = sessionId;
  if (!currentSessionId) {
    try {
      console.log("Creating new chat session");
      // Create a new chat session
      const sessionResponse = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: `Chat session ${new Date().toLocaleString()}`,
        }),
      });

      if (!sessionResponse.ok) {
        throw new Error(`Failed to create chat session: ${sessionResponse.statusText}`);
      }

      const sessionData = await sessionResponse.json();
      currentSessionId = sessionData.id;
      console.log("Created new session:", currentSessionId);
    } catch (error) {
      console.error("Error connecting to backend API:", error);
      return new Response(
        JSON.stringify({
          error: "Failed to connect to the backend API server. Please ensure the server is running.",
          details: error instanceof Error ? error.message : String(error)
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  } else {
    console.log("Using existing session:", currentSessionId);
  }

  try {
    // Forward the streaming request to the backend
    console.log(`Sending request to ${API_BASE_URL}/chat/sessions/${currentSessionId}/stream`);
    const streamResponse = await fetch(`${API_BASE_URL}/chat/sessions/${currentSessionId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: message,
      }),
    });

    if (!streamResponse.ok) {
      const errorText = await streamResponse.text().catch(() => streamResponse.statusText);
      console.error("Stream request failed:", streamResponse.status, errorText);
      throw new Error(`Failed to process streaming chat message: ${streamResponse.statusText}${errorText ? ` - ${errorText}` : ''}`);
    }

    // Forward the streaming response from the backend to the client
    return new Response(streamResponse.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error("Error processing streaming chat message:", error);
    return new Response(
      JSON.stringify({
        error: "Failed to process streaming chat message",
        details: error instanceof Error ? error.message : String(error)
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
