import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { apiKeysService } from '@/services/api-keys-api';
import { Eye, EyeOff, Key, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ApiKey {
  key: string;
  label: string;
  description: string;
  url: string;
  placeholder: string;
}

const FINANCIAL_API_KEYS: ApiKey[] = [
  {
    key: 'FINANCIAL_DATASETS_API_KEY',
    label: 'Financial Datasets API',
    description: 'Pro získání finančních dat pro hedge fund',
    url: 'https://financialdatasets.ai/',
    placeholder: 'your-financial-datasets-api-key'
  }
];

const OPENBB_API_KEYS: ApiKey[] = [
  {
    key: 'FMP_API_KEY',
    label: 'Financial Modeling Prep API',
    description: 'Pro finanční výkazy, fundamentální data a company profily',
    url: 'https://financialmodelingprep.com/developer/docs',
    placeholder: 'your-fmp-api-key'
  },
  {
    key: 'ALPHA_VANTAGE_API_KEY',
    label: 'Alpha Vantage API',
    description: 'Pro historická data akcií, forex a komodit',
    url: 'https://www.alphavantage.co/support/#api-key',
    placeholder: 'your-alpha-vantage-api-key'
  },
  {
    key: 'POLYGON_API_KEY',
    label: 'Polygon.io API',
    description: 'Pro real-time a historická tržní data',
    url: 'https://polygon.io/',
    placeholder: 'your-polygon-api-key'
  },
  {
    key: 'TIINGO_API_KEY',
    label: 'Tiingo API',
    description: 'Pro akcie, ETF, forex a krypto data',
    url: 'https://api.tiingo.com/',
    placeholder: 'your-tiingo-api-key'
  },
  {
    key: 'INTRINIO_API_KEY',
    label: 'Intrinio API',
    description: 'Pro finanční data a fundamentální analýzu',
    url: 'https://intrinio.com/',
    placeholder: 'your-intrinio-api-key'
  },
  {
    key: 'BENZINGA_API_KEY',
    label: 'Benzinga API',
    description: 'Pro zprávy, earnings a market sentiment',
    url: 'https://www.benzinga.com/apis/',
    placeholder: 'your-benzinga-api-key'
  },
  {
    key: 'FRED_API_KEY',
    label: 'FRED API (Federal Reserve)',
    description: 'Pro ekonomická data a makroekonomické indikátory',
    url: 'https://fred.stlouisfed.org/docs/api/api_key.html',
    placeholder: 'your-fred-api-key'
  },
  {
    key: 'QUANDL_API_KEY',
    label: 'Quandl API',
    description: 'Pro alternativní finanční a ekonomická data',
    url: 'https://www.quandl.com/tools/api',
    placeholder: 'your-quandl-api-key'
  },
  {
    key: 'EOD_API_KEY',
    label: 'EOD Historical Data API',
    description: 'Pro end-of-day data akcií, ETF a fondů',
    url: 'https://eodhistoricaldata.com/',
    placeholder: 'your-eod-api-key'
  },
  {
    key: 'TRADIER_API_KEY',
    label: 'Tradier API',
    description: 'Pro options data a deriváty',
    url: 'https://developer.tradier.com/',
    placeholder: 'your-tradier-api-key'
  },
  {
    key: 'CBOE_API_KEY',
    label: 'CBOE API',
    description: 'Pro volatilitu a options market data',
    url: 'https://www.cboe.com/market_data/',
    placeholder: 'your-cboe-api-key'
  },
  {
    key: 'NASDAQ_API_KEY',
    label: 'Nasdaq Data Link API',
    description: 'Pro Nasdaq tržní data a indexy',
    url: 'https://data.nasdaq.com/',
    placeholder: 'your-nasdaq-api-key'
  }
];

const MT5_CONFIG_KEYS: ApiKey[] = [
  {
    key: 'MT5_LOGIN',
    label: 'MT5 Login',
    description: 'Číslo účtu MetaTrader 5 pro live trading',
    url: 'https://www.metatrader5.com/',
    placeholder: '12345678'
  },
  {
    key: 'MT5_PASSWORD',
    label: 'MT5 Password',
    description: 'Heslo k MetaTrader 5 účtu',
    url: 'https://www.metatrader5.com/',
    placeholder: 'your-mt5-password'
  },
  {
    key: 'MT5_SERVER',
    label: 'MT5 Server',
    description: 'Server adresa vašeho MT5 brokera',
    url: 'https://www.metatrader5.com/',
    placeholder: 'YourBroker-Demo'
  }
];

const LLM_API_KEYS: ApiKey[] = [
  {
    key: 'ANTHROPIC_API_KEY',
    label: 'Anthropic API',
    description: 'Pro Claude modely (claude-3-5-sonnet, claude-3-opus, claude-3-5-haiku)',
    url: 'https://anthropic.com/',
    placeholder: 'your-anthropic-api-key'
  },
  {
    key: 'DEEPSEEK_API_KEY',
    label: 'DeepSeek API',
    description: 'Pro DeepSeek modely (deepseek-chat, deepseek-reasoner, atd.)',
    url: 'https://deepseek.com/',
    placeholder: 'your-deepseek-api-key'
  },
  {
    key: 'GROQ_API_KEY',
    label: 'Groq API',
    description: 'Pro Groq-hostované modely (deepseek, llama3, atd.)',
    url: 'https://groq.com/',
    placeholder: 'your-groq-api-key'
  },
  {
    key: 'GOOGLE_API_KEY',
    label: 'Google API',
    description: 'Pro Gemini modely (gemini-2.5-flash, gemini-2.5-pro)',
    url: 'https://ai.dev/',
    placeholder: 'your-google-api-key'
  },
  {
    key: 'OPENAI_API_KEY',
    label: 'OpenAI API',
    description: 'Pro OpenAI modely (gpt-4o, gpt-4o-mini, atd.)',
    url: 'https://platform.openai.com/',
    placeholder: 'your-openai-api-key'
  },
  {
    key: 'OPENROUTER_API_KEY',
    label: 'OpenRouter API',
    description: 'Pro OpenRouter modely (gpt-4o, gpt-4o-mini, atd.)',
    url: 'https://openrouter.ai/',
    placeholder: 'your-openrouter-api-key'
  }
];

export function ApiKeysSettings() {
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load API keys from backend on component mount
  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiKeysSummary = await apiKeysService.getAllApiKeys();
      
      // Load actual key values for existing keys
      const keysData: Record<string, string> = {};
      for (const summary of apiKeysSummary) {
        try {
          const fullKey = await apiKeysService.getApiKey(summary.provider);
          keysData[summary.provider] = fullKey.key_value;
        } catch (err) {
          console.warn(`Failed to load key for ${summary.provider}:`, err);
        }
      }
      
      setApiKeys(keysData);
    } catch (err) {
      console.error('Failed to load API keys:', err);
      setError('Nepodařilo se načíst API klíče. Zkuste to znovu.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyChange = async (key: string, value: string) => {
    // Update local state immediately for responsive UI
    setApiKeys(prev => ({
      ...prev,
      [key]: value
    }));

    // Auto-save with debouncing
    try {
      if (value.trim()) {
        await apiKeysService.createOrUpdateApiKey({
          provider: key,
          key_value: value.trim(),
          is_active: true
        });
      } else {
        // If value is empty, delete the key
        try {
          await apiKeysService.deleteApiKey(key);
        } catch (err) {
          // Key might not exist, which is fine
          console.log(`Key ${key} not found for deletion, which is expected`);
        }
      }
    } catch (err) {
      console.error(`Failed to save API key ${key}:`, err);
      setError(`Nepodařilo se uložit ${key}. Zkuste to znovu.`);
    }
  };

  const toggleKeyVisibility = (key: string) => {
    setVisibleKeys(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const clearKey = async (key: string) => {
    try {
      await apiKeysService.deleteApiKey(key);
      setApiKeys(prev => {
        const newKeys = { ...prev };
        delete newKeys[key];
        return newKeys;
      });
    } catch (err) {
      console.error(`Failed to delete API key ${key}:`, err);
      setError(`Nepodařilo se smazat ${key}. Zkuste to znovu.`);
    }
  };

  const renderApiKeySection = (title: string, description: string, keys: ApiKey[], icon: React.ReactNode) => (
    <Card className="bg-panel border-gray-700 dark:border-gray-700">
      <CardHeader>
        <CardTitle className="text-lg font-medium text-primary flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {keys.map((apiKey) => (
          <div key={apiKey.key} className="space-y-2">
                         <button
               className="text-sm font-medium text-primary hover:text-blue-500 cursor-pointer transition-colors text-left"
               onClick={() => window.open(apiKey.url, '_blank')}
             >
               {apiKey.label}
             </button>
            <div className="relative">
              <Input
                type={visibleKeys[apiKey.key] ? 'text' : 'password'}
                placeholder={apiKey.placeholder}
                value={apiKeys[apiKey.key] || ''}
                onChange={(e) => handleKeyChange(apiKey.key, e.target.value)}
                className="pr-20"
              />
              <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                {apiKeys[apiKey.key] && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 hover:bg-red-500/10 hover:text-red-500"
                    onClick={() => clearKey(apiKey.key)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => toggleKeyVisibility(apiKey.key)}
                >
                  {visibleKeys[apiKey.key] ? (
                    <EyeOff className="h-3 w-3" />
                  ) : (
                    <Eye className="h-3 w-3" />
                  )}
                </Button>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-primary mb-2">API Klíče</h2>
          <p className="text-sm text-muted-foreground">
            Načítání API klíčů...
          </p>
        </div>
        <Card className="bg-panel border-gray-700 dark:border-gray-700">
          <CardContent className="p-6">
            <div className="text-sm text-muted-foreground">
              Počkejte prosím, než načteme vaše API klíče...
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-primary mb-2">API Klíče</h2>
        <p className="text-sm text-muted-foreground">
          Nakonfigurujte API endpointy a autentifikační údaje pro finanční data a jazykové modely.
          Změny se automaticky ukládají.
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="bg-red-500/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Key className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="space-y-1">
                <h4 className="text-sm font-medium text-red-500">Chyba</h4>
                <p className="text-xs text-muted-foreground">{error}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setError(null);
                    loadApiKeys();
                  }}
                  className="text-xs mt-2 p-0 h-auto text-red-500 hover:text-red-400"
                >
                  Zkusit znovu
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Financial Data API Keys */}
      {renderApiKeySection(
        'Finanční data',
        'API klíče pro přístup k finančním tržním datům a datovým sadám.',
        FINANCIAL_API_KEYS,
        <Key className="h-4 w-4" />
      )}

      {/* OpenBB API Keys */}
      {renderApiKeySection(
        'OpenBB Platform',
        'API klíče pro OpenBB Platform - poskytují přístup k akcím, komoditám, forex, krypto a ekonomickým datům.',
        OPENBB_API_KEYS,
        <Key className="h-4 w-4" />
      )}

      {/* MT5 Configuration */}
      {renderApiKeySection(
        'MetaTrader 5',
        'Konfigurace pro MetaTrader 5 live trading - připojení k vašemu MT5 účtu pro automatické obchodování.',
        MT5_CONFIG_KEYS,
        <Key className="h-4 w-4" />
      )}

      {/* LLM API Keys */}
      {renderApiKeySection(
        'Jazykové modely',
        'API klíče pro přístup k různým poskytovatelům velkých jazykových modelů.',
        LLM_API_KEYS,
        <Key className="h-4 w-4" />
      )}

      {/* Security Note */}
      <Card className="bg-amber-500/5 border-amber-500/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Key className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
            <div className="space-y-1">
              <h4 className="text-sm font-medium text-amber-500">Bezpečnostní poznámka</h4>
              <p className="text-xs text-muted-foreground">
                API klíče jsou bezpečně uloženy ve vašem lokálním systému a změny se automaticky ukládají. 
                Udržujte své API klíče v bezpečí a nesdílejte je s ostatními.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
