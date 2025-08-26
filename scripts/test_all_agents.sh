#!/bin/bash

echo "🚀 AI Hedge Fund - Rychlý test agentů"
echo "====================================="

# Kontrola, že jsme ve správném adresáři
if [ ! -d "src/agents" ]; then
    echo "❌ Chyba: Adresář src/agents nenalezen!"
    echo "   Ujistěte se, že spouštíte skript z kořenového adresáře projektu."
    exit 1
fi

# Kontrola Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Chyba: Poetry není nainstalováno!"
    echo "   Nainstalujte Poetry: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "📋 Testování agentů..."
echo ""

# Počítadla
total=0
success=0
failed=0

# Seznam agentů k testování
agents=(
    "aswath_damodaran:aswath_damodaran_agent"
    "ben_graham:ben_graham_agent"
    "bill_ackman:bill_ackman_agent"
    "cathie_wood:cathie_wood_agent"
    "charlie_munger:charlie_munger_agent"
    "fundamentals:fundamentals_analyst_agent"
    "michael_burry:michael_burry_agent"
    "peter_lynch:peter_lynch_agent"
    "phil_fisher:phil_fisher_agent"
    "portfolio_manager:portfolio_management_agent"
    "rakesh_jhunjhunwala:rakesh_jhunjhunwala_agent"
    "risk_manager:risk_management_agent"
    "sentiment:sentiment_analyst_agent"
    "stanley_druckenmiller:stanley_druckenmiller_agent"
    "technicals:technical_analyst_agent"
    "valuation:valuation_analyst_agent"
    "warren_buffett:warren_buffett_agent"
)

# Testování každého agenta
for agent_info in "${agents[@]}"; do
    IFS=':' read -r agent_name function_name <<< "$agent_info"
    total=$((total + 1))
    
    # Pokus o import agenta
    if poetry run python -c "from src.agents.$agent_name import $function_name; print('✅ $agent_name - OK')" 2>/dev/null; then
        success=$((success + 1))
    else
        echo "❌ $agent_name - CHYBA"
        failed=$((failed + 1))
    fi
done

echo ""
echo "📊 VÝSLEDKY:"
echo "============"
echo "Celkem agentů: $total"
echo "Úspěšné: $success"
echo "Neúspěšné: $failed"

if [ $failed -eq 0 ]; then
    echo ""
    echo "🎉 Všechny agenty fungují správně!"
    exit 0
else
    echo ""
    echo "⚠️  $failed agentů nefunguje. Spusťte 'python scripts/fix_agents.py' pro detailní analýzu."
    exit 1
fi
