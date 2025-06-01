import React, { useState, useEffect } from 'react';
import { X, Loader2, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { Agent, CreateAgentParams, UpdateAgentParams } from '@/hooks/useAgents';

interface AgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (params: CreateAgentParams | UpdateAgentParams) => Promise<boolean>;
  agent?: Agent | null;
  mode: 'create' | 'edit';
}

const AgentModal: React.FC<AgentModalProps> = ({ 
  isOpen, 
  onClose, 
  onSave, 
  agent, 
  mode 
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    metadata: {} as Record<string, any>
  });
  const [newTag, setNewTag] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && agent) {
        setFormData({
          name: agent.name,
          description: agent.description,
          tags: [...agent.tags],
          metadata: { ...agent.metadata }
        });
      } else {
        setFormData({
          name: '',
          description: '',
          tags: [],
          metadata: {}
        });
      }
      setErrors({});
    }
  }, [isOpen, mode, agent]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Nome é obrigatório';
    } else if (formData.name.length < 3) {
      newErrors.name = 'Nome deve ter pelo menos 3 caracteres';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Descrição é obrigatória';
    } else if (formData.description.length < 10) {
      newErrors.description = 'Descrição deve ter pelo menos 10 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      const params = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        tags: formData.tags,
        metadata: formData.metadata
      };

      const success = await onSave(params);
      if (success) {
        onClose();
      }
    } catch (error) {
      console.error('Error saving agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = () => {
    const tag = newTag.trim().toLowerCase();
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (newTag.trim()) {
        handleAddTag();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {mode === 'create' ? 'Criar Novo Agente' : 'Editar Agente'}
            </h3>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              disabled={loading}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Name */}
            <div>
              <Label htmlFor="agent-name">Nome do Agente *</Label>
              <Input
                id="agent-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Ex: Assistente de Vendas"
                className={cn(errors.name && "border-red-500")}
                disabled={loading}
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <Label htmlFor="agent-description">Descrição *</Label>
              <Textarea
                id="agent-description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Descreva a função e especialidade do agente..."
                rows={3}
                className={cn(errors.description && "border-red-500")}
                disabled={loading}
              />
              {errors.description && (
                <p className="text-sm text-red-500 mt-1">{errors.description}</p>
              )}
            </div>

            {/* Tags */}
            <div>
              <Label>Tags</Label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Adicionar tag..."
                    disabled={loading}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleAddTag}
                    disabled={!newTag.trim() || loading}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                
                {formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          disabled={loading}
                          className="ml-1 hover:text-blue-600 dark:hover:text-blue-300"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Metadata Preview */}
            {Object.keys(formData.metadata).length > 0 && (
              <div>
                <Label>Metadados</Label>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                  <pre className="text-xs text-gray-600 dark:text-gray-300">
                    {JSON.stringify(formData.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {mode === 'create' ? 'Criando...' : 'Salvando...'}
                </>
              ) : (
                mode === 'create' ? 'Criar Agente' : 'Salvar Alterações'
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentModal;
