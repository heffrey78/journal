import { NextRequest, NextResponse } from 'next/server';

// Use 127.0.0.1 instead of localhost to explicitly use IPv4
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { session_id: string, message_id: string } }
) {
  try {
    const { session_id, message_id } = params;

    if (!session_id || !message_id) {
      return NextResponse.json({ error: 'Session ID and Message ID are required' }, { status: 400 });
    }

    const response = await fetch(`${API_BASE_URL}/chat/sessions/${session_id}/messages/${message_id}`);

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Failed to fetch message references: ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    // The backend returns a ChatMessageResponse object with message and references fields
    // We just want to return the references
    return NextResponse.json(data.references || []);
  } catch (error) {
    console.error('Error fetching message references:', error);
    return NextResponse.json(
      { error: 'Failed to fetch message references' },
      { status: 500 }
    );
  }
}
