'use client';

import React, { useState } from 'react';
import { Search, Clock, CheckCircle, AlertCircle, Database, Globe, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { ToolUsage } from './types';

interface ToolUsageIndicatorProps {
  toolsUsed?: ToolUsage[];
  className?: string;
}

const getToolIcon = (toolName: string) => {
  switch (toolName) {
    case 'journal_search':
      return Search;
    case 'web_search':
      return Globe;
    default:
      return Database;
  }
};

const getToolDisplayName = (toolName: string) => {
  switch (toolName) {
    case 'journal_search':
      return 'Journal Search';
    case 'web_search':
      return 'Web Search';
    default:
      return toolName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
};

export default function ToolUsageIndicator({ toolsUsed, className = '' }: ToolUsageIndicatorProps) {
  if (!toolsUsed || !Array.isArray(toolsUsed) || toolsUsed.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-1 ${className}`}>
      {toolsUsed.map((tool, index) => {
        if (!tool || typeof tool !== 'object') {
          console.error('Invalid tool object:', tool);
          return null;
        }

        return <ToolResultCard key={index} tool={tool} />;
      })}
    </div>
  );
}

interface ToolResultCardProps {
  tool: ToolUsage;
}

function ToolResultCard({ tool }: ToolResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const IconComponent = getToolIcon(tool.tool_name || 'unknown');
  const displayName = getToolDisplayName(tool.tool_name || 'unknown');

  const hasResults = tool.results && tool.results.length > 0;
  const canExpand = hasResults && tool.result_count && tool.result_count > 0;

  return (
    <div
      className={`text-xs border rounded-md ${
        tool.success === true
          ? 'bg-blue-50 text-blue-700 border-blue-200'
          : 'bg-red-50 text-red-700 border-red-200'
      }`}
    >
      {/* Main tool info row */}
      <div
        className={`flex items-center px-2 py-1 ${canExpand ? 'cursor-pointer hover:bg-opacity-80' : ''}`}
        onClick={canExpand ? () => setExpanded(!expanded) : undefined}
      >
        <IconComponent className="h-3 w-3 mr-1.5" />
        <span className="font-medium mr-2">{displayName}</span>

        {tool.success === true ? (
          <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
        ) : (
          <AlertCircle className="h-3 w-3 text-red-600 mr-1" />
        )}

        <div className="flex items-center gap-2 text-xs opacity-75">
          {tool.result_count !== undefined && (
            <span>{tool.result_count} results</span>
          )}

          {tool.execution_time_ms !== undefined && tool.execution_time_ms !== null && (
            <div className="flex items-center gap-0.5">
              <Clock className="h-2.5 w-2.5" />
              <span>{Number(tool.execution_time_ms).toFixed(0)}ms</span>
            </div>
          )}

          {tool.confidence !== undefined && tool.confidence !== null && (
            <span className="font-mono">
              {(Number(tool.confidence) * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {tool.error && (
          <span className="ml-auto text-xs text-red-600 truncate max-w-32" title={tool.error}>
            {tool.error}
          </span>
        )}

        {canExpand && (
          <div className="ml-auto">
            {expanded ? (
              <ChevronUp className="h-3 w-3 opacity-60" />
            ) : (
              <ChevronDown className="h-3 w-3 opacity-60" />
            )}
          </div>
        )}
      </div>

      {/* Expanded results */}
      {expanded && hasResults && (
        <div className="border-t border-current border-opacity-20 px-2 py-1">
          <ToolResults tool={tool} />
        </div>
      )}
    </div>
  );
}

interface ToolResultsProps {
  tool: ToolUsage;
}

function ToolResults({ tool }: ToolResultsProps) {
  if (!tool.results || tool.results.length === 0) {
    return null;
  }

  if (tool.tool_name === 'journal_search') {
    return (
      <div className="space-y-1">
        {tool.results.slice(0, 5).map((result, index) => (
          <div key={index} className="flex flex-col space-y-0.5">
            <div className="font-medium text-xs">
              {result.title || 'Untitled Entry'}
            </div>
            {result.content_preview && (
              <div className="text-xs opacity-75 max-h-8 overflow-hidden">
                {result.content_preview}
              </div>
            )}
            <div className="flex items-center gap-2 text-xs opacity-60">
              {result.date && <span>{result.date}</span>}
              {result.relevance && (
                <span className="font-mono">
                  {Math.round(result.relevance * 100)}% match
                </span>
              )}
            </div>
          </div>
        ))}
        {tool.results.length > 5 && (
          <div className="text-xs opacity-60 italic">
            +{tool.results.length - 5} more results...
          </div>
        )}
      </div>
    );
  }

  if (tool.tool_name === 'web_search') {
    return (
      <div className="space-y-1">
        {tool.results.slice(0, 5).map((result, index) => (
          <div key={index} className="flex flex-col space-y-0.5">
            <div className="flex items-start gap-1">
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-xs hover:underline flex items-center gap-1 text-blue-600"
              >
                {result.title || 'Untitled'}
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
            </div>
            {result.snippet && (
              <div className="text-xs opacity-75 max-h-8 overflow-hidden">
                {result.snippet}
              </div>
            )}
            <div className="flex items-center gap-2 text-xs opacity-60">
              {(result.source_domain || result.source) && <span>{result.source_domain || result.source}</span>}
              {result.published && <span>{result.published}</span>}
            </div>
          </div>
        ))}
        {tool.results.length > 5 && (
          <div className="text-xs opacity-60 italic">
            +{tool.results.length - 5} more results...
          </div>
        )}
      </div>
    );
  }

  return null;
}

interface ToolActivityIndicatorProps {
  isActive: boolean;
  toolName?: string;
  className?: string;
}

export function ToolActivityIndicator({ isActive, toolName, className = '' }: ToolActivityIndicatorProps) {
  if (!isActive) {
    return null;
  }

  const IconComponent = getToolIcon(toolName || 'unknown');
  const displayName = getToolDisplayName(toolName || 'Tool');

  return (
    <div className={`flex items-center text-xs px-3 py-2 bg-blue-50 text-blue-700 border border-blue-200 rounded-md ${className}`}>
      <IconComponent className="h-3 w-3 mr-2 animate-pulse" />
      <span className="font-medium">{displayName} is searching...</span>

      {/* Animated dots */}
      <div className="ml-2 flex space-x-0.5">
        <div className="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  );
}
