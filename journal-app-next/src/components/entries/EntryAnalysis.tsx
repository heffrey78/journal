import React, { useState, useEffect } from 'react';
import { EntrySummary, entriesApi } from '@/lib/api';
import { llmApi } from '@/lib/api';
import { PromptType } from '@/lib/types';
import Button from '@/components/ui/Button';

interface EntryAnalysisProps {
  entryId: string;
}

// Default prompt types as a fallback
const DEFAULT_PROMPT_TYPES = [
  { id: 'default', name: 'Default Summary', prompt: '' },
  { id: 'detailed', name: 'Detailed Analysis', prompt: '' },
  { id: 'creative', name: 'Creative Insights', prompt: '' },
  { id: 'concise', name: 'Concise Summary', prompt: '' }
];

const EntryAnalysis: React.FC<EntryAnalysisProps> = ({ entryId }) => {
  const [promptTypes, setPromptTypes] = useState<PromptType[]>(DEFAULT_PROMPT_TYPES);
  const [promptType, setPromptType] = useState('default');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentSummary, setCurrentSummary] = useState<EntrySummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [favoriteSummaries, setFavoriteSummaries] = useState<EntrySummary[]>([]);
  const [showFavoriteSummaries, setShowFavoriteSummaries] = useState(false);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);

  // Load prompt types from LLM config
  useEffect(() => {
    const loadPromptTypes = async () => {
      try {
        const config = await llmApi.getLLMConfig();
        if (config.prompt_types && config.prompt_types.length > 0) {
          setPromptTypes(config.prompt_types);
        }
      } catch (err) {
        console.error('Failed to load prompt types from config:', err);
      } finally {
        setIsLoadingConfig(false);
      }
    };

    loadPromptTypes();
  }, []);

  // Fetch favorite summaries on initial load
  useEffect(() => {
    fetchFavoriteSummaries();
  }, [entryId]);

  const fetchFavoriteSummaries = async () => {
    try {
      const summaries = await entriesApi.getFavoriteSummaries(entryId);
      setFavoriteSummaries(summaries);
      setShowFavoriteSummaries(summaries.length > 0);
    } catch (err) {
      console.error('Failed to fetch favorite summaries:', err);
    }
  };

  const handleAnalyzeEntry = async () => {
    setIsAnalyzing(true);
    setError(null);
    setProgress(10);
    setCurrentSummary(null);

    // Create a simulation of progress for better UX
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = Math.min(prev + 10, 90);
        return newProgress;
      });
    }, 500);

    try {
      const summary = await entriesApi.summarizeEntry(entryId, promptType);
      clearInterval(progressInterval);
      setProgress(100);
      setCurrentSummary(summary);

      // Hide progress bar after a delay
      setTimeout(() => {
        setIsAnalyzing(false);
        setProgress(0);
      }, 1000);
    } catch (err) {
      clearInterval(progressInterval);
      console.error('Failed to analyze entry:', err);
      setError('Failed to generate analysis. Please ensure Ollama is running on your system.');
      setIsAnalyzing(false);
      setProgress(0);
    }
  };

  const handleSaveAsFavorite = async () => {
    if (!currentSummary) return;

    try {
      await entriesApi.saveFavoriteSummary(entryId, {
        ...currentSummary,
        prompt_type: promptType
      });

      // Refetch favorites to update the list
      await fetchFavoriteSummaries();
    } catch (err) {
      console.error('Failed to save favorite summary:', err);
      setError('Failed to save as favorite. Please try again.');
    }
  };

  // Find the selected prompt type name
  const getSelectedPromptTypeName = () => {
    const promptTypeObj = promptTypes.find(pt => pt.id === promptType);
    return promptTypeObj?.name || promptType;
  };

  return (
    <div className="mt-8 bg-card text-card-foreground rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4">
        AI Entry Analysis
      </h2>

      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-4">
          <div className="flex-grow">
            <label htmlFor="prompt-type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Analysis Type:
            </label>
            {isLoadingConfig ? (
              <div className="w-full sm:w-auto px-3 py-2 border border-border rounded-md bg-card text-muted-foreground">
                Loading options...
              </div>
            ) : (
              <select
                id="prompt-type"
                value={promptType}
                onChange={(e) => setPromptType(e.target.value)}
                className="w-full sm:w-auto px-3 py-2 border border-border rounded-md bg-card text-card-foreground"
                disabled={isAnalyzing}
              >
                {promptTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.name}
                  </option>
                ))}
              </select>
            )}
          </div>
          <div className="mt-2 sm:mt-0">
            <Button
              onClick={handleAnalyzeEntry}
              isLoading={isAnalyzing}
              disabled={isAnalyzing || isLoadingConfig}
              size="md"
            >
              Analyze Entry
            </Button>
          </div>
        </div>

        {isAnalyzing && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-in-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {progress < 30 ? 'Processing entry content...' :
               progress < 60 ? 'Analyzing themes and patterns...' :
               'Finalizing results...'}
            </p>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-300 p-4 rounded">
            <p>{error}</p>
            <Button
              className="mt-2"
              onClick={handleAnalyzeEntry}
              size="sm"
              variant="outline"
            >
              Retry
            </Button>
          </div>
        )}

        {currentSummary && !isAnalyzing && (
          <div className="mt-4">
            <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/20 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Analysis Results</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveAsFavorite}
                >
                  Save as Favorite
                </Button>
              </div>

              <div className="prose dark:prose-invert prose-sm max-w-none">
                <p className="mb-3"><strong>Summary:</strong> {currentSummary.summary}</p>

                <div className="mb-3">
                  <strong>Key Topics:</strong>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {currentSummary.key_topics.map((topic, index) => (
                      <span
                        key={index}
                        className="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>

                <p className="mb-1"><strong>Detected Mood:</strong> {currentSummary.mood}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Analysis type: {getSelectedPromptTypeName()}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Favorite Summaries Section */}
      {showFavoriteSummaries && favoriteSummaries.length > 0 && (
        <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
            Saved Analyses
          </h3>

          <div className="space-y-4">
            {favoriteSummaries.map((summary, index) => (
              <div
                key={index}
                className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4"
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">Saved Analysis</h4>
                  <span className="text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 px-2 py-1 rounded">
                    {summary.prompt_type || 'Default'}
                  </span>
                </div>

                <p className="text-sm mb-3">{summary.summary}</p>

                <div className="mb-2">
                  <div className="flex flex-wrap gap-1 mt-1">
                    {summary.key_topics.map((topic, topicIndex) => (
                      <span
                        key={topicIndex}
                        className="bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 px-2 py-0.5 rounded text-xs"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="text-xs text-gray-500 dark:text-gray-400 flex justify-between">
                  <span>Mood: {summary.mood}</span>
                  {summary.created_at && (
                    <span>Saved on {new Date(summary.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EntryAnalysis;
