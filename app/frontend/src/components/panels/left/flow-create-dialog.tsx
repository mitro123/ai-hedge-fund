import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useToastManager } from '@/hooks/use-toast-manager';
import { flowService } from '@/services/flow-service';
import { Flow } from '@/types/flow';
import { useEffect, useState } from 'react';

interface FlowCreateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onFlowCreated: (flow: Flow) => void;
}

export function FlowCreateDialog({ isOpen, onClose, onFlowCreated }: FlowCreateDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { success, error } = useToastManager();

  // Reset form when dialog opens
  useEffect(() => {
    if (isOpen) {
      setName('');
      setDescription('');
    }
  }, [isOpen]);

  const handleCreate = async () => {
    if (!name.trim()) {
      error('Název toku je povinný');
      return;
    }

    setIsLoading(true);
    try {
      const newFlow = await flowService.createFlow({
        name: name.trim(),
        description: description.trim() || undefined,
        nodes: [],
        edges: [],
        viewport: { x: 0, y: 0, zoom: 1 },
      });
      
      success(`"${newFlow.name}" vytvořen!`);
      onFlowCreated(newFlow);
      onClose();
    } catch (err) {
      console.error('Failed to create flow:', err);
      error('Nepodařilo se vytvořit tok');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setName('');
    setDescription('');
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux)
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (name.trim()) {
        handleCreate();
      }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Vytvořit nový tok</DialogTitle>
          <DialogDescription>
            Vytvořte nový tok s vlastním názvem a popisem.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <label htmlFor="create-name" className="text-sm font-medium">
              Název
            </label>
            <Input
              id="create-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Zadejte název toku"
              className="col-span-3"
              autoFocus
            />
          </div>
          
          <div className="grid gap-2">
            <label htmlFor="create-description" className="text-sm font-medium">
              Popis
            </label>
            <Input
              id="create-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Zadejte popis toku (volitelné)"
              className="col-span-3"
            />
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Zrušit
          </Button>
          <Button 
            onClick={handleCreate} 
            disabled={isLoading || !name.trim()}
          >
            {isLoading ? 'Vytváření...' : 'Vytvořit tok'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
