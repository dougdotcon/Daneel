import React, { useState, useRef, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '../button';
import { Check, Copy, ChevronDown, ChevronUp, Code2 } from 'lucide-react';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';
import { Tooltip } from '../custom/tooltip';

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  showCopyButton?: boolean;
  showCollapseButton?: boolean;
  maxHeight?: number;
  className?: string;
  fileName?: string;
  highlightLines?: number[];
}

const detectLanguage = (code: string): string => {
  // Simple language detection based on file extensions or syntax patterns
  if (code.includes('import React') || code.includes('export default') || code.includes('const [')) {
    return 'jsx';
  } else if (code.includes('func ') && code.includes('package ')) {
    return 'go';
  } else if (code.includes('def ') && code.includes('import ')) {
    return 'python';
  } else if (code.includes('public class') || code.includes('private void')) {
    return 'java';
  } else if (code.includes('#include') || code.includes('int main(')) {
    return 'cpp';
  } else if (code.includes('<?php')) {
    return 'php';
  } else if (code.includes('<!DOCTYPE html>') || code.includes('<html>')) {
    return 'html';
  } else if (code.includes('SELECT ') && code.includes(' FROM ')) {
    return 'sql';
  } else if (code.includes('async ') && code.includes('await ')) {
    return 'typescript';
  } else if (code.includes('function ') || code.includes('const ') || code.includes('let ')) {
    return 'javascript';
  }
  
  return 'text';
};

const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language,
  showLineNumbers = true,
  showCopyButton = true,
  showCollapseButton = true,
  maxHeight = 500,
  className,
  fileName,
  highlightLines = [],
}) => {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [actualHeight, setActualHeight] = useState<number | null>(null);
  const codeRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';
  
  const detectedLanguage = language || detectLanguage(code);
  
  useEffect(() => {
    if (codeRef.current) {
      setActualHeight(codeRef.current.scrollHeight);
    }
  }, [code]);
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const shouldShowCollapseButton = showCollapseButton && actualHeight !== null && actualHeight > maxHeight;
  
  return (
    <div className={cn('relative rounded-md overflow-hidden my-4', className)}>
      {fileName && (
        <div className="flex items-center px-4 py-2 bg-slate-800 text-white dark:bg-slate-900">
          <Code2 className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium">{fileName}</span>
        </div>
      )}
      
      <div className="relative">
        <div
          ref={codeRef}
          style={{
            maxHeight: collapsed ? '100px' : maxHeight,
            overflow: 'hidden',
            transition: 'max-height 0.3s ease-in-out',
          }}
        >
          <SyntaxHighlighter
            language={detectedLanguage}
            style={isDarkTheme ? vscDarkPlus : vs}
            showLineNumbers={showLineNumbers}
            wrapLines={true}
            lineProps={(lineNumber) => {
              const style: React.CSSProperties = { display: 'block' };
              if (highlightLines.includes(lineNumber)) {
                style.backgroundColor = isDarkTheme ? 'rgba(255, 255, 0, 0.2)' : 'rgba(255, 255, 0, 0.3)';
              }
              return { style };
            }}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              padding: '1rem',
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
        
        {shouldShowCollapseButton && collapsed && (
          <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-slate-100 dark:from-slate-800 to-transparent pointer-events-none" />
        )}
      </div>
      
      <div className="flex justify-between items-center px-4 py-2 bg-slate-100 dark:bg-slate-800">
        <div className="text-xs text-slate-500 dark:text-slate-400">
          {detectedLanguage.toUpperCase()}
        </div>
        
        <div className="flex space-x-2">
          {shouldShowCollapseButton && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCollapsed(!collapsed)}
              className="h-8 px-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
            >
              {collapsed ? (
                <Tooltip value="Expand code">
                  <ChevronDown className="h-4 w-4" />
                </Tooltip>
              ) : (
                <Tooltip value="Collapse code">
                  <ChevronUp className="h-4 w-4" />
                </Tooltip>
              )}
            </Button>
          )}
          
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
                <Tooltip value="Copy code">
                  <Copy className="h-4 w-4" />
                </Tooltip>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodeBlock;
