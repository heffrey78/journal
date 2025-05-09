'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeftIcon,
  PrinterIcon,
  DocumentArrowDownIcon,
  ShareIcon
} from '@heroicons/react/24/outline';
import { batchAnalysisApi } from '@/lib/api';
import type { BatchAnalysis } from '@/lib/types';
import BatchAnalysisResults from '@/components/BatchAnalysisResults';
import MainLayout from '@/components/layout/MainLayout';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export default function BatchAnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [analysis, setAnalysis] = useState<BatchAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showShareTooltip, setShowShareTooltip] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  // Fetch batch analysis data
  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!id) return; // Skip if no ID available yet

      try {
        setLoading(true);
        console.log(`Fetching analysis with ID: ${id} (attempt ${retryCount + 1})`);
        const data = await batchAnalysisApi.getBatchAnalysis(id);

        if (!data) {
          throw new Error(`Analysis with ID ${id} not found`);
        }

        setAnalysis(data);
        setError(null);
      } catch (error) {
        console.error('Error fetching analysis:', error);

        // Check if we should retry
        if (retryCount < maxRetries) {
          setRetryCount(prev => prev + 1);
          setError(`Error loading analysis. Retrying... (${retryCount + 1}/${maxRetries})`);
          return; // Don't set loading to false yet
        } else {
          setError('Failed to load analysis. It may have been deleted or does not exist.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [id, retryCount]); // Retry when retryCount changes

  // Handle deletion
  const handleDelete = async () => {
    if (!id) return;

    try {
      await batchAnalysisApi.deleteBatchAnalysis(id);
      router.push('/analyses');
    } catch (error) {
      console.error('Error deleting analysis:', error);
      alert('Failed to delete analysis. Please try again.');
    }
  };

  // Handle printing
  const handlePrint = () => {
    window.print();
  };

  // Handle export as text
  const handleExport = () => {
    if (!analysis) return;

    try {
      // Create a text representation of the analysis
      const exportText = `
# ${analysis.title || 'Untitled Analysis'}
Date Range: ${analysis.date_range || 'Unknown date range'}
Analysis Type: ${analysis.prompt_type || 'default'}
Created: ${new Date(analysis.created_at || Date.now()).toLocaleString()}

## Summary
${analysis.summary || 'No summary available.'}

## Key Themes
${Array.isArray(analysis.key_themes) ? analysis.key_themes.join(', ') : 'No key themes available.'}

## Notable Insights
${Array.isArray(analysis.notable_insights) ? analysis.notable_insights.map(insight => `- ${insight}`).join('\n') : 'No notable insights available.'}

## Mood Trends
${analysis.mood_trends ? Object.entries(analysis.mood_trends).map(([mood, count]) => `- ${mood}: ${count}`).join('\n') : 'No mood data available.'}
`;

      // Create a Blob and download link
      const blob = new Blob([exportText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${analysis.title || 'journal-analysis'}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting analysis:', error);
      alert('Failed to export analysis. Please try again.');
    }
  };

  // Handle share (copy link)
  const handleShare = () => {
    try {
      const url = window.location.href;
      navigator.clipboard.writeText(url);
      setShowShareTooltip(true);
      setTimeout(() => setShowShareTooltip(false), 2000);
    } catch (error) {
      console.error('Error copying link:', error);
      alert('Failed to copy link. Please try again.');
    }
  };

  return (
    <MainLayout>
      {loading ? (
        <div className="container max-w-4xl mx-auto p-4">
          <div className="flex items-center justify-start mb-6">
            <Link href="/analyses" className="inline-flex items-center text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              <ArrowLeftIcon className="h-4 w-4 mr-1" />
              <span>Back to Analyses</span>
            </Link>
          </div>
          <div className="flex items-center justify-center p-12">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
          </div>
        </div>
      ) : error ? (
        <div className="container max-w-4xl mx-auto p-4">
          <div className="flex items-center justify-start mb-6">
            <Link href="/analyses" className="inline-flex items-center text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              <ArrowLeftIcon className="h-4 w-4 mr-1" />
              <span>Back to Analyses</span>
            </Link>
          </div>
          <div className="bg-destructive/10 dark:bg-destructive/20 border border-destructive/20 text-destructive rounded-lg p-6 text-center">
            <p className="text-lg font-semibold">{error}</p>
            <div className="mt-4">
              <Button onClick={() => setRetryCount(prev => prev + 1)} variant="outline">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      ) : !analysis ? (
        <div className="container max-w-4xl mx-auto p-4">
          <div className="flex items-center justify-start mb-6">
            <Link href="/analyses" className="inline-flex items-center text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              <ArrowLeftIcon className="h-4 w-4 mr-1" />
              <span>Back to Analyses</span>
            </Link>
          </div>
          <div className="bg-muted rounded-lg p-6 text-center">
            <p className="text-muted-foreground">Analysis not found</p>
          </div>
        </div>
      ) : (
        <div className="container max-w-4xl mx-auto p-4" ref={contentRef}>
          <div className="flex items-center justify-between mb-6 no-print">
            <Link href="/analyses" className="inline-flex items-center text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">
              <ArrowLeftIcon className="h-4 w-4 mr-1" />
              <span>Back to Analyses</span>
            </Link>

            <div className="flex items-center space-x-2">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handlePrint}
                      className="h-9 w-9"
                    >
                      <PrinterIcon className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Print</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleExport}
                      className="h-9 w-9"
                    >
                      <DocumentArrowDownIcon className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Export as text</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip open={showShareTooltip}>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleShare}
                      className="h-9 w-9"
                    >
                      <ShareIcon className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {showShareTooltip ? 'Link copied!' : 'Copy link'}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>

          {/* Main content */}
          <BatchAnalysisResults
            analysis={analysis}
            onDelete={handleDelete}
          />
        </div>
      )}
    </MainLayout>
  );
}
