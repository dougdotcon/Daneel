import React, { useState } from 'react';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Eye, 
  MessageSquare,
  Calendar,
  Tag,
  Loader2,
  AlertCircle,
  FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useFetch } from '@/hooks/useFetch';

interface UtteranceField {
  name: string;
  description: string;
  examples: string[];
}

interface Utterance {
  id: string;
  creation_utc: string;
  value: string;
  fields: UtteranceField[];
  tags: string[];
}

const UtterancesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedUtterance, setSelectedUtterance] = useState<string | null>(null);

  // Fetch real data from APIs
  const { data: utterances, loading: utterancesLoading, refetch: refetchUtterances } = useFetch<Utterance[]>('utterances');
  const { data: tags, loading: tagsLoading } = useFetch<{id: string, name: string}[]>('tags');

  const filteredUtterances = utterances?.filter(utterance => {
    const matchesSearch = utterance.value.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         utterance.fields.some(field => 
                           field.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           field.description.toLowerCase().includes(searchTerm.toLowerCase())
                         );
    const matchesTags = selectedTags.length === 0 || selectedTags.some(tag => utterance.tags.includes(tag));
    
    return matchesSearch && matchesTags;
  }) || [];

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta utterance?')) return;
    
    try {
      const response = await fetch(`/utterances/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        refetchUtterances();
      }
    } catch (error) {
      console.error('Error deleting utterance:', error);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Data inválida';
    }
  };

  const highlightFields = (value: string, fields: UtteranceField[]) => {
    let highlighted = value;
    fields.forEach(field => {
      const regex = new RegExp(`{${field.name}}`, 'g');
      highlighted = highlighted.replace(regex, `<span class="bg-blue-100 text-blue-800 px-1 rounded">{${field.name}}</span>`);
    });
    return highlighted;
  };

  if (utterancesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Carregando utterances...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Utterances</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Gerencie templates de mensagens com campos dinâmicos
          </p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Nova Utterance
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar por valor ou campos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
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
            <MessageSquare className="h-5 w-5 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Total</p>
              <p className="text-lg font-semibold text-blue-600">
                {utterances?.length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <FileText className="h-5 w-5 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Com Campos</p>
              <p className="text-lg font-semibold text-green-600">
                {utterances?.filter(u => u.fields.length > 0).length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Tag className="h-5 w-5 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Com Tags</p>
              <p className="text-lg font-semibold text-purple-600">
                {utterances?.filter(u => u.tags.length > 0).length || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Utterances List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Utterances ({filteredUtterances.length})
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredUtterances.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <MessageSquare className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                Nenhuma utterance encontrada
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {searchTerm || selectedTags.length > 0 
                  ? 'Tente ajustar os filtros de busca.'
                  : 'Comece criando sua primeira utterance.'
                }
              </p>
            </div>
          ) : (
            filteredUtterances.map((utterance) => (
              <div key={utterance.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-500">
                        {formatDate(utterance.creation_utc)}
                      </span>
                      {utterance.fields.length > 0 && (
                        <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-800">
                          {utterance.fields.length} campo(s)
                        </span>
                      )}
                    </div>
                    
                    <div className="mb-3">
                      <div 
                        className="text-sm font-medium text-gray-900 dark:text-white"
                        dangerouslySetInnerHTML={{ 
                          __html: highlightFields(utterance.value, utterance.fields) 
                        }}
                      />
                    </div>
                    
                    {utterance.fields.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Campos:</p>
                        <div className="flex flex-wrap gap-2">
                          {utterance.fields.map((field, index) => (
                            <div
                              key={index}
                              className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                              title={field.description}
                            >
                              <span className="font-medium">{field.name}</span>
                              {field.examples.length > 0 && (
                                <span className="text-gray-500 ml-1">
                                  (ex: {field.examples[0]})
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {utterance.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {utterance.tags.map(tagId => {
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
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => setSelectedUtterance(utterance.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleDelete(utterance.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Utterance Details Modal would go here */}
      {selectedUtterance && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Detalhes da Utterance
                </h3>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setSelectedUtterance(null)}
                >
                  ×
                </Button>
              </div>
            </div>
            <div className="px-6 py-4">
              <p className="text-gray-600 dark:text-gray-400">
                Detalhes completos da utterance seriam exibidos aqui...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UtterancesPage;
