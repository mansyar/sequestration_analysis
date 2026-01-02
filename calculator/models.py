"""
Pydantic models for Carbon Sequestration Calculator

Input validation and output structuring for the API
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class CalculatorInput(BaseModel):
    """Input parameters for sequestration calculation"""
    
    # Emission Data Points (3-point model)
    emissions_initial: float = Field(
        default=1200,
        ge=0,
        le=5000,
        description="Initial emissions (MtCO2e)"
    )
    emissions_peak: float = Field(
        default=1244,
        ge=0,
        le=5000,
        description="Peak emissions (MtCO2e)"
    )
    target_2050: float = Field(
        default=540,
        ge=0,
        le=5000,
        description="Target emissions by target year (MtCO2e)"
    )
    sequestration_percent: float = Field(
        default=60,
        ge=0,
        le=100,
        description="Percentage of reduction from sequestration (FOLU policy)"
    )
    
    # Year parameters
    initial_year: int = Field(
        default=2023,
        ge=2000,
        le=2100,
        description="Initial emission year"
    )
    peak_year: int = Field(
        default=2030,
        ge=2000,
        le=2100,
        description="Peak emission year"
    )
    target_year: int = Field(
        default=2050,
        ge=2025,
        le=2100,
        description="Target year for emissions goal"
    )
    new_planting_start_year: int = Field(
        default=2023,
        ge=2000,
        le=2100,
        description="Year to start new planting"
    )
    
    # Existing forest area allocation
    forest_area_available: float = Field(
        default=120_343_230,
        ge=0,
        description="Available forest area in hectares"
    )
    coastal_area_available: float = Field(
        default=5_321_321,
        ge=0,
        description="Available coastal/mangrove area in hectares"
    )
    
    # Existing forest carbon status
    existing_forest_status: str = Field(
        default="mixed",
        description="Carbon status of existing forests: 'mature' (0%), 'mixed' (50%), or 'active' (100%)"
    )
    
    # New planting allocation (forest vs coastal)
    new_planting_forest_percent: float = Field(
        default=80,
        ge=0,
        le=100,
        description="Percentage of new planting allocated to forest"
    )
    
    # Sequestration rates (IPCC Tier 1 defaults)
    forest_rate: float = Field(
        default=6.9,
        ge=1,
        le=50,
        description="Forest sequestration rate (tCO2/ha/year)"
    )
    coastal_rate: float = Field(
        default=6.6,
        ge=1,
        le=50,
        description="Coastal sequestration rate (tCO2/ha/year)"
    )
    include_below_ground: bool = Field(
        default=False,
        description="Include below-ground biomass in calculation"
    )
    root_to_shoot_ratio: float = Field(
        default=0.37,
        ge=0.1,
        le=1.0,
        description="Root-to-shoot ratio for below-ground biomass"
    )
    
    # Risk factor for new plantings (disasters/disturbances)
    risk_factor: float = Field(
        default=0,
        ge=0,
        le=50,
        description="Risk buffer % for new plantings (fires, pests, drought)"
    )

    # Annual sequestration degradation for existing forests
    degradation_rate: float = Field(
        default=2.0,
        ge=0.0,
        le=10.0,
        description="Annual loss of existing forest sequestration capacity (%)"
    )


class FeasibilityResult(BaseModel):
    """Feasibility analysis for a specific ecosystem"""
    area_needed: float = Field(description="Area needed in hectares")
    area_available: float = Field(description="Area available in hectares")
    is_feasible: bool = Field(description="Whether the requirement is feasible")
    utilization_percent: float = Field(description="Percentage of available area needed")
    deficit_or_surplus: float = Field(description="Surplus (positive) or deficit (negative) in hectares")


class CalculatorResult(BaseModel):
    """Output from sequestration calculation"""
    
    # Summary
    total_reduction_needed: float = Field(description="Total emission reduction needed (MtCO2e)")
    sequestration_target: float = Field(description="Reduction from sequestration (MtCO2e)")
    years: int = Field(description="Number of years for calculation")
    
    # Area requirements
    total_area_needed: float = Field(description="Total area needed (hectares)")
    forest_area_needed: float = Field(description="Forest area needed (hectares)")
    coastal_area_needed: float = Field(description="Coastal area needed (hectares)")
    
    # Rates used
    effective_forest_rate: float = Field(description="Forest rate used (tCO2/ha/year)")
    effective_coastal_rate: float = Field(description="Coastal rate used (tCO2/ha/year)")
    weighted_average_rate: float = Field(description="Weighted average rate (tCO2/ha/year)")
    
    # Feasibility
    forest_feasibility: FeasibilityResult
    coastal_feasibility: FeasibilityResult
    overall_feasible: bool = Field(description="Whether overall target is achievable")
    
    # Annual metrics
    annual_sequestration_needed: float = Field(description="Annual sequestration needed (tCO2/year)")
    cumulative_sequestration: float = Field(description="Total sequestration over period (tCO2)")


class ScenarioResult(BaseModel):
    """Result for a single scenario"""
    scenario_name: str
    scenario_description: str
    result: CalculatorResult


class ScenarioComparisonResult(BaseModel):
    """Comparison of multiple scenarios"""
    scenarios: List[ScenarioResult]
    most_feasible: Optional[str] = Field(description="Name of most feasible scenario")
    recommendation: str = Field(description="Recommendation based on analysis")


class ReferenceInfo(BaseModel):
    """Academic reference information"""
    id: str
    authors: str
    year: int
    title: str
    journal: str
    key_finding: str
    doi: Optional[str] = None
    url: Optional[str] = None


class YearlyDataPoint(BaseModel):
    """Single year data point for trajectory"""
    year: int
    cumulative_sequestration: float  # tCO2 cumulative
    annual_sequestration: float  # tCO2 per year
    remaining_emissions: float  # MtCO2e remaining to target
    forest_area_cumulative: float  # ha needed by this year
    coastal_area_cumulative: float  # ha needed by this year


class TrajectoryData(BaseModel):
    """Annual trajectory data for charts"""
    years: List[int]
    annual_sequestration: List[float]  # tCO2/year
    cumulative_sequestration: List[float]  # tCO2 total
    remaining_emissions: List[float]  # MtCO2e
    forest_area_trajectory: List[float]  # ha cumulative
    coastal_area_trajectory: List[float]  # ha cumulative
    data_points: List[YearlyDataPoint]


class ChartData(BaseModel):
    """Complete chart data for frontend"""
    trajectory: TrajectoryData
    area_comparison: dict  # For bar chart: current vs needed
    scenario_areas: dict  # For scenario comparison chart


class RiskScenarioData(BaseModel):
    """Data for a single risk scenario for multi-scenario charts"""
    name: str  # "Optimistic", "Moderate", "Pessimistic"
    risk_factor: float  # 0, 20, 40
    color: str  # Chart color
    total_area_needed: float
    forest_area_needed: float
    coastal_area_needed: float
    years: List[int]
    area_trajectory: List[float]  # Cumulative area needed per year
    emissions_trajectory: List[float]  # Remaining emissions per year



class RoadmapPoint(BaseModel):
    """Data point for a single year in the National Net Zero Roadmap"""
    year: int
    emissions: float  # MtCO2e
    existing_sink: float  # MtCO2e (negative value)
    new_sink: float  # MtCO2e (negative value)
    other_mitigation: float  # MtCO2e (negative value - 40% non-sequestration)
    net_balance: float  # MtCO2e


class RoadmapData(BaseModel):
    """Complete roadmap data for 2023-2050"""
    points: List[RoadmapPoint]
    years: List[int]
    emissions: List[float]
    existing_sink: List[float]
    new_sink: List[float]
    other_mitigation: List[float]
    net_balance: List[float]


class MultiRiskChartData(BaseModel):
    """Chart data for multiple risk scenarios"""
    scenarios: List[RiskScenarioData]
    roadmap: RoadmapData
    current_forest: float
    current_coastal: float


# =============================================================================
# New Chart Data Models (for overhauled charts)
# =============================================================================

class ExistingForestSequestrationChartData(BaseModel):
    """Chart 1: Sequestration of existing forest vs year (MtCO2e/yr)"""
    years: List[int]
    total_sequestration_mt: List[float]  # MtCO2e/year
    base_rate: float  # Starting rate (tCO2/ha/yr) before degradation
    activity_factor: float  # 0, 0.5, or 1.0 based on existing_forest_status


class GrossEmissionChartData(BaseModel):
    """Chart 2: Gross emissions with data points, interpolation, and policy line"""
    years: List[int]
    # Sparse data points for bar chart (null for non-data-point years)
    sparse_data_points: List[Optional[float]]
    # Data points (only 3: initial, peak, target)
    data_point_years: List[int]
    data_point_values: List[float]
    # Interpolated line (all years)
    interpolated_emissions: List[float]
    # Policy target line (sequestration contribution)
    policy_target_line: List[float]  # sequestration_percent of emissions


class CarbonBalanceChartData(BaseModel):
    """Chart 3: Carbon balance (gross emissions vs existing forest sequestration)"""
    years: List[int]
    gross_emissions: List[float]  # MtCO2e (positive)
    existing_forest_sequestration: List[float]  # MtCO2e (negative)
    net_balance: List[float]  # gross - existing sequestration


class NetZeroBalanceChartData(BaseModel):
    """Figure 6: Net Carbon Balance including new planting sequestration"""
    years: List[int]
    gross_emissions: List[float]
    existing_forest_sequestration: List[float]
    new_planting_sequestration: List[float]
    net_balance: List[float]


class NewPlantingChartData(BaseModel):
    """Chart 4a & 4b: New planting area requirements"""
    years: List[int]
    annual_planting_area: List[float]  # ha/year
    cumulative_planted_area: List[float]  # ha total
    cumulative_sequestration_gap: List[float]  # What new plantings need to offset
    target_reached_year: Optional[int] = None  # Year when target is reached (may exceed target_year)
    target_emission_reduction: float  # Total emission reduction target for new plantings
    is_target_achieved: bool  # Whether target is achieved within projection
    annual_new_sequestration_mt: List[float]  # Annual absorption from new plantings (MtCO2e/yr)


class AllChartData(BaseModel):
    """Complete chart data for all 5 new charts"""
    existing_forest_sequestration: ExistingForestSequestrationChartData
    gross_emissions: GrossEmissionChartData
    carbon_balance: CarbonBalanceChartData
    new_planting: NewPlantingChartData
    net_zero_balance: NetZeroBalanceChartData
