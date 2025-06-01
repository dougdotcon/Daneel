import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  Eye, 
  ToggleLeft, 
  ToggleRight,
  Tag,
  Link,
  Loader2,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useFetch } from '@/hooks/useFetch';

interface Guideline {
  id: string;
  condition: string;
  action: string;
  enabled: boolean;
  tags: string[];
  metadata?: {
    created_at?: string;
    updated_at?: string;
  };
}

interface GuidelineRelationship {
  id: string;
  source_guideline_id: string;
  target_guideline_id: string;
  kind: string;
}

const GuidelinesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showDisabled, setShowDisabled] = useState(false);

  // Fetch real data from APIs
  const { data: guidelines, loading: guidelinesLoading, refetch: refetchGuidelines } = useFetch<Guideline[]>('guidelines');
  const { data: relationships, loading: relationshipsLoading } = useFetch<GuidelineRelationship[]>('relationships');
  const { data: tags, loading: tagsLoading } = useFetch<{id: string, name: string}[]>('tags');

  const filteredGuidelines = guidelines?.filter(guideline => {
    const matchesSearch = guideline.condition.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         guideline.action.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTags = selectedTags.length === 0 || selectedTags.some(tag => guideline.tags.includes(tag));
    const matchesEnabled = showDisabled || guideline.enabled;
    
    return matchesSearch && matchesTags && matchesEnabled;
  }) || [];

  const handleToggleEnabled = async (id: string, enabled: boolean) => {
    try {
      const response = await fetch(`/guidelines/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !enabled })
      });
      
      if (response.ok) {
        refetchGuidelines();
      }
    } catch (error) {
      console.error('Error toggling guideline:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta guideline?')) return;
    
    try {
      const response = await fetch(`/guidelines/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        refetchGuidelines();
      }
    } catch (error) {
      console.error('Error deleting guideline:', error);
    }
  };

  const getRelationshipsForGuideline = (guidelineId: string) => {
    return relationships?.filter(rel => 
      rel.source_guideline_id === guidelineId || rel.target_guideline_id === guidelineId
    ) || [];
  };

  if (guidelinesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Carregando guidelines...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Guidelines</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Gerencie regras de comportamento dos agentes
          </p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Nova Guideline
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar por condição ou ação..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant={showDisabled ? "default" : "outline"}
              size="sm"
              onClick={() => setShowDisabled(!showDisabled)}
            >
              <Filter className="h-4 w-4 mr-2" />
              {showDisabled ? 'Todas' : 'Apenas Ativas'}
            </Button>
          </div>
        </div>

        {/* Tags Filter */}
        {tags && tags.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Filtrar por tags:</p>
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
                <button
                  key={tag.id}
                  onClick={() => {
                    setSelectedTags(prev => 
                      prev.includes(tag.id) 
                        ? prev.filter(t => t !== tag.id)
                        : [...prev, tag.id]
                    );
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    selectedTags.includes(tag.id)
                      ? 'bg-blue-100 text-blue-800 border border-blue-200'
                      : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                  }`}
                >
                  {tag.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Ativas</p>
              <p className="text-lg font-semibold text-green-600">
                {guidelines?.filter(g => g.enabled).length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-gray-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Inativas</p>
              <p className="text-lg font-semibold text-gray-600">
                {guidelines?.filter(g => !g.enabled).length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Link className="h-5 w-5 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Relacionamentos</p>
              <p className="text-lg font-semibold text-blue-600">
                {relationships?.length || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Guidelines List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Guidelines ({filteredGuidelines.length})
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredGuidelines.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                Nenhuma guideline encontrada
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {searchTerm || selectedTags.length > 0 
                  ? 'Tente ajustar os filtros de busca.'
                  : 'Comece criando sua primeira guideline.'
                }
              </p>
            </div>
          ) : (
            filteredGuidelines.map((guideline) => {
              const guidelineRelationships = getRelationshipsForGuideline(guideline.id);
              
              return (
                <div key={guideline.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <button
                          onClick={() => handleToggleEnabled(guideline.id, guideline.enabled)}
                          className="flex items-center"
                        >
                          {guideline.enabled ? (
                            <ToggleRight className="h-5 w-5 text-green-500" />
                          ) : (
                            <ToggleLeft className="h-5 w-5 text-gray-400" />
                          )}
                        </button>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          guideline.enabled 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {guideline.enabled ? 'Ativa' : 'Inativa'}
                        </span>
                        {guidelineRelationships.length > 0 && (
                          <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                            {guidelineRelationships.length} relacionamento(s)
                          </span>
                        )}
                      </div>
                      
                      <div className="mb-2">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          <span className="text-gray-500">Quando:</span> {guideline.condition}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          <span className="text-gray-500">Então:</span> {guideline.action}
                        </p>
                      </div>
                      
                      {guideline.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {guideline.tags.map(tagId => {
                            const tag = tags?.find(t => t.id === tagId);
                            return (
                              <span
                                key={tagId}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
                              >
                                <Tag className="h-3 w-3 mr-1" />
                                {tag?.name || tagId}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleDelete(guideline.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default GuidelinesPage;
