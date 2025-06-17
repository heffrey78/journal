'use client';

import React, { useState, useEffect } from 'react';
import { Persona } from '@/types/chat';
import { fetchPersonas } from '@/api/chat';
import { Select, SelectOption } from '@/components/ui/select';

interface PersonaDropdownProps {
  currentPersonaId?: string | null;
  onPersonaChange: (personaId: string) => void;
  disabled?: boolean;
}

export default function PersonaDropdown({
  currentPersonaId,
  onPersonaChange,
  disabled = false,
}: PersonaDropdownProps) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPersonas() {
      try {
        setIsLoading(true);
        setError(null);
        const fetchedPersonas = await fetchPersonas(true);
        setPersonas(fetchedPersonas);
      } catch (err) {
        console.error('Error fetching personas:', err);
        setError('Failed to load personas');
        setPersonas([]);
      } finally {
        setIsLoading(false);
      }
    }

    loadPersonas();
  }, []);

  const handlePersonaChange = (value: string) => {
    onPersonaChange(value);
  };

  const displayPersonas = personas.length > 0 ? personas : [];

  return (
    <div className="flex items-center space-x-1">
      <span className="text-sm text-foreground whitespace-nowrap">
        Persona:
      </span>
      <Select
        value={currentPersonaId || undefined}
        onChange={handlePersonaChange}
        disabled={disabled || isLoading}
        placeholder={isLoading ? "Loading..." : "Select persona"}
        className="max-w-[180px]"
      >
        {error ? (
          <SelectOption value="error" disabled>
            Failed to load personas
          </SelectOption>
        ) : displayPersonas.length === 0 && !isLoading ? (
          <SelectOption value="none" disabled>
            No personas available
          </SelectOption>
        ) : (
          displayPersonas.map((persona) => (
            <SelectOption key={persona.id} value={persona.id}>
              {`${persona.icon} ${persona.name}${persona.is_default ? ' (Default)' : ''}`}
            </SelectOption>
          ))
        )}
      </Select>
    </div>
  );
}
