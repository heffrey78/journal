'use client';

import React, { useState, useEffect } from 'react';
import { Persona, PersonaCreate, PersonaUpdate } from '@/types/chat';
import { fetchPersonas, createPersona, updatePersona, deletePersona } from '@/api/chat';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Edit3, Trash2, Save, X } from 'lucide-react';

interface PersonaManagerProps {
  onSaveComplete?: (success: boolean, message: string) => void;
}

export default function PersonaManager({ onSaveComplete }: PersonaManagerProps) {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingPersona, setEditingPersona] = useState<Persona | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    loadPersonas();
  }, []);

  const loadPersonas = async () => {
    try {
      setLoading(true);
      const fetchedPersonas = await fetchPersonas(true);
      setPersonas(fetchedPersonas);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load personas');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePersona = async (data: PersonaCreate) => {
    try {
      setSaving('create');
      const newPersona = await createPersona(data);
      setPersonas([...personas, newPersona]);
      setShowCreateForm(false);
      onSaveComplete?.(true, 'Persona created successfully');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create persona';
      onSaveComplete?.(false, message);
    } finally {
      setSaving(null);
    }
  };

  const handleUpdatePersona = async (personaId: string, data: PersonaUpdate) => {
    try {
      setSaving(personaId);
      const updatedPersona = await updatePersona(personaId, data);
      setPersonas(personas.map(p => p.id === personaId ? updatedPersona : p));
      setEditingPersona(null);
      onSaveComplete?.(true, 'Persona updated successfully');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update persona';
      onSaveComplete?.(false, message);
    } finally {
      setSaving(null);
    }
  };

  const handleDeletePersona = async (persona: Persona) => {
    if (persona.is_default) {
      onSaveComplete?.(false, 'Cannot delete default personas');
      return;
    }

    if (!confirm(`Are you sure you want to delete "${persona.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setSaving(persona.id);
      await deletePersona(persona.id);
      setPersonas(personas.filter(p => p.id !== persona.id));
      onSaveComplete?.(true, 'Persona deleted successfully');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete persona';
      onSaveComplete?.(false, message);
    } finally {
      setSaving(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium">Chat Personas</h3>
          <Skeleton className="h-9 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="p-4">
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <Skeleton className="w-8 h-8 rounded" />
                  <Skeleton className="h-5 w-24" />
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-4">
          <p className="font-medium">Failed to load personas</p>
          <p className="text-sm">{error}</p>
        </div>
        <Button onClick={loadPersonas} variant="outline">
          Try Again
        </Button>
      </div>
    );
  }

  const defaultPersonas = personas.filter(p => p.is_default);
  const customPersonas = personas.filter(p => !p.is_default);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">Chat Personas</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Manage AI personalities for different conversation styles
          </p>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          disabled={saving !== null}
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Persona
        </Button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <PersonaForm
          onSubmit={handleCreatePersona}
          onCancel={() => setShowCreateForm(false)}
          isSubmitting={saving === 'create'}
        />
      )}

      {/* Default Personas */}
      {defaultPersonas.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3">
            Default Personas
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {defaultPersonas.map((persona) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                isEditing={editingPersona?.id === persona.id}
                onEdit={(p) => setEditingPersona(p)}
                onSave={(data) => handleUpdatePersona(persona.id, data)}
                onDelete={() => handleDeletePersona(persona)}
                onCancel={() => setEditingPersona(null)}
                isSubmitting={saving === persona.id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Custom Personas */}
      <div>
        <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3">
          Custom Personas {customPersonas.length > 0 && `(${customPersonas.length})`}
        </h4>
        {customPersonas.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-gray-500 dark:text-gray-400">
              <p>No custom personas yet.</p>
              <p className="text-sm mt-1">Create your first custom persona to get started.</p>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {customPersonas.map((persona) => (
              <PersonaCard
                key={persona.id}
                persona={persona}
                isEditing={editingPersona?.id === persona.id}
                onEdit={(p) => setEditingPersona(p)}
                onSave={(data) => handleUpdatePersona(persona.id, data)}
                onDelete={() => handleDeletePersona(persona)}
                onCancel={() => setEditingPersona(null)}
                isSubmitting={saving === persona.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface PersonaFormProps {
  persona?: Persona;
  onSubmit: (data: PersonaCreate | PersonaUpdate) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

function PersonaForm({ persona, onSubmit, onCancel, isSubmitting = false }: PersonaFormProps) {
  const [formData, setFormData] = useState({
    name: persona?.name || '',
    description: persona?.description || '',
    system_prompt: persona?.system_prompt || '',
    icon: persona?.icon || '🤖'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.description.trim() || !formData.system_prompt.trim()) {
      return;
    }
    onSubmit(formData);
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-medium">
          {persona ? 'Edit Persona' : 'Create New Persona'}
        </h4>
        <Button variant="outline" size="sm" onClick={onCancel} disabled={isSubmitting}>
          <X className="w-4 h-4" />
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Icon</label>
            <Input
              value={formData.icon}
              onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
              placeholder="🤖"
              maxLength={10}
              className="text-center text-lg"
            />
          </div>
          <div className="md:col-span-3">
            <label className="block text-sm font-medium mb-1">Name</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter persona name"
              required
              maxLength={100}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <Input
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Brief description of the persona's purpose"
            required
            maxLength={500}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">System Prompt</label>
          <textarea
            value={formData.system_prompt}
            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            placeholder="Define the persona's behavior and personality..."
            required
            rows={6}
            maxLength={2000}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white resize-none"
          />
          <div className="text-xs text-gray-500 mt-1">
            {formData.system_prompt.length}/2000 characters
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || !formData.name.trim() || !formData.description.trim() || !formData.system_prompt.trim()}
          >
            {isSubmitting ? (
              <>Saving...</>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                {persona ? 'Update' : 'Create'} Persona
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}

interface PersonaCardProps {
  persona: Persona;
  isEditing: boolean;
  onEdit: (persona: Persona) => void;
  onSave: (data: PersonaUpdate) => void;
  onDelete: () => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

function PersonaCard({
  persona,
  isEditing,
  onEdit,
  onSave,
  onDelete,
  onCancel,
  isSubmitting
}: PersonaCardProps) {
  if (isEditing) {
    return (
      <PersonaForm
        persona={persona}
        onSubmit={onSave}
        onCancel={onCancel}
        isSubmitting={isSubmitting}
      />
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{persona.icon}</span>
          <div>
            <h5 className="font-medium">{persona.name}</h5>
            {persona.is_default && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded dark:bg-green-900 dark:text-green-200">
                Default
              </span>
            )}
          </div>
        </div>
        {!persona.is_default && (
          <div className="flex space-x-1">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onEdit(persona)}
              disabled={isSubmitting}
            >
              <Edit3 className="w-3 h-3" />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onDelete}
              disabled={isSubmitting}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        {persona.description}
      </p>

      <details className="text-sm">
        <summary className="cursor-pointer text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
          View System Prompt
        </summary>
        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded text-xs font-mono whitespace-pre-wrap">
          {persona.system_prompt}
        </div>
      </details>
    </Card>
  );
}
