import React, { useState } from 'react';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Tag,
  Calendar,
  Loader2,
  AlertCircle,
  Hash
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useFetch } from '@/hooks/useFetch';

interface TagData {
  id: string;
  name: string;
  creation_utc: string;
}

interface CreateTagData {
  name: string;
}

const TagsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [creating, setCreating] = useState(false);

  // Fetch real data from APIs
  const { data: tags, loading: tagsLoading, refetch: refetchTags } = useFetch<TagData[]>('tags');

  const filteredTags = tags?.filter(tag => 
    tag.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const handleCreate = async () => {
    if (!newTagName.trim()) return;
    
    setCreating(true);
    try {
      const response = await fetch('/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newTagName.trim() } as CreateTagData)
      });
      
      if (response.ok) {
        setNewTagName('');
        setIsCreating(false);
        refetchTags();
      } else {
        const error = await response.json();
        alert(`Erro ao criar tag: ${error.detail || 'Erro desconhecido'}`);
      }
    } catch (error) {
      console.error('Error creating tag:', error);
      alert('Erro ao criar tag');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Tem certeza que deseja excluir a tag "${name}"?`)) return;
    
    try {
      const response = await fetch(`/tags/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        refetchTags();
      } else {
        const error = await response.json();
        alert(`Erro ao excluir tag: ${error.detail || 'Erro desconhecido'}`);
      }
    } catch (error) {
      console.error('Error deleting tag:', error);
      alert('Erro ao excluir tag');
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

  if (tagsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-600">Carregando tags...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Tags</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Gerencie tags para organizar agentes, guidelines e outros recursos
          </p>
        </div>
        <Button 
          className="flex items-center gap-2"
          onClick={() => setIsCreating(true)}
        >
          <Plus className="h-4 w-4" />
          Nova Tag
        </Button>
      </div>

      {/* Create Tag Form */}
      {isCreating && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Criar Nova Tag
          </h3>
          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="Nome da tag (ex: customer-service, sales, etc.)"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreate();
                  if (e.key === 'Escape') {
                    setIsCreating(false);
                    setNewTagName('');
                  }
                }}
                autoFocus
              />
            </div>
            <Button 
              onClick={handleCreate}
              disabled={!newTagName.trim() || creating}
            >
              {creating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Criar'
              )}
            </Button>
            <Button 
              variant="outline"
              onClick={() => {
                setIsCreating(false);
                setNewTagName('');
              }}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Buscar tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Tag className="h-5 w-5 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Total de Tags</p>
              <p className="text-lg font-semibold text-blue-600">
                {tags?.length || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center">
            <Hash className="h-5 w-5 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Filtradas</p>
              <p className="text-lg font-semibold text-green-600">
                {filteredTags.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tags List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Tags ({filteredTags.length})
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {filteredTags.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <Tag className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                Nenhuma tag encontrada
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {searchTerm 
                  ? 'Tente ajustar o termo de busca.'
                  : 'Comece criando sua primeira tag.'
                }
              </p>
              {!searchTerm && (
                <Button 
                  className="mt-4"
                  onClick={() => setIsCreating(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Criar Primeira Tag
                </Button>
              )}
            </div>
          ) : (
            filteredTags.map((tag) => (
              <div key={tag.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Tag className="h-4 w-4 text-blue-600" />
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                        {tag.name}
                      </h4>
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Calendar className="h-3 w-3" />
                        Criada em {formatDate(tag.creation_utc)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleDelete(tag.id, tag.name)}
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

      {/* Usage Information */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Sobre Tags
            </h4>
            <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
              Tags são usadas para organizar e categorizar agentes, guidelines, variáveis de contexto, 
              utterances e outros recursos do sistema. Elas facilitam a busca e o gerenciamento de recursos relacionados.
            </p>
            <ul className="text-sm text-blue-700 dark:text-blue-200 mt-2 list-disc list-inside">
              <li>Use nomes descritivos e consistentes</li>
              <li>Evite espaços - use hífens ou underscores</li>
              <li>Considere criar uma hierarquia (ex: customer-service, customer-support)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TagsPage;
