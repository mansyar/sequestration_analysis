"""
Core calculation formulas for Carbon Sequestration Calculator

Based on IPCC 2006 Guidelines Volume 4 (AFOLU) Tier 1 methodology
"""

from typing import List
from .models import (
    CalculatorInput, 
    CalculatorResult, 
    FeasibilityResult,
    ScenarioResult,
    ScenarioComparisonResult,
    ScenarioType
)
from .constants import (
    SCENARIOS,
    FOREST_SEQUESTRATION_RATE,
    COASTAL_SEQUESTRATION_RATE,
    ROOT_TO_SHOOT_RATIO
)


def calculate_sequestration(input_params: CalculatorInput) -> CalculatorResult:
    """
    Calculate required sequestration area based on input parameters.
    
    Formula:
    1. total_reduction = emissions_2030 - target_2050
    2. sequestration_target = total_reduction × sequestration_percent
    3. weighted_rate = (forest% × forest_rate) + (coastal% × coastal_rate)
    4. annual_needed = sequestration_target / years
    5. area_needed = annual_needed / weighted_rate
    """
    
    # Apply scenario preset if not custom
    if input_params.scenario != ScenarioType.CUSTOM:
        scenario = SCENARIOS.get(input_params.scenario.value)
        if scenario:
            input_params.forest_percent = scenario.forest_percent * 100
            input_params.include_below_ground = scenario.include_below_ground
    
    # Calculate time period
    years = input_params.target_year - input_params.start_year
    if years <= 0:
        years = 1  # Minimum 1 year
    
    # Step 1: Calculate total reduction needed
    total_reduction = input_params.emissions_2030 - input_params.target_2050
    if total_reduction < 0:
        total_reduction = 0  # No reduction if target higher than baseline
    
    # Step 2: Calculate sequestration contribution
    sequestration_target = total_reduction * (input_params.sequestration_percent / 100)
    
    # Step 3: Calculate effective rates (including below-ground if enabled)
    effective_forest_rate = input_params.forest_rate
    effective_coastal_rate = input_params.coastal_rate
    
    if input_params.include_below_ground:
        effective_forest_rate *= (1 + input_params.root_to_shoot_ratio)
        effective_coastal_rate *= (1 + input_params.root_to_shoot_ratio)
    
    # Step 3b: Apply risk factor discount (fires, pests, drought, etc.)
    risk_discount = 1 - (input_params.risk_factor / 100)
    effective_forest_rate *= risk_discount
    effective_coastal_rate *= risk_discount
    
    # Step 4: Calculate weighted average rate
    forest_fraction = input_params.forest_percent / 100
    coastal_fraction = 1 - forest_fraction
    
    weighted_rate = (forest_fraction * effective_forest_rate) + (coastal_fraction * effective_coastal_rate)
    
    # Step 5: Calculate annual and cumulative sequestration needs
    # Convert MtCO2e to tCO2
    sequestration_target_tonnes = sequestration_target * 1_000_000
    annual_sequestration_needed = sequestration_target_tonnes / years
    
    # Step 6: Calculate total area needed
    if weighted_rate > 0:
        total_area_needed = annual_sequestration_needed / weighted_rate
    else:
        total_area_needed = float('inf')
    
    # Step 7: Calculate area by ecosystem type
    forest_area_needed = total_area_needed * forest_fraction
    coastal_area_needed = total_area_needed * coastal_fraction
    
    # Step 8: Feasibility analysis
    forest_feasibility = _calculate_feasibility(
        area_needed=forest_area_needed,
        area_available=input_params.forest_area_available
    )
    
    coastal_feasibility = _calculate_feasibility(
        area_needed=coastal_area_needed,
        area_available=input_params.coastal_area_available
    )
    
    overall_feasible = forest_feasibility.is_feasible and coastal_feasibility.is_feasible
    
    return CalculatorResult(
        total_reduction_needed=total_reduction,
        sequestration_target=sequestration_target,
        years=years,
        total_area_needed=total_area_needed,
        forest_area_needed=forest_area_needed,
        coastal_area_needed=coastal_area_needed,
        effective_forest_rate=effective_forest_rate,
        effective_coastal_rate=effective_coastal_rate,
        weighted_average_rate=weighted_rate,
        forest_feasibility=forest_feasibility,
        coastal_feasibility=coastal_feasibility,
        overall_feasible=overall_feasible,
        annual_sequestration_needed=annual_sequestration_needed,
        cumulative_sequestration=sequestration_target_tonnes
    )


def _calculate_feasibility(area_needed: float, area_available: float) -> FeasibilityResult:
    """Calculate feasibility for a specific ecosystem type"""
    
    is_feasible = area_needed <= area_available
    
    if area_available > 0:
        utilization_percent = (area_needed / area_available) * 100
    else:
        utilization_percent = float('inf') if area_needed > 0 else 0
    
    deficit_or_surplus = area_available - area_needed
    
    return FeasibilityResult(
        area_needed=area_needed,
        area_available=area_available,
        is_feasible=is_feasible,
        utilization_percent=min(utilization_percent, 999.99),  # Cap for display
        deficit_or_surplus=deficit_or_surplus
    )


def compare_scenarios(base_input: CalculatorInput) -> ScenarioComparisonResult:
    """
    Compare all predefined scenarios and provide recommendations.
    """
    results: List[ScenarioResult] = []
    
    for scenario_key, scenario in SCENARIOS.items():
        # Create input with scenario settings
        scenario_input = base_input.model_copy()
        scenario_input.forest_percent = scenario.forest_percent * 100
        scenario_input.include_below_ground = scenario.include_below_ground
        scenario_input.scenario = ScenarioType.CUSTOM  # Avoid re-applying
        
        result = calculate_sequestration(scenario_input)
        
        results.append(ScenarioResult(
            scenario_name=scenario.name,
            scenario_description=scenario.description,
            result=result
        ))
    
    # Find most feasible scenario
    feasible_scenarios = [r for r in results if r.result.overall_feasible]
    
    if feasible_scenarios:
        # Among feasible, find the one with lowest area utilization
        most_feasible = min(
            feasible_scenarios,
            key=lambda x: max(
                x.result.forest_feasibility.utilization_percent,
                x.result.coastal_feasibility.utilization_percent
            )
        )
        recommendation = f"Recommended: {most_feasible.scenario_name} - achieves target with lowest land utilization"
    else:
        # None feasible - find closest
        closest = min(
            results,
            key=lambda x: x.result.coastal_feasibility.utilization_percent  # Coastal usually limiting factor
        )
        recommendation = f"No scenario fully feasible. {closest.scenario_name} is closest but requires additional measures"
        most_feasible = closest
    
    return ScenarioComparisonResult(
        scenarios=results,
        most_feasible=most_feasible.scenario_name if most_feasible else None,
        recommendation=recommendation
    )


def generate_trajectory(input_params: CalculatorInput, result: "CalculatorResult") -> dict:
    """
    Generate annual trajectory data from start_year to target_year.
    Shows year-by-year sequestration accumulation and area growth.
    """
    from .models import YearlyDataPoint, TrajectoryData, ChartData
    
    years = []
    annual_seq = []
    cumulative_seq = []
    remaining_emissions = []
    forest_trajectory = []
    coastal_trajectory = []
    data_points = []
    
    start_year = input_params.start_year
    target_year = input_params.target_year
    num_years = target_year - start_year
    
    if num_years <= 0:
        num_years = 1
    
    # Annual values
    annual_seq_value = result.annual_sequestration_needed
    annual_forest_area = result.forest_area_needed / num_years if num_years > 0 else result.forest_area_needed
    annual_coastal_area = result.coastal_area_needed / num_years if num_years > 0 else result.coastal_area_needed
    
    # Starting emissions
    current_emissions = input_params.emissions_2030
    annual_reduction = result.total_reduction_needed / num_years if num_years > 0 else result.total_reduction_needed
    
    cumulative = 0
    forest_cumulative = 0
    coastal_cumulative = 0
    
    for i in range(num_years + 1):
        year = start_year + i
        
        if i > 0:
            cumulative += annual_seq_value
            forest_cumulative += annual_forest_area
            coastal_cumulative += annual_coastal_area
            current_emissions -= annual_reduction
        
        years.append(year)
        annual_seq.append(annual_seq_value if i > 0 else 0)
        cumulative_seq.append(cumulative)
        remaining_emissions.append(max(0, current_emissions))
        forest_trajectory.append(forest_cumulative)
        coastal_trajectory.append(coastal_cumulative)
        
        data_points.append(YearlyDataPoint(
            year=year,
            cumulative_sequestration=cumulative,
            annual_sequestration=annual_seq_value if i > 0 else 0,
            remaining_emissions=max(0, current_emissions),
            forest_area_cumulative=forest_cumulative,
            coastal_area_cumulative=coastal_cumulative
        ))
    
    trajectory = TrajectoryData(
        years=years,
        annual_sequestration=annual_seq,
        cumulative_sequestration=cumulative_seq,
        remaining_emissions=remaining_emissions,
        forest_area_trajectory=forest_trajectory,
        coastal_area_trajectory=coastal_trajectory,
        data_points=data_points
    )
    
    # Area comparison data for bar chart
    area_comparison = {
        "labels": ["Forest (Hutan Daratan)", "Coastal (Hutan Perairan)"],
        "current": [input_params.forest_area_available, input_params.coastal_area_available],
        "needed": [result.forest_area_needed, result.coastal_area_needed]
    }
    
    # Scenario comparison for bar chart
    scenario_areas = {}
    for scenario_key, scenario in SCENARIOS.items():
        scenario_input = input_params.model_copy()
        scenario_input.forest_percent = scenario.forest_percent * 100
        scenario_input.include_below_ground = scenario.include_below_ground
        scenario_input.scenario = ScenarioType.CUSTOM
        scenario_result = calculate_sequestration(scenario_input)
        scenario_areas[scenario.name] = {
            "total": scenario_result.total_area_needed,
            "forest": scenario_result.forest_area_needed,
            "coastal": scenario_result.coastal_area_needed,
            "feasible": scenario_result.overall_feasible
        }
    
    return ChartData(
        trajectory=trajectory,
        area_comparison=area_comparison,
        scenario_areas=scenario_areas
    )

