import React, { useState } from 'react';
import { ChevronRight, ChevronDown, CircleDot, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTheme } from 'next-themes';

interface InspectorProps {
  data: any;
  expandLevel?: number;
  className?: string;
  title?: string;
}

type ValueType = 
  | 'string'
  | 'number'
  | 'boolean'
  | 'null'
  | 'undefined'
  | 'function'
  | 'symbol'
  | 'object'
  | 'array'
  | 'date'
  | 'regexp'
  | 'error'
  | 'map'
  | 'set'
  | 'bigint';

const getValueType = (value: any): ValueType => {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  if (Array.isArray(value)) return 'array';
  if (value instanceof Date) return 'date';
  if (value instanceof RegExp) return 'regexp';
  if (value instanceof Error) return 'error';
  if (value instanceof Map) return 'map';
  if (value instanceof Set) return 'set';
  if (typeof value === 'bigint') return 'bigint';
  
  return typeof value as ValueType;
};

const getValueColor = (type: ValueType, isDarkTheme: boolean): string => {
  switch (type) {
    case 'string':
      return isDarkTheme ? 'text-green-400' : 'text-green-600';
    case 'number':
    case 'bigint':
      return isDarkTheme ? 'text-blue-400' : 'text-blue-600';
    case 'boolean':
      return isDarkTheme ? 'text-purple-400' : 'text-purple-600';
    case 'null':
    case 'undefined':
      return isDarkTheme ? 'text-gray-400' : 'text-gray-600';
    case 'function':
      return isDarkTheme ? 'text-yellow-400' : 'text-yellow-600';
    case 'symbol':
      return isDarkTheme ? 'text-pink-400' : 'text-pink-600';
    case 'date':
    case 'regexp':
      return isDarkTheme ? 'text-red-400' : 'text-red-600';
    case 'error':
      return isDarkTheme ? 'text-red-500' : 'text-red-700';
    default:
      return '';
  }
};

const formatValue = (value: any, type: ValueType): string => {
  switch (type) {
    case 'string':
      return `"${value}"`;
    case 'function':
      return `ƒ ${value.name || 'anonymous'}()`;
    case 'date':
      return value.toISOString();
    case 'regexp':
      return value.toString();
    case 'error':
      return `${value.name}: ${value.message}`;
    case 'map':
      return `Map(${value.size})`;
    case 'set':
      return `Set(${value.size})`;
    case 'array':
      return `Array(${value.length})`;
    case 'object':
      return `Object`;
    case 'bigint':
      return `${value.toString()}n`;
    default:
      return String(value);
  }
};

const ObjectInspector: React.FC<{ 
  data: any; 
  name?: string; 
  depth: number; 
  expandLevel: number;
  path: string;
}> = ({ 
  data, 
  name, 
  depth, 
  expandLevel,
  path,
}) => {
  const [isExpanded, setIsExpanded] = useState(depth < expandLevel);
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';
  
  const type = getValueType(data);
  const isPrimitive = ['string', 'number', 'boolean', 'null', 'undefined', 'symbol', 'bigint'].includes(type);
  const isExpandable = !isPrimitive && (
    type === 'object' || 
    type === 'array' || 
    type === 'map' || 
    type === 'set' || 
    type === 'function'
  );
  
  const toggleExpand = () => {
    if (isExpandable) {
      setIsExpanded(!isExpanded);
    }
  };
  
  const renderObjectProperties = () => {
    if (!isExpanded) return null;
    
    const properties = [];
    
    if (type === 'array') {
      for (let i = 0; i < data.length; i++) {
        properties.push(
          <ObjectInspector
            key={`${path}.${i}`}
            data={data[i]}
            name={String(i)}
            depth={depth + 1}
            expandLevel={expandLevel}
            path={`${path}.${i}`}
          />
        );
      }
    } else if (type === 'map') {
      let index = 0;
      data.forEach((value: any, key: any) => {
        properties.push(
          <ObjectInspector
            key={`${path}.${index}`}
            data={value}
            name={formatValue(key, getValueType(key))}
            depth={depth + 1}
            expandLevel={expandLevel}
            path={`${path}.${index}`}
          />
        );
        index++;
      });
    } else if (type === 'set') {
      let index = 0;
      data.forEach((value: any) => {
        properties.push(
          <ObjectInspector
            key={`${path}.${index}`}
            data={value}
            name={String(index)}
            depth={depth + 1}
            expandLevel={expandLevel}
            path={`${path}.${index}`}
          />
        );
        index++;
      });
    } else if (type === 'object' || type === 'function') {
      const keys = Object.getOwnPropertyNames(data);
      
      for (const key of keys) {
        try {
          const value = data[key];
          properties.push(
            <ObjectInspector
              key={`${path}.${key}`}
              data={value}
              name={key}
              depth={depth + 1}
              expandLevel={expandLevel}
              path={`${path}.${key}`}
            />
          );
        } catch (error) {
          properties.push(
            <div key={`${path}.${key}`} className="pl-6 py-1">
              <span className="text-red-500">{key}: [Error accessing property]</span>
            </div>
          );
        }
      }
    }
    
    return properties.length > 0 ? (
      <div className="pl-4">{properties}</div>
    ) : (
      <div className="pl-4 py-1 text-gray-500 italic">No properties</div>
    );
  };
  
  const valueColor = getValueColor(type, isDarkTheme);
  
  return (
    <div className="font-mono text-sm">
      <div 
        className={cn("flex items-start py-1", isExpandable ? "cursor-pointer" : "")}
        onClick={toggleExpand}
      >
        <div className="mr-1 w-4 flex-shrink-0">
          {isExpandable ? (
            isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
          ) : (
            <span className="w-4"></span>
          )}
        </div>
        
        {name !== undefined && (
          <div className="mr-1 font-medium">{name}: </div>
        )}
        
        <div className={cn(valueColor)}>
          {isExpandable ? (
            <span>{formatValue(data, type)}</span>
          ) : (
            <span>{formatValue(data, type)}</span>
          )}
        </div>
      </div>
      
      {isExpandable && renderObjectProperties()}
    </div>
  );
};

const Inspector: React.FC<InspectorProps> = ({
  data,
  expandLevel = 1,
  className,
  title,
}) => {
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';
  
  return (
    <div className={cn(
      'border rounded-md overflow-hidden',
      isDarkTheme ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200',
      className
    )}>
      {title && (
        <div className={cn(
          'px-4 py-2 font-medium border-b',
          isDarkTheme ? 'bg-gray-800 border-gray-700' : 'bg-gray-100 border-gray-200'
        )}>
          {title}
        </div>
      )}
      <div className="p-4 overflow-auto">
        <ObjectInspector 
          data={data} 
          depth={0} 
          expandLevel={expandLevel}
          path="root"
        />
      </div>
    </div>
  );
};

export default Inspector;
