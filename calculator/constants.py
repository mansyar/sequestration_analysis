"""
IPCC 2006 Tier 1 Default Values for Carbon Sequestration Calculations

Sources:
- IPCC 2006 Guidelines for National Greenhouse Gas Inventories, Volume 4: AFOLU
- 2013 Wetlands Supplement for coastal wetlands
- Peer-reviewed studies on Indonesian forest/mangrove carbon

References:
- Murdiyarso et al. (2015). Nature Climate Change
- Alongi (2014). Estuarine, Coastal and Shelf Science
- Hergoualc'h & Verchot (2011). Biogeosciences
- Indonesia NDC (2022). UNFCCC
"""

from dataclasses import dataclass
from typing import Dict, List

# =============================================================================
# IPCC 2006 Tier 1 Sequestration Rates (tCO2/ha/year)
# =============================================================================

# Strict IPCC 2006 defaults - Above-ground biomass only
# Calculation: Biomass Growth (t dm/ha/yr) × Carbon Fraction (0.47) × CO2/C ratio (44/12)
# Forest: 4.0 × 0.47 × 3.67 = 6.89 tCO2/ha/yr (IPCC 2006 Vol.4 Table 4.9)
# Coastal: 4.8 × 0.47 × 3.67 = 8.28 tCO2/ha/yr (IPCC Wetlands Supplement 2014)
# Adjusted to Alongi (2014) global mangrove average: 179.6 g C/m²/yr = 6.59 tCO2/ha/yr
FOREST_SEQUESTRATION_RATE = 6.9   # Tropical rainforest (IPCC Table 4.9)
COASTAL_SEQUESTRATION_RATE = 6.6  # Mangrove (Alongi 2014; DOI: 10.1146/annurev-marine-010213-135020)

# Root-to-shoot ratio for below-ground biomass (IPCC 2006 Table 4.4)
# Mokany et al. (2006) DOI: 10.1111/j.1365-2486.2005.001043.x
ROOT_TO_SHOOT_RATIO = 0.37  # Tropical moist forests

# With below-ground biomass included (above-ground × (1 + root-to-shoot))
FOREST_RATE_FULL_BIOMASS = FOREST_SEQUESTRATION_RATE * (1 + ROOT_TO_SHOOT_RATIO)  # ~9.45
COASTAL_RATE_FULL_BIOMASS = COASTAL_SEQUESTRATION_RATE * (1 + ROOT_TO_SHOOT_RATIO)  # ~9.04

# =============================================================================
# Indonesia Baseline Data - 3-Point Emission Model
# =============================================================================

# Current land areas (hectares)
INDONESIA_FOREST_AREA = 120_343_230  # Hutan daratan
INDONESIA_COASTAL_AREA = 5_321_321   # Hutan perairan/coastal

# Emission Data Points (MtCO2e) - 3-point trajectory
DEFAULT_EMISSIONS_INITIAL = 1200  # Initial emissions (2023 baseline)
DEFAULT_EMISSIONS_PEAK = 1244     # Peak emissions (2030)
DEFAULT_TARGET_2050 = 540         # Target emissions by 2050

# Year Parameters
DEFAULT_INITIAL_YEAR = 2023
DEFAULT_PEAK_YEAR = 2030
DEFAULT_TARGET_YEAR = 2050
DEFAULT_NEW_PLANTING_START_YEAR = 2023  # Same as initial year

# Policy parameters
DEFAULT_SEQUESTRATION_PERCENT = 60  # 60% from sequestration (FOLU policy)

# Sequestration Rate Degradation (for existing forests)
SEQUESTRATION_DEGRADATION_RATE = 0.02  # 2% annual degradation

# New Planting Allocation (forest vs coastal ratio)
DEFAULT_NEW_PLANTING_FOREST_PERCENT = 80
DEFAULT_NEW_PLANTING_COASTAL_PERCENT = 20

# =============================================================================
# Existing Forest Carbon Status Options
# =============================================================================

# Existing forests may be at carbon equilibrium (mature) or actively absorbing (young/regenerating)
# Reference: Odum (1969), Luyssaert et al. (2008) - Mature forests are near carbon equilibrium
EXISTING_FOREST_STATUS_OPTIONS = {
    "mature": {"factor": 0.0, "label": "Mature (0% - Carbon Equilibrium)"},
    "mixed": {"factor": 0.5, "label": "Mixed (50% - Partial Absorption)"},
    "active": {"factor": 1.0, "label": "Active (100% - Full Absorption)"}
}
DEFAULT_EXISTING_FOREST_STATUS = "mixed"  # Changed from "mature" to "mixed"

# =============================================================================
# Planting Distribution Methods
# =============================================================================
# Different strategies for distributing planting area across years

PLANTING_METHOD_OPTIONS = {
    "equal": {
        "label": "📊 Equal Distribution",
        "description": "Plant the same area every year",
        "icon": "━━━━━"
    },
    "front_loaded": {
        "label": "📈 Front-loaded (Early Emphasis)",
        "description": "Plant more in early years, tapering off later",
        "icon": "╲____"
    },
    "back_loaded": {
        "label": "📉 Back-loaded (Gradual Ramp-up)",
        "description": "Start small, increase planting over time",
        "icon": "____╱"
    },
    "s_curve": {
        "label": "🔄 S-Curve (Logistic Growth)",
        "description": "Slow start, rapid mid-phase, plateau at end",
        "icon": "___/‾"
    },
    "adaptive": {
        "label": "🎯 Adaptive (Degradation Response)",
        "description": "Prioritize based on degradation rates",
        "icon": "~∿~∿"
    }
}

DEFAULT_PLANTING_METHOD = "equal"

# =============================================================================
# New Planting Maturity Curve (IPCC-based)
# =============================================================================
# Reference: Chapin et al. (2002), Baldocchi (2008), IPCC 2006

MATURITY_PHASES = {
    "establishment": {"start": 0, "end": 5, "capacity": 0.0},      # 0% capacity
    "rapid_growth": {"start": 5, "end": 15, "capacity": 0.8},      # Sigmoid to 80%
    "full_maturity": {"start": 15, "end": 40, "capacity": 1.0},    # 100% capacity
    "degradation_start": 40                                         # Apply 2% degradation after 40 years
}


# =============================================================================
# Academic References
# =============================================================================

@dataclass
class Reference:
    """Academic reference with citation details"""
    id: str
    authors: str
    year: int
    title: str
    journal: str
    key_finding: str
    doi: str = ""
    url: str = ""

REFERENCES: List[Reference] = [
    Reference(
        id="murdiyarso2015",
        authors="Murdiyarso, D., Purbopuspito, J., Kauffman, J.B., et al.",
        year=2015,
        title="The potential of Indonesian mangrove forests for global climate change mitigation",
        journal="Nature Climate Change",
        key_finding="Indonesian mangroves store ~1,083 Mg C/ha, 5× higher than terrestrial forests",
        doi="10.1038/nclimate2734",
        url="https://www.nature.com/articles/nclimate2734"
    ),
    Reference(
        id="alongi2014",
        authors="Alongi, D.M.",
        year=2014,
        title="Carbon cycling and storage in mangrove forests",
        journal="Estuarine, Coastal and Shelf Science",
        key_finding="Mangrove conservation more cost-effective than restoration for emission reduction",
        doi="10.1016/j.ecss.2014.01.004",
        url="https://www.sciencedirect.com/science/article/abs/pii/S0272771414000183"
    ),
    Reference(
        id="hergoualch2011",
        authors="Hergoualc'h, K. & Verchot, L.V.",
        year=2011,
        title="Stocks and fluxes of carbon associated with land use change in Southeast Asian tropical peatlands",
        journal="Biogeosciences",
        key_finding="Tropical peat/mangrove emit 3-5× more CO₂ when degraded vs. mineral soils",
        doi="10.5194/bg-8-69-2011",
        url="https://bg.copernicus.org/articles/8/69/2011/"
    ),
    Reference(
        id="ipcc2006",
        authors="IPCC",
        year=2006,
        title="2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4: AFOLU",
        journal="Intergovernmental Panel on Climate Change",
        key_finding="Tier 1 default values for forest biomass growth and carbon fractions",
        url="https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol4.html"
    ),
    Reference(
        id="ipcc2013wetlands",
        authors="IPCC",
        year=2013,
        title="2013 Supplement to the 2006 IPCC Guidelines: Wetlands",
        journal="Intergovernmental Panel on Climate Change",
        key_finding="Specific guidance for coastal wetlands and mangrove ecosystems",
        url="https://www.ipcc-nggip.iges.or.jp/public/wetlands/"
    ),
    Reference(
        id="indonesia_ndc2022",
        authors="Republic of Indonesia",
        year=2022,
        title="Enhanced Nationally Determined Contribution",
        journal="UNFCCC",
        key_finding="LULUCF sector delivers 60-63% of national emission reductions by 2030",
        url="https://unfccc.int/documents/499746"
    ),
    Reference(
        id="folu_netsink2030",
        authors="Ministry of Environment and Forestry, Indonesia",
        year=2021,
        title="Indonesia's FOLU Net Sink 2030",
        journal="National Strategy Document",
        key_finding="Forestry sector targeting net carbon sink by 2030",
        url="https://www.menlhk.go.id/"
    ),
    Reference(
        id="chapin2002",
        authors="Chapin, F.S., Matson, P.A., and Mooney, H.A.",
        year=2002,
        title="Principles of Terrestrial Ecosystem Ecology",
        journal="Springer",
        key_finding="Fundamental principles of ecosystem carbon cycling and sequestration dynamics",
        url="https://link.springer.com/book/10.1007/978-1-4419-9504-9"
    ),
    Reference(
        id="baldocchi2008",
        authors="Baldocchi, D.",
        year=2008,
        title="'Breathing' of the terrestrial biosphere: lessons learned from a global network of carbon dioxide flux measurement systems",
        journal="Australian Journal of Botany",
        key_finding="Global synthesis of CO2 flux measurements across various biomes",
        doi="10.1071/BT08014",
        url="https://www.publish.csiro.au/ajb/BT08014"
    ),
    Reference(
        id="grace2006",
        authors="Grace, J. and Zhang, R.",
        year=2006,
        title="Predicting the effect of climate change on global plant productivity and the carbon cycle",
        journal="Plant Growth and Climate Change (Blackwell Publishing)",
        key_finding="Modeling climate feedback loops on forest sequestration capacity",
        url="https://onlinelibrary.wiley.com/doi/book/10.1002/9780470988695"
    )
]
