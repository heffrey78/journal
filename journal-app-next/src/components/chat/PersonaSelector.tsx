'use client';

import React, { useState, useEffect } from 'react';
import { Persona } from '@/types/chat';
import { fetchPersonas } from '@/api/chat';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

interface PersonaSelectorProps {
  selectedPersonaId?: string;
  onPersonaSelect: (persona: Persona) => void;
  onCancel?: () => void;
  className?: string;
}

export default function PersonaSelector({
  selectedPersonaId,
  onPersonaSelect,
  onCancel,
  className = ''
}: PersonaSelectorProps) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPersonas() {
      try {
        setLoading(true);
        const fetchedPersonas = await fetchPersonas(true);
        setPersonas(fetchedPersonas);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load personas');
      } finally {
        setLoading(false);
      }
    }

    loadPersonas();
  }, []);

  const handlePersonaClick = (persona: Persona) => {
    onPersonaSelect(persona);
  };

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="text-center mb-6">
          <h2 className="text-xl font-semibold mb-2">Choose Your AI Persona</h2>
          <p className="text-muted-foreground">
            Select a personality for your conversation
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-start space-x-3">
                <Skeleton className="w-8 h-8 rounded" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-5 w-24" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center space-y-4 ${className}`}>
        <div className="text-red-600 mb-4">
          <p className="font-medium">Failed to load personas</p>
          <p className="text-sm">{error}</p>
        </div>
        <Button
          onClick={() => window.location.reload()}
          variant="outline"
        >
          Try Again
        </Button>
      </div>
    );
  }

  // Separate default and custom personas
  const defaultPersonas = personas.filter(p => p.is_default);
  const customPersonas = personas.filter(p => !p.is_default);

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="text-center mb-6">
        <h2 className="text-xl font-semibold mb-2">Choose Your AI Persona</h2>
        <p className="text-muted-foreground">
          Select a personality for your conversation
        </p>
      </div>

      {/* Default Personas */}
      {defaultPersonas.length > 0 && (
        <div>
          <h3 className="text-lg font-medium mb-3">Default Personas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {defaultPersonas.map((persona) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                isSelected={selectedPersonaId === persona.id}
                onClick={() => handlePersonaClick(persona)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Custom Personas */}
      {customPersonas.length > 0 && (
        <div>
          <h3 className="text-lg font-medium mb-3">Custom Personas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {customPersonas.map((persona) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                isSelected={selectedPersonaId === persona.id}
                onClick={() => handlePersonaClick(persona)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {onCancel && (
        <div className="flex justify-center pt-4">
          <Button onClick={onCancel} variant="outline">
            Cancel
          </Button>
        </div>
      )}
    </div>
  );
}

interface PersonaCardProps {
  persona: Persona;
  isSelected: boolean;
  onClick: () => void;
}

function PersonaCard({ persona, isSelected, onClick }: PersonaCardProps) {
  return (
    <Card
      className={`
        p-4 cursor-pointer transition-all duration-200 hover:shadow-md
        ${isSelected
          ? 'ring-2 ring-blue-500 border-blue-500 bg-blue-50 dark:bg-blue-950'
          : 'hover:border-gray-300 dark:hover:border-gray-600'
        }
      `}
      onClick={onClick}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className="text-2xl flex-shrink-0 mt-1">
          {persona.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h4 className="font-medium text-sm truncate">
              {persona.name}
            </h4>
            {persona.is_default && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded dark:bg-green-900 dark:text-green-200">
                Default
              </span>
            )}
          </div>

          <p className="text-sm text-muted-foreground" style={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden'
          }}>
            {persona.description}
          </p>

          {isSelected && (
            <div className="mt-3 flex items-center text-blue-600 dark:text-blue-400">
              <svg
                className="w-4 h-4 mr-1"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-xs font-medium">Selected</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
