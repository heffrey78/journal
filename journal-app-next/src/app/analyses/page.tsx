'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import MainLayout from '@/components/layout/MainLayout';
import { batchAnalysisApi } from '@/lib/api';
import { BatchAnalysis } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { ChartBarIcon, ClockIcon } from '@heroicons/react/24/outline';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

export default function AnalysesPage() {
  const [analyses, setAnalyses] = useState<BatchAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        setLoading(true);
        const data = await batchAnalysisApi.getBatchAnalyses();
        setAnalyses(data);
      } catch (err) {
        console.error('Failed to load analyses:', err);
        setError('Failed to load analyses. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyses();
  }, []);

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy');
    } catch {
      return 'Unknown date';
    }
  };

  // Generate a truncated summary
  const truncateSummary = (summary: string | undefined, maxLength = 150) => {
    if (!summary) return 'No summary available';
    return summary.length > maxLength ? `${summary.substring(0, maxLength)}...` : summary;
  };

  return (
    <MainLayout>
      <div className="container max-w-5xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Batch Analyses</h1>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((key) => (
              <Card key={key} className="shadow-sm">
                <CardHeader>
                  <Skeleton className="h-6 w-2/3 mb-2" />
                  <Skeleton className="h-4 w-1/3" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-3/4" />
                </CardContent>
                <CardFooter>
                  <div className="w-full flex justify-between">
                    <Skeleton className="h-4 w-1/4" />
                    <Skeleton className="h-9 w-20" />
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-800 dark:text-red-300">{error}</p>
            <Button
              onClick={() => window.location.reload()}
              className="mt-4"
              size="sm"
            >
              Try Again
            </Button>
          </div>
        ) : analyses.length === 0 ? (
          <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center">
            <ChartBarIcon className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No analyses yet</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
              Select multiple entries from your journal to create your first batch analysis.
            </p>
            <Link href="/entries" className="inline-block">
              <Button>Browse Entries</Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {analyses.map((analysis) => (
              <Link href={`/analyses/${analysis.id}`} key={analysis.id} className="block group">
                <Card className="h-full hover:border-primary/50 transition-colors shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between">
                      <div>
                        <CardTitle className="group-hover:text-primary transition-colors">
                          {analysis.title || 'Untitled Analysis'}
                        </CardTitle>
                        <CardDescription className="flex items-center mt-1">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {formatDate(analysis.created_at)}
                        </CardDescription>
                      </div>
                      <div className="bg-primary/10 rounded-md p-1.5 h-fit">
                        <ChartBarIcon className="h-5 w-5 text-primary" />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-muted-foreground line-clamp-3">
                      {truncateSummary(analysis.summary)}
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {analysis.prompt_type && (
                        <Badge variant="secondary">
                          {analysis.prompt_type}
                        </Badge>
                      )}
                      {analysis.key_themes && analysis.key_themes.length > 0 && (
                        <Badge variant="outline">
                          {analysis.key_themes.length} themes
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                  <CardFooter>
                    <div className="flex justify-between items-center w-full">
                      <span className="text-sm text-muted-foreground">
                        {analysis.entry_ids?.length || 0} {analysis.entry_ids?.length === 1 ? 'entry' : 'entries'}
                      </span>
                      <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 transition-opacity">
                        View Analysis
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
