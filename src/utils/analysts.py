"""Constants and utilities related to analysts configuration."""

from src.agents import portfolio_manager
from src.agents.aswath_damodaran import aswath_damodaran_agent
from src.agents.ben_graham import ben_graham_agent
from src.agents.bill_ackman import bill_ackman_agent
from src.agents.cathie_wood import cathie_wood_agent
from src.agents.charlie_munger import charlie_munger_agent
from src.agents.commodities_agent import commodities_analyst_agent
from src.agents.fundamentals import fundamentals_analyst_agent
from src.agents.michael_burry import michael_burry_agent
from src.agents.peter_lynch import peter_lynch_agent
from src.agents.phil_fisher import phil_fisher_agent
from src.agents.rakesh_jhunjhunwala import rakesh_jhunjhunwala_agent
from src.agents.sentiment import sentiment_analyst_agent
from src.agents.stanley_druckenmiller import stanley_druckenmiller_agent
from src.agents.technicals import technical_analyst_agent
from src.agents.valuation import valuation_analyst_agent
from src.agents.warren_buffett import warren_buffett_agent

# Define analyst configuration - single source of truth
ANALYST_CONFIG = {
    "aswath_damodaran": {
        "display_name": "Aswath Damodaran",
        "description": "Děkan oceňování",
        "investing_style": "Zaměřuje se na vnitřní hodnotu a finanční metriky pro posouzení investičních příležitostí prostřednictvím rigorózní analýzy oceňování.",
        "agent_func": aswath_damodaran_agent,
        "type": "analyst",
        "order": 0,
    },
    "ben_graham": {
        "display_name": "Ben Graham",
        "description": "Otec hodnotového investování",
        "investing_style": "Zdůrazňuje bezpečnostní rezervu a investuje do podhodnocených společností se silnými fundamenty prostřednictvím systematické hodnotové analýzy.",
        "agent_func": ben_graham_agent,
        "type": "analyst",
        "order": 1,
    },
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "description": "Aktivistický investor",
        "investing_style": "Snaží se ovlivnit management a odemknout hodnotu prostřednictvím strategického aktivismu a kontrariánských investičních pozic.",
        "agent_func": bill_ackman_agent,
        "type": "analyst",
        "order": 2,
    },
    "cathie_wood": {
        "display_name": "Cathie Wood",
        "description": "Královna růstového investování",
        "investing_style": "Zaměřuje se na disruptivní inovace a růst, investuje do společností, které vedou technologický pokrok a tržní disrupcí.",
        "agent_func": cathie_wood_agent,
        "type": "analyst",
        "order": 3,
    },
    "charlie_munger": {
        "display_name": "Charlie Munger",
        "description": "Racionální myslitel",
        "investing_style": "Obhajuje hodnotové investování se zaměřením na kvalitní podniky a dlouhodobý růst prostřednictvím racionálního rozhodování.",
        "agent_func": charlie_munger_agent,
        "type": "analyst",
        "order": 4,
    },
    "michael_burry": {
        "display_name": "Michael Burry",
        "description": "Kontrariánský investor z Big Short",
        "investing_style": "Dělá kontrariánské sázky, často shortuje přehodnocené trhy a investuje do podhodnocených aktiv prostřednictvím hluboké fundamentální analýzy.",
        "agent_func": michael_burry_agent,
        "type": "analyst",
        "order": 5,
    },
    "peter_lynch": {
        "display_name": "Peter Lynch",
        "description": "Investor desetinásobných zisků",
        "investing_style": "Investuje do společností s pochopitelnými obchodními modely a silným růstovým potenciálem pomocí strategie 'kupuj to, co znáš'.",
        "agent_func": peter_lynch_agent,
        "type": "analyst",
        "order": 6,
    },
    "phil_fisher": {
        "display_name": "Phil Fisher",
        "description": "Investor založený na průzkumu",
        "investing_style": "Zdůrazňuje investování do společností se silným managementem a inovativními produkty, zaměřuje se na dlouhodobý růst prostřednictvím důkladného průzkumu.",
        "agent_func": phil_fisher_agent,
        "type": "analyst",
        "order": 7,
    },
    "rakesh_jhunjhunwala": {
        "display_name": "Rakesh Jhunjhunwala",
        "description": "Velký býk Indie",
        "investing_style": "Využívá makroekonomické poznatky k investování do vysokorostoucích sektorů, zejména na rozvíjejících se trzích a domácích příležitostech.",
        "agent_func": rakesh_jhunjhunwala_agent,
        "type": "analyst",
        "order": 8,
    },
    "stanley_druckenmiller": {
        "display_name": "Stanley Druckenmiller",
        "description": "Makroekonomický investor",
        "investing_style": "Zaměřuje se na makroekonomické trendy, dělá velké sázky na měny, komodity a úrokové sazby prostřednictvím top-down analýzy.",
        "agent_func": stanley_druckenmiller_agent,
        "type": "analyst",
        "order": 9,
    },
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "description": "Věštec z Omahy",
        "investing_style": "Hledá společnosti se silnými fundamenty a konkurenčními výhodami prostřednictvím hodnotového investování a dlouhodobého vlastnictví.",
        "agent_func": warren_buffett_agent,
        "type": "analyst",
        "order": 10,
    },
    "technical_analyst": {
        "display_name": "Technický analytik",
        "description": "Specialista na grafické vzory",
        "investing_style": "Zaměřuje se na grafické vzory a tržní trendy pro investiční rozhodnutí, často používá technické indikátory a analýzu cenové akce.",
        "agent_func": technical_analyst_agent,
        "type": "analyst",
        "order": 11,
    },
    "fundamentals_analyst": {
        "display_name": "Fundamentální analytik",
        "description": "Specialista na finanční výkazy",
        "investing_style": "Zabývá se finančními výkazy a ekonomickými ukazateli pro posouzení vnitřní hodnoty společností prostřednictvím fundamentální analýzy.",
        "agent_func": fundamentals_analyst_agent,
        "type": "analyst",
        "order": 12,
    },
    "sentiment_analyst": {
        "display_name": "Sentimentální analytik",
        "description": "Specialista na tržní nálady",
        "investing_style": "Měří tržní sentiment a chování investorů pro předpověď pohybů trhu a identifikaci příležitostí prostřednictvím behaviorální analýzy.",
        "agent_func": sentiment_analyst_agent,
        "type": "analyst",
        "order": 13,
    },
    "valuation_analyst": {
        "display_name": "Oceňovací analytik",
        "description": "Specialista na oceňování společností",
        "investing_style": "Specializuje se na určování spravedlivé hodnoty společností, používá různé oceňovací modely a finanční metriky pro investiční rozhodnutí.",
        "agent_func": valuation_analyst_agent,
        "type": "analyst",
        "order": 14,
    },
    "commodities_analyst": {
        "display_name": "Komoditní analytik",
        "description": "Specialista na komoditní trhy",
        "investing_style": "Zaměřuje se na analýzu komoditních trhů včetně ropy, zlata, zemědělských produktů a dalších surovin. Analyzuje nabídku a poptávku, sezónní vzory, geopolitické faktory a ekonomické indikátory.",
        "agent_func": commodities_analyst_agent,
        "type": "analyst",
        "order": 15,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [
    (config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}


def get_agents_list():
    """Get the list of agents for API responses."""
    return [
        {
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "investing_style": config["investing_style"],
            "order": config["order"],
        }
        for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
    ]
