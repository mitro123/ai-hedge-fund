import { Flow } from '@/components/Flow';
import { useFlowContext } from '@/contexts/flow-context';
import { useTabsContext } from '@/contexts/tabs-context';
import { setNodeInternalState, setCurrentFlowId as setNodeStateFlowId } from '@/hooks/use-node-state';
import { cn } from '@/lib/utils';
import { flowService } from '@/services/flow-service';
import { Flow as FlowType } from '@/types/flow';
import { useEffect } from 'react';

// Import správce připojení flow pro kontrolu, zda flow aktivně běží

interface FlowTabContentProps {
  flow: FlowType;
  className?: string;
}

export function FlowTabContent({ flow, className }: FlowTabContentProps) {
  const { loadFlow } = useFlowContext();
  const { activeTabId } = useTabsContext();

  // Vylepšená funkce načítání, která obnoví jak use-node-state, tak data kontextu uzlů
  const loadFlowWithCompleteState = async (flowToLoad: FlowType) => {
    try {
      const flowId = flowToLoad.id.toString();
      
      // Nejprve nastavit ID flow pro izolaci stavu uzlů
      setNodeStateFlowId(flowId);
      
      // NEMAZAT konfigurační stav při přepínání záložek - useNodeState automaticky řeší izolaci flow
      // NERESETOVAT runtime data při přepínání záložek - zachovat všechna runtime data
      // Runtime data by měla být resetována pouze při explicitním spuštění nového běhu tlačítkem Play
      console.log(`[FlowTabContent] Načítám flow ${flowId}, zachovávám všechny stavy (konfigurace + runtime)`);

      // Načíst flow pomocí základní kontextové funkce (řeší stav React Flow)
      await loadFlow(flowToLoad);

      // Poté obnovit vnitřní stavy pro každý uzel (data use-node-state)
      if (flowToLoad.nodes) {
        flowToLoad.nodes.forEach((node: any) => {
          if (node.data?.internal_state) {
            setNodeInternalState(node.id, node.data.internal_state);
          }
        });
      }
      
      // POZNÁMKA: Záměrně zde NEOBNOVUJEME nodeContextData
      // Runtime data spuštění (zprávy, analýzy, stav agentů) by měla začít znovu
      // Pouze konfigurační data (tickery, výběr modelů) jsou obnovena výše
    } catch (error) {
      console.error('Failed to load flow with complete state:', error);
      throw error;
    }
  };

  // Načíst nejnovější stav flow, když se tato záložka stane aktivní
  useEffect(() => {
    const isThisTabActive = activeTabId === `flow-${flow.id}`;
    
    if (isThisTabActive) {
      const fetchAndLoadFlow = async () => {
        try {
          // Načíst nejnovější data flow z backendu
          const latestFlow = await flowService.getFlow(flow.id);
          // Načíst čerstvá data flow s úplnou obnovou stavu
          await loadFlowWithCompleteState(latestFlow);
        } catch (error) {
          console.error('Failed to fetch latest flow state:', error);
          // Záložní načtení cachovaných dat flow s úplnou obnovou stavu
          await loadFlowWithCompleteState(flow);
        }
      };

      fetchAndLoadFlow();
    }
  }, [activeTabId, flow.id, flow, loadFlow]);

  return (
    <div className={cn("h-full w-full", className)}>
      <Flow />
    </div>
  );
}
