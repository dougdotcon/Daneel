import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { useTheme } from 'next-themes';
import { ChevronRight, ChevronDown, Code2 } from 'lucide-react';
import CodeBlock from '../code/code-block';

export interface StackFrame {
  functionName: string;
  fileName: string;
  lineNumber: number;
  columnNumber?: number;
  source?: string;
  isLibrary?: boolean;
  variables?: Record<string, any>;
}

interface CallStackProps {
  frames: StackFrame[];
  className?: string;
  title?: string;
  onFrameSelect?: (frame: StackFrame) => void;
}

const CallStack: React.FC<CallStackProps> = ({
  frames,
  className,
  title = 'Call Stack',
  onFrameSelect,
}) => {
  const [selectedFrameIndex, setSelectedFrameIndex] = useState<number | null>(frames.length > 0 ? 0 : null);
  const [expandedFrames, setExpandedFrames] = useState<Record<number, boolean>>({});
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';
  
  const toggleFrameExpanded = (index: number) => {
    setExpandedFrames(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };
  
  const handleFrameClick = (index: number, frame: StackFrame) => {
    setSelectedFrameIndex(index);
    if (onFrameSelect) {
      onFrameSelect(frame);
    }
  };
  
  const getFrameFileName = (frame: StackFrame) => {
    const parts = frame.fileName.split('/');
    return parts[parts.length - 1];
  };
  
  return (
    <div className={cn(
      'border rounded-md overflow-hidden',
      isDarkTheme ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200',
      className
    )}>
      <div className={cn(
        'px-4 py-2 font-medium border-b',
        isDarkTheme ? 'bg-gray-800 border-gray-700' : 'bg-gray-100 border-gray-200'
      )}>
        {title}
      </div>
      
      <div className="overflow-auto max-h-96">
        {frames.length === 0 ? (
          <div className="p-4 text-center text-gray-500">No stack frames available</div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-800">
            {frames.map((frame, index) => (
              <div key={index} className="text-sm">
                <div 
                  className={cn(
                    'flex items-start p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800',
                    selectedFrameIndex === index && 'bg-blue-50 dark:bg-blue-900/20',
                    frame.isLibrary && 'opacity-70'
                  )}
                  onClick={() => handleFrameClick(index, frame)}
                >
                  <div 
                    className="mr-2 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFrameExpanded(index);
                    }}
                  >
                    {frame.source || frame.variables ? (
                      expandedFrames[index] ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )
                    ) : (
                      <span className="w-4 inline-block"></span>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="font-medium">
                      {frame.functionName || '<anonymous>'}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center mt-1">
                      <Code2 className="h-3 w-3 mr-1" />
                      {getFrameFileName(frame)}:{frame.lineNumber}
                      {frame.columnNumber !== undefined && `:${frame.columnNumber}`}
                    </div>
                  </div>
                </div>
                
                {expandedFrames[index] && (
                  <div className="px-3 pb-3">
                    {frame.source && (
                      <div className="mb-3">
                        <div className="text-xs font-medium mb-1 text-gray-500 dark:text-gray-400">
                          Source
                        </div>
                        <CodeBlock 
                          code={frame.source}
                          language={frame.fileName.endsWith('.js') ? 'javascript' : 
                                   frame.fileName.endsWith('.ts') ? 'typescript' :
                                   frame.fileName.endsWith('.py') ? 'python' :
                                   frame.fileName.endsWith('.java') ? 'java' :
                                   frame.fileName.endsWith('.c') || frame.fileName.endsWith('.cpp') ? 'cpp' :
                                   'text'}
                          showLineNumbers={true}
                          highlightLines={[frame.lineNumber]}
                          maxHeight={200}
                          showCollapseButton={true}
                          className="text-xs"
                        />
                      </div>
                    )}
                    
                    {frame.variables && Object.keys(frame.variables).length > 0 && (
                      <div>
                        <div className="text-xs font-medium mb-1 text-gray-500 dark:text-gray-400">
                          Local Variables
                        </div>
                        <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-2 text-xs font-mono">
                          {Object.entries(frame.variables).map(([name, value]) => (
                            <div key={name} className="flex items-start py-1">
                              <div className="font-medium mr-2">{name}:</div>
                              <div className="text-blue-600 dark:text-blue-400">
                                {typeof value === 'string' ? `"${value}"` : 
                                 typeof value === 'object' && value !== null ? 
                                   (Array.isArray(value) ? 
                                     `Array(${value.length})` : 
                                     `Object {${Object.keys(value).join(', ')}}`) :
                                   String(value)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CallStack;
