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
# Indonesia Baseline Data
# =============================================================================

# Current land areas (hectares)
INDONESIA_FOREST_AREA = 120_343_230  # Hutan daratan
INDONESIA_COASTAL_AREA = 5_321_321   # Hutan perairan/coastal

# Emission targets (MtCO2e)
DEFAULT_EMISSIONS_2023 = 1200  # Baseline 2023 emissions
DEFAULT_EMISSIONS_2030 = 1244  # Baseline emissions peak
DEFAULT_TARGET_2050 = 540      # Target emissions by 2050

# Policy parameters
DEFAULT_SEQUESTRATION_PERCENT = 60  # 60% from sequestration

# Time parameters
DEFAULT_START_YEAR = 2030
DEFAULT_TARGET_YEAR = 2050

# =============================================================================
# Scenario Presets
# =============================================================================

@dataclass
class ScenarioPreset:
    """Predefined scenario configuration"""
    name: str
    forest_percent: float
    coastal_percent: float
    include_below_ground: bool
    description: str

SCENARIOS: Dict[str, ScenarioPreset] = {
    "conservative": ScenarioPreset(
        name="Conservative",
        forest_percent=0.90,
        coastal_percent=0.10,
        include_below_ground=False,
        description="Reflects current area ratio (~95:5)"
    ),
    "balanced": ScenarioPreset(
        name="Balanced",
        forest_percent=0.80,
        coastal_percent=0.20,
        include_below_ground=False,
        description="Higher coastal efficiency"
    ),
    "coastal_optimized": ScenarioPreset(
        name="Coastal-Optimized",
        forest_percent=0.70,
        coastal_percent=0.30,
        include_below_ground=False,
        description="Maximum mangrove potential"
    ),
    "full_biomass": ScenarioPreset(
        name="Full Biomass",
        forest_percent=0.80,
        coastal_percent=0.20,
        include_below_ground=True,
        description="+37% sequestration (R:S ratio)"
    )
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
