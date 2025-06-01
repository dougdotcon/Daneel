import React, { useState } from 'react';
import { 
  Download, 
  Upload, 
  Archive, 
  Clock, 
  FileText,
  AlertCircle,
  CheckCircle,
  Loader2,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { useToast, toast } from '@/components/ui/toast';

interface BackupFile {
  id: string;
  name: string;
  size: string;
  created: string;
  type: 'full' | 'agents' | 'configuration';
  status: 'completed' | 'in_progress' | 'failed';
}

const BackupPage: React.FC = () => {
  const [backups, setBackups] = useState<BackupFile[]>([
    {
      id: '1',
      name: 'backup-full-2025-01-15.zip',
      size: '2.4 MB',
      created: '2025-01-15T10:30:00Z',
      type: 'full',
      status: 'completed'
    },
    {
      id: '2',
      name: 'backup-agents-2025-01-14.zip',
      size: '1.1 MB',
      created: '2025-01-14T15:45:00Z',
      type: 'agents',
      status: 'completed'
    },
    {
      id: '3',
      name: 'backup-config-2025-01-13.zip',
      size: '0.3 MB',
      created: '2025-01-13T09:15:00Z',
      type: 'configuration',
      status: 'completed'
    }
  ]);
  
  const [isCreatingBackup, setIsCreatingBackup] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [selectedBackupType, setSelectedBackupType] = useState<'full' | 'agents' | 'configuration'>('full');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const { addToast } = useToast();

  const createBackup = async () => {
    setIsCreatingBackup(true);
    
    try {
      // Simular criação de backup
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const newBackup: BackupFile = {
        id: Date.now().toString(),
        name: `backup-${selectedBackupType}-${new Date().toISOString().split('T')[0]}.zip`,
        size: selectedBackupType === 'full' ? '2.8 MB' : selectedBackupType === 'agents' ? '1.3 MB' : '0.4 MB',
        created: new Date().toISOString(),
        type: selectedBackupType,
        status: 'completed'
      };
      
      setBackups(prev => [newBackup, ...prev]);
      addToast(toast.success(`Backup ${selectedBackupType} criado com sucesso!`));
    } catch (error) {
      addToast(toast.error('Erro ao criar backup'));
    } finally {
      setIsCreatingBackup(false);
    }
  };

  const downloadBackup = (backup: BackupFile) => {
    // Simular download
    const link = document.createElement('a');
    link.href = '#';
    link.download = backup.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    addToast(toast.success(`Download de ${backup.name} iniciado`));
  };

  const deleteBackup = (backupId: string) => {
    const backup = backups.find(b => b.id === backupId);
    if (backup && window.confirm(`Tem certeza que deseja excluir o backup "${backup.name}"?`)) {
      setBackups(prev => prev.filter(b => b.id !== backupId));
      addToast(toast.success('Backup excluído com sucesso'));
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.name.endsWith('.zip')) {
        setUploadedFile(file);
        addToast(toast.info(`Arquivo ${file.name} selecionado para restore`));
      } else {
        addToast(toast.error('Por favor, selecione um arquivo .zip'));
      }
    }
  };

  const restoreBackup = async () => {
    if (!uploadedFile) {
      addToast(toast.error('Selecione um arquivo de backup primeiro'));
      return;
    }

    setIsRestoring(true);
    
    try {
      // Simular restore
      await new Promise(resolve => setTimeout(resolve, 4000));
      
      addToast(toast.success(`Restore de ${uploadedFile.name} concluído com sucesso!`));
      setUploadedFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('backup-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (error) {
      addToast(toast.error('Erro ao restaurar backup'));
    } finally {
      setIsRestoring(false);
    }
  };

  const getTypeIcon = (type: BackupFile['type']) => {
    switch (type) {
      case 'full':
        return <Archive className="h-4 w-4 text-blue-500" />;
      case 'agents':
        return <FileText className="h-4 w-4 text-green-500" />;
      case 'configuration':
        return <RefreshCw className="h-4 w-4 text-purple-500" />;
    }
  };

  const getTypeLabel = (type: BackupFile['type']) => {
    switch (type) {
      case 'full':
        return 'Completo';
      case 'agents':
        return 'Agentes';
      case 'configuration':
        return 'Configuração';
    }
  };

  const getStatusIcon = (status: BackupFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Backup e Restore</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Gerencie backups do sistema e restaure dados
        </p>
      </div>

      {/* Create Backup Section */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Criar Novo Backup
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <Label htmlFor="backup-type">Tipo de Backup</Label>
            <select
              id="backup-type"
              value={selectedBackupType}
              onChange={(e) => setSelectedBackupType(e.target.value as any)}
              className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-white"
              disabled={isCreatingBackup}
            >
              <option value="full">Backup Completo</option>
              <option value="agents">Apenas Agentes</option>
              <option value="configuration">Apenas Configuração</option>
            </select>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {selectedBackupType === 'full' && 'Inclui agentes, configurações, sessões e dados'}
              {selectedBackupType === 'agents' && 'Inclui apenas agentes e suas configurações'}
              {selectedBackupType === 'configuration' && 'Inclui apenas configurações do sistema'}
            </p>
          </div>
          
          <div className="flex items-end">
            <Button
              onClick={createBackup}
              disabled={isCreatingBackup}
              className="w-full"
            >
              {isCreatingBackup ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Criando Backup...
                </>
              ) : (
                <>
                  <Archive className="h-4 w-4 mr-2" />
                  Criar Backup
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Restore Section */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Restaurar Backup
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <Label htmlFor="backup-file">Arquivo de Backup</Label>
            <Input
              id="backup-file"
              type="file"
              accept=".zip"
              onChange={handleFileUpload}
              disabled={isRestoring}
              className="mt-1"
            />
            {uploadedFile && (
              <p className="mt-1 text-sm text-green-600 dark:text-green-400">
                Arquivo selecionado: {uploadedFile.name}
              </p>
            )}
          </div>
          
          <div className="flex items-end">
            <Button
              onClick={restoreBackup}
              disabled={isRestoring || !uploadedFile}
              variant="outline"
              className="w-full"
            >
              {isRestoring ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Restaurando...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Restaurar Backup
                </>
              )}
            </Button>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800 dark:text-yellow-200">
              <strong>Atenção:</strong> O restore irá sobrescrever os dados atuais. 
              Certifique-se de fazer um backup antes de restaurar.
            </div>
          </div>
        </div>
      </div>

      {/* Backups List */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Backups Disponíveis
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {backups.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
              Nenhum backup disponível
            </div>
          ) : (
            backups.map((backup) => (
              <div key={backup.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getTypeIcon(backup.type)}
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {backup.name}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                        <span>{getTypeLabel(backup.type)}</span>
                        <span>{backup.size}</span>
                        <span>{formatDate(backup.created)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(backup.status)}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadBackup(backup)}
                      disabled={backup.status !== 'completed'}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deleteBackup(backup.id)}
                      disabled={backup.status === 'in_progress'}
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
    </div>
  );
};

export default BackupPage;
