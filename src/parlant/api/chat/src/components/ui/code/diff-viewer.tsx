import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '../button';
import { Copy, Check, ArrowLeftRight, Code2 } from 'lucide-react';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';
import { Tooltip } from '../custom/tooltip';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../tabs';

interface DiffViewerProps {
  oldCode: string;
  newCode: string;
  language?: string;
  showLineNumbers?: boolean;
  showCopyButton?: boolean;
  className?: string;
  fileName?: string;
  diffMode?: 'split' | 'unified';
}

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
  lineNumber: number;
}

const computeDiff = (oldCode: string, newCode: string): { oldLines: DiffLine[], newLines: DiffLine[] } => {
  const oldLines = oldCode.split('\n');
  const newLines = newCode.split('\n');
  
  // Simple diff algorithm (this is a simplified version, in a real app you'd use a proper diff library)
  const result = {
    oldLines: [] as DiffLine[],
    newLines: [] as DiffLine[],
  };
  
  let i = 0, j = 0;
  
  while (i < oldLines.length || j < newLines.length) {
    if (i < oldLines.length && j < newLines.length && oldLines[i] === newLines[j]) {
      // Unchanged line
      result.oldLines.push({ type: 'unchanged', content: oldLines[i], lineNumber: i + 1 });
      result.newLines.push({ type: 'unchanged', content: newLines[j], lineNumber: j + 1 });
      i++;
      j++;
    } else if (j < newLines.length && (i >= oldLines.length || oldLines[i] !== newLines[j])) {
      // Added line
      result.newLines.push({ type: 'added', content: newLines[j], lineNumber: j + 1 });
      j++;
    } else if (i < oldLines.length && (j >= newLines.length || oldLines[i] !== newLines[j])) {
      // Removed line
      result.oldLines.push({ type: 'removed', content: oldLines[i], lineNumber: i + 1 });
      i++;
    }
  }
  
  return result;
};

const DiffViewer: React.FC<DiffViewerProps> = ({
  oldCode,
  newCode,
  language,
  showLineNumbers = true,
  showCopyButton = true,
  className,
  fileName,
  diffMode = 'split',
}) => {
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<'split' | 'unified'>(diffMode);
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';
  
  const diff = computeDiff(oldCode, newCode);
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(newCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const getLineStyle = (type: DiffLine['type']): React.CSSProperties => {
    if (type === 'added') {
      return { backgroundColor: isDarkTheme ? 'rgba(0, 255, 0, 0.1)' : 'rgba(0, 255, 0, 0.2)' };
    } else if (type === 'removed') {
      return { backgroundColor: isDarkTheme ? 'rgba(255, 0, 0, 0.1)' : 'rgba(255, 0, 0, 0.2)' };
    }
    return {};
  };
  
  const renderSplitView = () => (
    <div className="grid grid-cols-2 gap-0">
      <div className="border-r border-slate-300 dark:border-slate-700">
        <div className="text-xs text-slate-500 dark:text-slate-400 p-2 bg-slate-100 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-700">
          Old
        </div>
        <SyntaxHighlighter
          language={language || 'text'}
          style={isDarkTheme ? vscDarkPlus : vs}
          showLineNumbers={showLineNumbers}
          wrapLines={true}
          lineProps={(lineNumber) => {
            const line = diff.oldLines.find(l => l.lineNumber === lineNumber);
            return { style: line ? getLineStyle(line.type) : {} };
          }}
          customStyle={{
            margin: 0,
            borderRadius: 0,
            padding: '1rem',
          }}
        >
          {oldCode}
        </SyntaxHighlighter>
      </div>
      <div>
        <div className="text-xs text-slate-500 dark:text-slate-400 p-2 bg-slate-100 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-700">
          New
        </div>
        <SyntaxHighlighter
          language={language || 'text'}
          style={isDarkTheme ? vscDarkPlus : vs}
          showLineNumbers={showLineNumbers}
          wrapLines={true}
          lineProps={(lineNumber) => {
            const line = diff.newLines.find(l => l.lineNumber === lineNumber);
            return { style: line ? getLineStyle(line.type) : {} };
          }}
          customStyle={{
            margin: 0,
            borderRadius: 0,
            padding: '1rem',
          }}
        >
          {newCode}
        </SyntaxHighlighter>
      </div>
    </div>
  );
  
  const renderUnifiedView = () => {
    // Combine old and new lines for unified view
    const unifiedLines: { content: string; type: DiffLine['type'] }[] = [];
    
    let i = 0, j = 0;
    while (i < diff.oldLines.length || j < diff.newLines.length) {
      if (i < diff.oldLines.length && diff.oldLines[i].type === 'removed') {
        unifiedLines.push({ content: diff.oldLines[i].content, type: 'removed' });
        i++;
      } else if (j < diff.newLines.length && diff.newLines[j].type === 'added') {
        unifiedLines.push({ content: diff.newLines[j].content, type: 'added' });
        j++;
      } else if (i < diff.oldLines.length && j < diff.newLines.length) {
        unifiedLines.push({ content: diff.newLines[j].content, type: 'unchanged' });
        i++;
        j++;
      }
    }
    
    const unifiedCode = unifiedLines.map(line => line.content).join('\n');
    
    return (
      <SyntaxHighlighter
        language={language || 'text'}
        style={isDarkTheme ? vscDarkPlus : vs}
        showLineNumbers={showLineNumbers}
        wrapLines={true}
        lineProps={(lineNumber) => {
          if (lineNumber <= unifiedLines.length) {
            return { style: getLineStyle(unifiedLines[lineNumber - 1].type) };
          }
          return {};
        }}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          padding: '1rem',
        }}
      >
        {unifiedCode}
      </SyntaxHighlighter>
    );
  };
  
  return (
    <div className={cn('relative rounded-md overflow-hidden my-4 border border-slate-300 dark:border-slate-700', className)}>
      {fileName && (
        <div className="flex items-center px-4 py-2 bg-slate-800 text-white dark:bg-slate-900">
          <Code2 className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium">{fileName}</span>
        </div>
      )}
      
      <Tabs defaultValue={mode} onValueChange={(value) => setMode(value as 'split' | 'unified')}>
        <div className="flex justify-between items-center px-4 py-2 bg-slate-100 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-700">
          <TabsList className="h-8">
            <TabsTrigger value="split" className="text-xs h-6 px-2">Split View</TabsTrigger>
            <TabsTrigger value="unified" className="text-xs h-6 px-2">Unified View</TabsTrigger>
          </TabsList>
          
          {showCopyButton && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 px-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            >
              {copied ? (
                <Tooltip value="Copied!">
                  <Check className="h-4 w-4" />
                </Tooltip>
              ) : (
                <Tooltip value="Copy new code">
                  <Copy className="h-4 w-4" />
                </Tooltip>
              )}
            </Button>
          )}
        </div>
        
        <TabsContent value="split" className="m-0">
          {renderSplitView()}
        </TabsContent>
        
        <TabsContent value="unified" className="m-0">
          {renderUnifiedView()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DiffViewer;
