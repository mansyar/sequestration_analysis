"""
Pydantic models for Carbon Sequestration Calculator

Input validation and output structuring for the API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ScenarioType(str, Enum):
    """Available scenario presets"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    COASTAL_OPTIMIZED = "coastal_optimized"
    FULL_BIOMASS = "full_biomass"
    CUSTOM = "custom"


class CalculatorInput(BaseModel):
    """Input parameters for sequestration calculation"""
    
    # Emission targets
    emissions_2030: float = Field(
        default=1244,
        ge=0,
        le=5000,
        description="Baseline emissions in 2030 (MtCO2e)"
    )
    target_2050: float = Field(
        default=540,
        ge=0,
        le=5000,
        description="Target emissions by 2050 (MtCO2e)"
    )
    sequestration_percent: float = Field(
        default=60,
        ge=0,
        le=100,
        description="Percentage of reduction from sequestration"
    )
    
    # Area allocation
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
    forest_percent: float = Field(
        default=80,
        ge=0,
        le=100,
        description="Percentage of sequestration from forest"
    )
    
    # Sequestration rates (IPCC Tier 1 defaults)
    forest_rate: float = Field(
        default=11.0,
        ge=1,
        le=50,
        description="Forest sequestration rate (tCO2/ha/year)"
    )
    coastal_rate: float = Field(
        default=13.0,
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
    
    # Time parameters
    start_year: int = Field(
        default=2030,
        ge=2020,
        le=2100,
        description="Start year for calculation"
    )
    target_year: int = Field(
        default=2050,
        ge=2025,
        le=2100,
        description="Target year for emissions goal"
    )
    
    # Risk factor for disasters/disturbances
    risk_factor: float = Field(
        default=0,
        ge=0,
        le=50,
        description="Risk buffer % (fires, pests, drought) - reduces effective sequestration"
    )
    
    # Scenario selection
    scenario: ScenarioType = Field(
        default=ScenarioType.BALANCED,
        description="Predefined scenario to use"
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

