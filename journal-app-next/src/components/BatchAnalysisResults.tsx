import { useState } from 'react';
import { format } from 'date-fns';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrashIcon } from '@heroicons/react/24/outline';
import { ChartPieIcon, ListBulletIcon, ChartBarIcon, DocumentTextIcon, TagIcon } from '@heroicons/react/24/outline';
import type { BatchAnalysis } from '@/lib/types';

// Helper components
const EmptyState = ({ message }: { message: string }) => (
  <div className="flex flex-col items-center justify-center p-6 text-center border border-dashed rounded-lg border-muted">
    <p className="text-muted-foreground">{message}</p>
  </div>
);

const SectionCard = ({
  title,
  icon,
  children
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) => (
  <Card className="print-break-inside-avoid">
    <CardHeader className="pb-3">
      <div className="flex items-center space-x-2">
        <div className="bg-primary/10 p-1.5 rounded-md">
          {icon}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </div>
    </CardHeader>
    <CardContent>{children}</CardContent>
  </Card>
);

type BatchAnalysisResultsProps = {
  analysis: BatchAnalysis;
  onDelete?: () => void;
};

export default function BatchAnalysisResults({ analysis, onDelete }: BatchAnalysisResultsProps) {
  const [activeTab, setActiveTab] = useState('summary');

  // Format dates
  const createdDate = analysis.created_at
    ? format(new Date(analysis.created_at), 'MMMM d, yyyy')
    : 'Unknown date';

  // Handle undefined or null values
  const summary = analysis.summary || 'No summary was generated for this analysis.';
  const keyThemes = Array.isArray(analysis.key_themes) ? analysis.key_themes : [];
  const notableInsights = Array.isArray(analysis.notable_insights) ? analysis.notable_insights : [];
  const moodTrends = analysis.mood_trends && typeof analysis.mood_trends === 'object'
    ? analysis.mood_trends
    : {};
  const entryCount = Array.isArray(analysis.entry_ids) ? analysis.entry_ids.length : 0;

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:justify-between md:items-end space-y-3 md:space-y-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {analysis.title || 'Untitled Analysis'}
          </h1>
          <p className="text-muted-foreground mt-1">
            Created on {createdDate} • {entryCount} {entryCount === 1 ? 'entry' : 'entries'} analyzed
          </p>
          {analysis.date_range && (
            <Badge variant="outline" className="mt-2">
              {analysis.date_range}
            </Badge>
          )}
          {analysis.prompt_type && analysis.prompt_type !== 'default' && (
            <Badge variant="secondary" className="mt-2 ml-2">
              {analysis.prompt_type}
            </Badge>
          )}
        </div>

        {onDelete && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm" className="no-print">
                <TrashIcon className="h-4 w-4 mr-1" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete this analysis. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={onDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-4 mb-6 no-print">
          <TabsTrigger value="summary">
            <DocumentTextIcon className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Summary</span>
          </TabsTrigger>
          <TabsTrigger value="themes">
            <TagIcon className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Themes</span>
          </TabsTrigger>
          <TabsTrigger value="insights">
            <ListBulletIcon className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Insights</span>
          </TabsTrigger>
          <TabsTrigger value="mood">
            <ChartBarIcon className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Mood</span>
          </TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-6">
          <SectionCard
            title="Summary"
            icon={<DocumentTextIcon className="h-5 w-5 text-primary" />}
          >
            <div className="prose prose-sm max-w-none dark:prose-invert">
              {summary.split('\n').map((paragraph, index) => (
                paragraph ? <p key={index}>{paragraph}</p> : <br key={index} />
              ))}
            </div>
          </SectionCard>
        </TabsContent>

        {/* Themes Tab */}
        <TabsContent value="themes" className="space-y-6">
          <SectionCard
            title="Key Themes"
            icon={<TagIcon className="h-5 w-5 text-primary" />}
          >
            {keyThemes.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {keyThemes.map((theme, index) => (
                  <Badge key={index} variant="secondary">{theme}</Badge>
                ))}
              </div>
            ) : (
              <EmptyState message="No key themes were identified in this analysis." />
            )}
          </SectionCard>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          <SectionCard
            title="Notable Insights"
            icon={<ListBulletIcon className="h-5 w-5 text-primary" />}
          >
            {notableInsights.length > 0 ? (
              <ul className="space-y-2">
                {notableInsights.map((insight, index) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2 mt-1.5 h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState message="No notable insights were identified in this analysis." />
            )}
          </SectionCard>
        </TabsContent>

        {/* Mood Tab */}
        <TabsContent value="mood" className="space-y-6">
          <SectionCard
            title="Mood Trends"
            icon={<ChartBarIcon className="h-5 w-5 text-primary" />}
          >
            {Object.keys(moodTrends).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(moodTrends).map(([mood, count], index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="text-sm font-medium w-24 truncate">{mood}</div>
                    <div className="flex-1">
                      <div className="h-2 bg-primary/20 rounded-full">
                        <div
                          className="h-2 bg-primary rounded-full"
                          style={{
                            width: `${Math.min(Number(count) * 10, 100)}%`
                          }}
                        />
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">{count}</div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState message="No mood data was identified in this analysis." />
            )}
          </SectionCard>
        </TabsContent>
      </Tabs>

      {/* Print view - shown when printing but hidden on screen */}
      <div className="hidden print:block space-y-8 mt-10">
        <SectionCard
          title="Summary"
          icon={<DocumentTextIcon className="h-5 w-5 text-primary" />}
        >
          <div className="prose prose-sm max-w-none">
            {summary.split('\n').map((paragraph, index) => (
              paragraph ? <p key={index}>{paragraph}</p> : <br key={index} />
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Key Themes"
          icon={<TagIcon className="h-5 w-5 text-primary" />}
        >
          {keyThemes.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {keyThemes.map((theme, index) => (
                <Badge key={index} variant="secondary">{theme}</Badge>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No key themes were identified.</p>
          )}
        </SectionCard>

        <SectionCard
          title="Notable Insights"
          icon={<ListBulletIcon className="h-5 w-5 text-primary" />}
        >
          {notableInsights.length > 0 ? (
            <ul className="space-y-2">
              {notableInsights.map((insight, index) => (
                <li key={index} className="flex items-start">
                  <span className="mr-2 mt-1.5 h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground">No notable insights were identified.</p>
          )}
        </SectionCard>

        <SectionCard
          title="Mood Trends"
          icon={<ChartBarIcon className="h-5 w-5 text-primary" />}
        >
          {Object.keys(moodTrends).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(moodTrends).map(([mood, count], index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="text-sm font-medium w-24 truncate">{mood}</div>
                  <div className="flex-1">
                    <div className="h-2 bg-primary/20 rounded-full">
                      <div
                        className="h-2 bg-primary rounded-full"
                        style={{
                          width: `${Math.min(Number(count) * 10, 100)}%`
                        }}
                      />
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">{count}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No mood data was identified.</p>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
