# Batch Analysis Feature Plan

## Feature Overview

The batch analysis feature will allow users to select multiple entries (e.g., entries from a week or entries with a specific tag) and generate an analysis that summarizes key themes, insights, and patterns across these entries. This builds upon the existing capabilities for individual entry analysis and the batch operations support implemented in Commit 27.

## Key Components

### 1. Backend API Enhancements

First, we need to extend the LLM service to support batch analysis:

1. **Batch Analysis Endpoint**: Add an endpoint to process multiple entries and generate a consolidated analysis
2. **Analysis Models**: Create data models for batch analysis results
3. **Storage Support**: Add functionality to save and retrieve batch analyses

### 2. Frontend UI Components

Next, we'll add UI components to enable selection and analysis of multiple entries:

1. **Entry Selection**: Enhance the entries page with multi-select capabilities 
2. **Analysis Configuration**: Create an interface for configuring batch analysis parameters
3. **Results Display**: Design a view to display and interact with batch analysis results

## Detailed Implementation Plan

### 1. Backend Implementation

#### 1.1 Create Batch Analysis Models
We'll need to create a model for batch analysis results:

```python
class BatchAnalysis(BaseModel):
    """Model for batch analysis of multiple journal entries."""
    id: str
    title: str
    entry_ids: List[str]
    date_range: Optional[str]
    created_at: str
    summary: str
    key_themes: List[str]
    mood_trends: Dict[str, int]
    notable_insights: List[str]
    prompt_type: Optional[str] = None
```

#### 1.2 Extend LLM Service for Batch Analysis
We'll add a method to the LLM service to analyze multiple entries:

```python
def analyze_entries_batch(
    self,
    entries: List[Dict[str, Any]],
    title: str = "",
    prompt_type: str = "weekly",
    progress_callback: Optional[Callable[[float], None]] = None,
) -> BatchAnalysis:
    """
    Generate an analysis for a batch of journal entries.
    
    Args:
        entries: List of entries to analyze
        title: Title for the batch analysis
        prompt_type: Type of analysis to perform (weekly, monthly, topic, etc.)
        progress_callback: Optional function to report progress
        
    Returns:
        A BatchAnalysis object with the results
    """
    # Implementation details here
```

#### 1.3 Add API Endpoints
We'll add endpoints to create and retrieve batch analyses:

```python
@app.post("/batch/analyze", response_model=BatchAnalysis, tags=["batch"])
async def analyze_entries_batch(
    request: BatchAnalysisRequest,
    llm: LLMService = Depends(get_llm_service),
    storage: StorageManager = Depends(get_storage),
):
    """Generate an analysis for a batch of journal entries."""
    # Implementation details here
```

### 2. Frontend Implementation

#### 2.1 Enhance Entry List with Multi-Select

Build on the existing `EntryList` component that already supports selecting multiple entries for batch operations:

```tsx
// Add to EntryList.tsx
const [batchAnalysisDialogOpen, setBatchAnalysisDialogOpen] = useState(false);

// Add batch analysis button to the action bar next to the Move Entries button
<button
  onClick={() => setBatchAnalysisDialogOpen(true)}
  disabled={selectedEntries.length === 0 || isProcessing}
  className={`flex items-center space-x-1 px-3 py-1.5 text-sm rounded ${
    selectedEntries.length > 0
      ? 'bg-indigo-600 text-white hover:bg-indigo-700'
      : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
  }`}
>
  <span>Analyze {selectedEntries.length > 0 ? `(${selectedEntries.length})` : ''}</span>
</button>
```

#### 2.2 Create Batch Analysis Dialog

Create a dialog to configure and initiate batch analysis:

```tsx
// BatchAnalysisDialog.tsx
interface BatchAnalysisDialogProps {
  entryIds: string[];
  isOpen: boolean;
  onClose: () => void;
}

const BatchAnalysisDialog: React.FC<BatchAnalysisDialogProps> = ({
  entryIds,
  isOpen,
  onClose
}) => {
  const [title, setTitle] = useState('');
  const [promptType, setPromptType] = useState('weekly');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  
  // Handle the analysis request
  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      // Call API to analyze entries
      const result = await batchApi.analyzeEntries({
        entryIds,
        title: title || `Analysis of ${entryIds.length} entries`,
        promptType
      });
      
      // Redirect to the analysis result page
      router.push(`/batch-analysis/${result.id}`);
    } catch (error) {
      console.error('Failed to analyze entries:', error);
    } finally {
      setIsAnalyzing(false);
      onClose();
    }
  };
  
  // Rest of dialog implementation
};
```

#### 2.3 Create Batch Analysis Results View

Design a view to display the results of batch analyses:

```tsx
// BatchAnalysisResults.tsx
interface BatchAnalysisResultsProps {
  batchAnalysis: BatchAnalysis;
}

const BatchAnalysisResults: React.FC<BatchAnalysisResultsProps> = ({
  batchAnalysis
}) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{batchAnalysis.title}</h2>
      
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">Summary</h3>
        <p className="text-gray-700 dark:text-gray-300">{batchAnalysis.summary}</p>
      </div>
      
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">Key Themes</h3>
        <div className="flex flex-wrap gap-2">
          {batchAnalysis.key_themes.map((theme, i) => (
            <span key={i} className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full">
              {theme}
            </span>
          ))}
        </div>
      </div>
      
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">Notable Insights</h3>
        <ul className="list-disc list-inside">
          {batchAnalysis.notable_insights.map((insight, i) => (
            <li key={i} className="text-gray-700 dark:text-gray-300">{insight}</li>
          ))}
        </ul>
      </div>
      
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">Mood Trends</h3>
        {/* Mood visualization component would go here */}
      </div>
      
      <div className="mt-4 text-sm text-gray-500">
        <p>Analysis of {batchAnalysis.entry_ids.length} entries from {batchAnalysis.date_range || 'selected period'}</p>
        <p>Created on {new Date(batchAnalysis.created_at).toLocaleString()}</p>
      </div>
    </div>
  );
};
```

### 3. Storage Extensions

#### 3.1 Add Tables for Batch Analyses

Update the database schema to store batch analyses:

```python
def create_batch_analyses_table(self):
    """Create the batch analyses table if it doesn't exist."""
    self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS batch_analyses (
        id TEXT PRIMARY KEY,
        title TEXT,
        date_range TEXT,
        summary TEXT,
        key_themes TEXT,
        mood_trends TEXT,
        notable_insights TEXT,
        prompt_type TEXT,
        created_at TEXT
    )
    ''')
    
    self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS batch_analysis_entries (
        batch_id TEXT,
        entry_id TEXT,
        PRIMARY KEY (batch_id, entry_id),
        FOREIGN KEY (batch_id) REFERENCES batch_analyses(id) ON DELETE CASCADE,
        FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE
    )
    ''')
    self.connection.commit()
```

#### 3.2 Add Methods to Save and Retrieve Batch Analyses

Add methods to save and retrieve batch analyses:

```python
def save_batch_analysis(self, analysis: BatchAnalysis) -> bool:
    """Save a batch analysis to the database."""
    try:
        # Convert complex types to JSON strings
        key_themes_json = json.dumps(analysis.key_themes)
        mood_trends_json = json.dumps(analysis.mood_trends)
        notable_insights_json = json.dumps(analysis.notable_insights)
        
        # Insert into batch_analyses table
        self.cursor.execute(
            '''
            INSERT OR REPLACE INTO batch_analyses
            (id, title, date_range, summary, key_themes, mood_trends, 
             notable_insights, prompt_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                analysis.id,
                analysis.title,
                analysis.date_range,
                analysis.summary,
                key_themes_json,
                mood_trends_json,
                notable_insights_json,
                analysis.prompt_type,
                analysis.created_at or datetime.now().isoformat(),
            ),
        )
        
        # Insert entry associations into batch_analysis_entries table
        for entry_id in analysis.entry_ids:
            self.cursor.execute(
                '''
                INSERT OR REPLACE INTO batch_analysis_entries
                (batch_id, entry_id)
                VALUES (?, ?)
                ''',
                (analysis.id, entry_id),
            )
        
        self.connection.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to save batch analysis: {e}")
        self.connection.rollback()
        return False

def get_batch_analysis(self, batch_id: str) -> Optional[BatchAnalysis]:
    """Get a batch analysis by ID."""
    # Implementation details here

def get_batch_analyses(self, limit: int = 10, offset: int = 0) -> List[BatchAnalysis]:
    """Get a list of batch analyses with pagination."""
    # Implementation details here
```

## Use Cases to Support

### 1. Weekly Review
Users can select all entries from the past week and generate a weekly reflection that highlights patterns, recurring themes, and emotional trends.

### 2. Topic-Based Analysis
Users can select entries with a specific tag or search result and analyze them as a group to identify insights about a particular topic.

### 3. Project Reflection
Users can select entries related to a specific project or goal and generate an analysis of their progress, challenges, and insights.

### 4. Mood Tracking
Users can analyze entries over time to track mood trends and identify patterns in emotional states.

## Implementation Schedule

The feature should be implemented in the following steps:

1. First, add the backend models and storage extensions
2. Next, implement the batch analysis method in the LLM service
3. Then add the API endpoints
4. Integrate the multi-select functionality in the entry list UI
5. Add the batch analysis dialog and results view
6. Add navigation and management of saved batch analyses
7. Test and refine the feature

## Technical Considerations

1. **Performance**: For large batches of entries, the analysis might take significant time. Consider implementing a background job system for processing.

2. **Token Limits**: LLM context windows have limits. For large batches, implement chunking and summarization strategies.

3. **Error Handling**: Implement robust error handling for when the analysis fails or the LLM service is unavailable.

4. **User Experience**: Provide clear feedback on progress during analysis, especially for large batches.

5. **Storage**: Batch analyses might be large. Ensure the database can handle the size and implement pagination for displaying results.