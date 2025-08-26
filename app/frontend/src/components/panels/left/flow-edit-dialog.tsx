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
import { useTabsContext } from '@/contexts/tabs-context';
import { useToastManager } from '@/hooks/use-toast-manager';
import { flowService } from '@/services/flow-service';
import { Flow } from '@/types/flow';
import { useEffect, useState } from 'react';

interface FlowEditDialogProps {
  flow: Flow | null;
  isOpen: boolean;
  onClose: () => void;
  onFlowUpdated: () => void;
}

export function FlowEditDialog({ flow, isOpen, onClose, onFlowUpdated }: FlowEditDialogProps) {
  const [name, setName] = useState(flow?.name || '');
  const [description, setDescription] = useState(flow?.description || '');
  const [isLoading, setIsLoading] = useState(false);
  const { success, error } = useToastManager();
  const { updateFlowTabTitle } = useTabsContext();

  // Update form when flow changes
  useEffect(() => {
    if (flow) {
      setName(flow.name);
      setDescription(flow.description || '');
    }
  }, [flow]);

  const handleSave = async () => {
    if (!flow || !name.trim()) {
      error('Název toku je povinný');
      return;
    }

    setIsLoading(true);
    try {
      await flowService.updateFlow(flow.id, {
        name: name.trim(),
        description: description.trim() || undefined,
      });
      
      // Update the tab title if it's currently open
      updateFlowTabTitle(flow.id, name.trim());
      
      success(`"${name}" aktualizován!`);
      onFlowUpdated();
      onClose();
    } catch (err) {
      console.error('Failed to update flow:', err);
      error('Nepodařilo se aktualizovat tok');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    if (flow) {
      setName(flow.name);
      setDescription(flow.description || '');
    }
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux)
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (name.trim()) {
        handleSave();
      }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Upravit tok</DialogTitle>
          <DialogDescription>
            Aktualizujte název a popis vašeho toku.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <label htmlFor="name" className="text-sm font-medium">
              Název
            </label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Zadejte název toku"
              className="col-span-3"
            />
          </div>
          
          <div className="grid gap-2">
            <label htmlFor="description" className="text-sm font-medium">
              Popis
            </label>
            <Input
              id="description"
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
            onClick={handleSave} 
            disabled={isLoading || !name.trim()}
          >
            {isLoading ? 'Ukládání...' : 'Uložit změny'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
