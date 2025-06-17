'use client';

import React, { useState, useEffect } from 'react';
import { Persona } from '@/types/chat';
import { getPersona } from '@/api/chat';

interface PersonaIndicatorProps {
  personaId?: string;
  className?: string;
}

export default function PersonaIndicator({ personaId, className = '' }: PersonaIndicatorProps) {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!personaId) {
      setPersona(null);
      return;
    }

    async function loadPersona() {
      try {
        setLoading(true);
        setError(null);
        const fetchedPersona = await getPersona(personaId);
        setPersona(fetchedPersona);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load persona');
      } finally {
        setLoading(false);
      }
    }

    loadPersona();
  }, [personaId]);

  if (!personaId) {
    return null;
  }

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 text-sm text-muted-foreground ${className}`}>
        <div className="w-4 h-4 bg-gray-200 rounded animate-pulse"></div>
        <span>Loading persona...</span>
      </div>
    );
  }

  if (error || !persona) {
    return (
      <div className={`flex items-center space-x-2 text-sm text-muted-foreground ${className}`}>
        <span className="text-red-500">⚠️</span>
        <span>Persona unavailable</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-2 text-sm ${className}`}>
      <span className="text-lg" title={persona.description}>
        {persona.icon}
      </span>
      <span className="font-medium text-muted-foreground">
        {persona.name}
      </span>
      {persona.is_default && (
        <span className="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded dark:bg-green-900 dark:text-green-200">
          Default
        </span>
      )}
    </div>
  );
}
