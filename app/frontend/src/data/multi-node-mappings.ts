export interface MultiNodeDefinition {
  name: string;
  nodes: {
    componentName: string;
    offsetX: number;
    offsetY: number;
  }[];
  edges: {
    source: string;
    target: string;
  }[];
}

const multiNodeDefinition: Record<string, MultiNodeDefinition> = {
  "Value Investors": {
    name: "Value Investors",
    nodes: [
      { componentName: "Vstup akcií", offsetX: 0, offsetY: 0 },
      { componentName: "Ben Graham", offsetX: 400, offsetY: -400 },
      { componentName: "Charlie Munger", offsetX: 400, offsetY: 0 },
      { componentName: "Warren Buffett", offsetX: 400, offsetY: 400 },
      { componentName: "Správce portfolia", offsetX: 800, offsetY: 0 },
    ],
    edges: [
      { source: "Vstup akcií", target: "Ben Graham" },
      { source: "Vstup akcií", target: "Charlie Munger" },
      { source: "Vstup akcií", target: "Warren Buffett" },
      { source: "Ben Graham", target: "Správce portfolia" },
      { source: "Charlie Munger", target: "Správce portfolia" },
      { source: "Warren Buffett", target: "Správce portfolia" },
    ],
  },
  "Data Wizards": {
    name: "Data Wizards",
    nodes: [
      { componentName: "Vstup akcií", offsetX: 0, offsetY: 0 },
      { componentName: "Technický analytik", offsetX: 400, offsetY: -550 },
      { componentName: "Fundamentální analytik", offsetX: 400, offsetY: -200 },
      { componentName: "Sentimentální analytik", offsetX: 400, offsetY: 150 },
      { componentName: "Oceňovací analytik", offsetX: 400, offsetY: 500 },
      { componentName: "Správce portfolia", offsetX: 800, offsetY: 0 },
    ],
    edges: [
      { source: "Vstup akcií", target: "Technický analytik" },
      { source: "Vstup akcií", target: "Fundamentální analytik" },
      { source: "Vstup akcií", target: "Sentimentální analytik" },
      { source: "Vstup akcií", target: "Oceňovací analytik" },
      { source: "Technický analytik", target: "Správce portfolia" },
      { source: "Fundamentální analytik", target: "Správce portfolia" },
      { source: "Sentimentální analytik", target: "Správce portfolia" },
      { source: "Oceňovací analytik", target: "Správce portfolia" },

    ],
  },
  "Market Mavericks": {
    name: "Market Mavericks",
    nodes: [
      { componentName: "Vstup akcií", offsetX: 0, offsetY: 0 },
      { componentName: "Michael Burry", offsetX: 400, offsetY: -400 },
      { componentName: "Bill Ackman", offsetX: 400, offsetY: 0 },
      { componentName: "Stanley Druckenmiller", offsetX: 400, offsetY: 400 },
      { componentName: "Správce portfolia", offsetX: 800, offsetY: 0 },
    ],
    edges: [
      { source: "Vstup akcií", target: "Michael Burry" },
      { source: "Vstup akcií", target: "Bill Ackman" },
      { source: "Vstup akcií", target: "Stanley Druckenmiller" },
      { source: "Michael Burry", target: "Správce portfolia" },
      { source: "Bill Ackman", target: "Správce portfolia" },
      { source: "Stanley Druckenmiller", target: "Správce portfolia" },
    ],
  },
};

export function getMultiNodeDefinition(name: string): MultiNodeDefinition | null {
  return multiNodeDefinition[name] || null;
}

export function isMultiNodeComponent(componentName: string): boolean {
  return componentName in multiNodeDefinition;
}
