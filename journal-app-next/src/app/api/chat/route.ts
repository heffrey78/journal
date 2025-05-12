import { NextRequest, NextResponse } from 'next/server';

// Define the backend API base URL - configurable via environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, sessionId } = body;

    console.log("Chat request:", { messageLength: message?.length, sessionId });

    // If no sessionId is provided, we need to create a new session first
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
        return NextResponse.json(
          {
            error: "Failed to connect to the backend API server. Please ensure the server is running at " + API_BASE_URL,
            details: error instanceof Error ? error.message : String(error)
          },
          { status: 503 }
        );
      }
    } else {
      console.log("Using existing session:", currentSessionId);
    }

    // Process the user message
    try {
      console.log(`Sending request to ${API_BASE_URL}/chat/sessions/${currentSessionId}/process`);
      const chatResponse = await fetch(`${API_BASE_URL}/chat/sessions/${currentSessionId}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: message,
        }),
      });

      if (!chatResponse.ok) {
        const errorText = await chatResponse.text().catch(() => chatResponse.statusText);
        console.error("Chat request failed:", chatResponse.status, errorText);
        throw new Error(`Failed to process chat message: ${chatResponse.statusText}${errorText ? ` - ${errorText}` : ''}`);
      }

      const responseData = await chatResponse.json();
      console.log("Chat response received:", {
        messageId: responseData.message?.id,
        referenceCount: responseData.references?.length || 0
      });

      // Format the response for the frontend
      return NextResponse.json({
        response: responseData.message.content,
        sessionId: currentSessionId,
        references: responseData.references || [],
        messageId: responseData.message.id,
      });
    } catch (error) {
      console.error("Error processing chat message:", error);
      return NextResponse.json(
        {
          error: "Failed to process chat message",
          details: error instanceof Error ? error.message : String(error)
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error("Error in chat API:", error);
    return NextResponse.json(
      { error: "Failed to process chat request" },
      { status: 500 }
    );
  }
}
