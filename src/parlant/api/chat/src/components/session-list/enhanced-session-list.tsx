import React, { useState, useMemo } from 'react';
import { twMerge } from 'tailwind-merge';
import { 
  Search, 
  Filter, 
  Calendar, 
  MessageCircle, 
  Clock, 
  Star,
  MoreVertical,
  Trash2,
  Edit,
  Archive,
  Pin,
  PinOff
} from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';

interface Session {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
  agentName: string;
  isPinned?: boolean;
  isArchived?: boolean;
  isFavorite?: boolean;
  status: 'active' | 'idle' | 'archived';
}

interface EnhancedSessionListProps {
  sessions: Session[];
  selectedSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete?: (sessionId: string) => void;
  onSessionEdit?: (sessionId: string, newTitle: string) => void;
  onSessionPin?: (sessionId: string, pinned: boolean) => void;
  onSessionArchive?: (sessionId: string, archived: boolean) => void;
  onSessionFavorite?: (sessionId: string, favorite: boolean) => void;
  className?: string;
}

type SortOption = 'recent' | 'oldest' | 'alphabetical' | 'messageCount';
type FilterOption = 'all' | 'active' | 'archived' | 'pinned' | 'favorites';

export default function EnhancedSessionList({
  sessions,
  selectedSessionId,
  onSessionSelect,
  onSessionDelete,
  onSessionEdit,
  onSessionPin,
  onSessionArchive,
  onSessionFavorite,
  className
}: EnhancedSessionListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('recent');
  const [filterBy, setFilterBy] = useState<FilterOption>('all');
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Filter and sort sessions
  const filteredAndSortedSessions = useMemo(() => {
    let filtered = sessions;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(session =>
        session.title.toLowerCase().includes(query) ||
        session.lastMessage.toLowerCase().includes(query) ||
        session.agentName.toLowerCase().includes(query)
      );
    }

    // Apply category filter
    switch (filterBy) {
      case 'active':
        filtered = filtered.filter(s => s.status === 'active');
        break;
      case 'archived':
        filtered = filtered.filter(s => s.isArchived);
        break;
      case 'pinned':
        filtered = filtered.filter(s => s.isPinned);
        break;
      case 'favorites':
        filtered = filtered.filter(s => s.isFavorite);
        break;
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return b.timestamp.getTime() - a.timestamp.getTime();
        case 'oldest':
          return a.timestamp.getTime() - b.timestamp.getTime();
        case 'alphabetical':
          return a.title.localeCompare(b.title);
        case 'messageCount':
          return b.messageCount - a.messageCount;
        default:
          return 0;
      }
    });

    // Pinned sessions always come first
    const pinned = sorted.filter(s => s.isPinned);
    const unpinned = sorted.filter(s => !s.isPinned);
    
    return [...pinned, ...unpinned];
  }, [sessions, searchQuery, sortBy, filterBy]);

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) { // 7 days
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const truncateMessage = (message: string, maxLength: number = 60) => {
    if (message.length <= maxLength) return message;
    return message.substring(0, maxLength) + '...';
  };

  const handleEditStart = (session: Session) => {
    setEditingSessionId(session.id);
    setEditTitle(session.title);
  };

  const handleEditSave = () => {
    if (editingSessionId && editTitle.trim()) {
      onSessionEdit?.(editingSessionId, editTitle.trim());
    }
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleEditCancel = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  return (
    <div className={twMerge('flex flex-col h-full bg-white', className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Conversations</h2>
        
        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Filters and Sort */}
        <div className="flex gap-2">
          <Select value={filterBy} onValueChange={(value: FilterOption) => setFilterBy(value)}>
            <SelectTrigger className="flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="pinned">Pinned</SelectItem>
              <SelectItem value="favorites">Favorites</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
            <SelectTrigger className="flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">Recent</SelectItem>
              <SelectItem value="oldest">Oldest</SelectItem>
              <SelectItem value="alphabetical">A-Z</SelectItem>
              <SelectItem value="messageCount">Most Active</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto">
        {filteredAndSortedSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <MessageCircle className="h-8 w-8 mb-2" />
            <p className="text-sm">No conversations found</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filteredAndSortedSessions.map((session) => (
              <div
                key={session.id}
                className={twMerge(
                  'group relative p-3 rounded-lg cursor-pointer transition-all duration-200',
                  'hover:bg-gray-50 border border-transparent',
                  selectedSessionId === session.id && 'bg-blue-50 border-blue-200',
                  session.isPinned && 'bg-yellow-50 border-yellow-200'
                )}
                onClick={() => onSessionSelect(session.id)}
              >
                {/* Session Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {session.isPinned && (
                      <Pin className="h-3 w-3 text-yellow-600 flex-shrink-0" />
                    )}
                    {session.isFavorite && (
                      <Star className="h-3 w-3 text-yellow-500 flex-shrink-0" />
                    )}
                    
                    {editingSessionId === session.id ? (
                      <Input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleEditSave();
                          if (e.key === 'Escape') handleEditCancel();
                        }}
                        onBlur={handleEditSave}
                        className="h-6 text-sm"
                        autoFocus
                      />
                    ) : (
                      <h3 className="font-medium text-gray-900 truncate text-sm">
                        {session.title}
                      </h3>
                    )}
                  </div>

                  {/* Actions Menu */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-3 w-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEditStart(session)}>
                        <Edit className="h-3 w-3 mr-2" />
                        Rename
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => onSessionPin?.(session.id, !session.isPinned)}
                      >
                        {session.isPinned ? (
                          <>
                            <PinOff className="h-3 w-3 mr-2" />
                            Unpin
                          </>
                        ) : (
                          <>
                            <Pin className="h-3 w-3 mr-2" />
                            Pin
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => onSessionFavorite?.(session.id, !session.isFavorite)}
                      >
                        <Star className="h-3 w-3 mr-2" />
                        {session.isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={() => onSessionArchive?.(session.id, !session.isArchived)}
                      >
                        <Archive className="h-3 w-3 mr-2" />
                        {session.isArchived ? 'Unarchive' : 'Archive'}
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => onSessionDelete?.(session.id)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-3 w-3 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Session Preview */}
                <div className="space-y-1">
                  <p className="text-xs text-gray-600 truncate">
                    {truncateMessage(session.lastMessage)}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center gap-2">
                      <span>{session.agentName}</span>
                      <span>•</span>
                      <span>{session.messageCount} messages</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span>{formatTimestamp(session.timestamp)}</span>
                    </div>
                  </div>
                </div>

                {/* Status Indicator */}
                <div className={twMerge(
                  'absolute top-3 right-3 w-2 h-2 rounded-full',
                  session.status === 'active' && 'bg-green-500',
                  session.status === 'idle' && 'bg-yellow-500',
                  session.status === 'archived' && 'bg-gray-400'
                )} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
