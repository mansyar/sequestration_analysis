"""
Core calculation formulas for Carbon Sequestration Calculator

Based on IPCC 2006 Guidelines Volume 4 (AFOLU) Tier 1 methodology
"""

import math
from typing import List
from .models import (
    CalculatorInput, 
    CalculatorResult, 
    FeasibilityResult,
    ScenarioResult,
    ScenarioComparisonResult,
    ScenarioType,
    RiskScenarioData,
    MultiRiskChartData,
    RoadmapPoint,
    RoadmapData
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
    
    # Step 5: Calculate carbon loss from existing forest degradation
    # Existing forests are mature (at equilibrium) but losing capacity at degradation_rate% per year
    # This represents deforestation, forest fires, climate stress, etc.
    # We calculate cumulative loss over the time period
    total_existing_area = input_params.forest_area_available + input_params.coastal_area_available
    degradation_rate_decimal = input_params.degradation_rate / 100
    
    # Calculate cumulative carbon loss from degradation over the years
    # Using compound degradation: each year loses degradation_rate% of remaining capacity
    # Summed over all years
    cumulative_degradation_loss = 0
    remaining_capacity = 1.0  # Start at 100% capacity
    for year in range(years):
        annual_loss = remaining_capacity * degradation_rate_decimal
        cumulative_degradation_loss += annual_loss
        remaining_capacity -= annual_loss
    
    # Convert to carbon tonnes (use weighted rate as baseline for existing forest capacity)
    degradation_loss_tonnes = cumulative_degradation_loss * total_existing_area * weighted_rate
    
    # Step 6: Calculate annual and cumulative sequestration needs
    # Convert MtCO2e to tCO2
    sequestration_target_tonnes = sequestration_target * 1_000_000
    
    # New reforestation must:
    # 1. Achieve the original sequestration target
    # 2. Compensate for carbon lost from existing forest degradation
    total_sequestration_needed = sequestration_target_tonnes + degradation_loss_tonnes
    annual_sequestration_needed = total_sequestration_needed / years
    
    # Step 7: Calculate total area needed
    if weighted_rate > 0:
        total_area_needed = annual_sequestration_needed / weighted_rate
    else:
        total_area_needed = float('inf')
    
    # Step 8: Calculate area by ecosystem type
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


# IPCC-style traffic light colors for risk scenarios
RISK_SCENARIOS = [
    {"name": "Optimistic", "risk_factor": 0, "color": "#43A047"},   # IPCC Green
    {"name": "Moderate", "risk_factor": 20, "color": "#FB8C00"},    # IPCC Orange/Amber
    {"name": "Pessimistic", "risk_factor": 40, "color": "#E53935"}  # IPCC Red
]


def generate_multi_risk_data(
    base_input: CalculatorInput,
    selected_scenarios: List[str] = None
) -> MultiRiskChartData:
    """
    Generate chart data for multiple risk scenarios simultaneously.
    
    Args:
        base_input: Base calculator input (risk_factor will be overridden)
        selected_scenarios: List of scenario names to include ("Optimistic", "Moderate", "Pessimistic")
                          If None, includes all scenarios
    """
    if selected_scenarios is None:
        selected_scenarios = ["Optimistic", "Moderate", "Pessimistic"]
    
    scenarios_data = []
    
    for risk_scenario in RISK_SCENARIOS:
        if risk_scenario["name"] not in selected_scenarios:
            continue
        
        # Create input with this risk factor
        scenario_input = base_input.model_copy()
        scenario_input.risk_factor = risk_scenario["risk_factor"]
        
        # Calculate result for this scenario
        result = calculate_sequestration(scenario_input)
        
        # Generate year-by-year trajectory
        years = list(range(base_input.start_year, base_input.target_year + 1))
        total_years = len(years) - 1
        
        area_trajectory = []
        emissions_trajectory = []
        
        total_reduction = base_input.emissions_2030 - base_input.target_2050
        
        for i, year in enumerate(years):
            # Linear progression for simplicity
            progress = i / max(total_years, 1)
            area_trajectory.append(result.total_area_needed * progress)
            remaining = base_input.emissions_2030 - (total_reduction * progress)
            emissions_trajectory.append(remaining)
        
        scenarios_data.append(RiskScenarioData(
            name=risk_scenario["name"],
            risk_factor=risk_scenario["risk_factor"],
            color=risk_scenario["color"],
            total_area_needed=result.total_area_needed,
            forest_area_needed=result.forest_area_needed,
            coastal_area_needed=result.coastal_area_needed,
            years=years,
            area_trajectory=area_trajectory,
            emissions_trajectory=emissions_trajectory
        ))
    
    # Calculate result for moderate scenario (default 20% risk) for roadmap
    moderate_input = base_input.model_copy()
    moderate_input.risk_factor = 20  # Moderate risk
    moderate_result = calculate_sequestration(moderate_input)
    roadmap_data = calculate_net_zero_roadmap(base_input, moderate_result)

    return MultiRiskChartData(
        scenarios=scenarios_data,
        roadmap=roadmap_data,
        current_forest=base_input.forest_area_available,
        current_coastal=base_input.coastal_area_available
    )


def cohort_maturity_factor(years_since_planting: int) -> float:
    """
    Returns fraction of full sequestration capacity for a forest cohort.
    
    Biological growth phases:
    - Years 0-5: 0% (establishment phase - roots developing)
    - Years 5-15: Sigmoid growth to 80% (rapid growth phase)
    - Years 15+: 80-100% (mature plateau)
    
    Reference: Chapin et al. (2002), Baldocchi (2008)
    """
    if years_since_planting < 5:
        return 0.0
    elif years_since_planting < 15:
        t = years_since_planting - 5
        # Sigmoid growth from 0 to 0.8 over 10 years
        return 0.8 * (1 / (1 + math.exp(-0.5 * (t - 5))))
    else:
        # Gradual increase from 80% to 100% over additional years
        return min(1.0, 0.8 + 0.02 * (years_since_planting - 15))


def calculate_net_zero_roadmap(input_params: CalculatorInput, result_moderate: CalculatorResult) -> RoadmapData:
    """
    Calculate the 2023-2050 National Net Zero Roadmap using cohort-based planting model.
    
    Key improvements:
    1. Emissions: Uses dynamic parameters (emissions_2030, target_2050)
    2. Existing Sink: Exponential decay using degradation_rate
    3. New Sink: Cohort-based planting (2025-2045) with 5-year biological growth lag
    4. Other Mitigation: 40% of reduction from non-sequestration sources
    
    All charts share these dynamic parameters from input_params.
    """
    from .constants import (
        DEFAULT_EMISSIONS_2023,
        INDONESIA_FOREST_AREA,
        INDONESIA_COASTAL_AREA
    )

    # Timeline: 2023 to target_year (default 2050)
    years = list(range(2023, input_params.target_year + 1))
    
    # === Existing Sink Capacity (2023 baseline) ===
    forest_capacity_2023 = INDONESIA_FOREST_AREA * input_params.forest_rate
    coastal_capacity_2023 = INDONESIA_COASTAL_AREA * input_params.coastal_rate
    
    if input_params.include_below_ground:
        forest_capacity_2023 *= (1 + input_params.root_to_shoot_ratio)
        coastal_capacity_2023 *= (1 + input_params.root_to_shoot_ratio)
        
    total_sink_2023_mt = (forest_capacity_2023 + coastal_capacity_2023) / 1_000_000
    
    # === New Sink: Cohort-based planting model ===
    # Total area to plant over 20 years (2025-2045)
    total_area_needed = result_moderate.total_area_needed
    planting_start_year = 2025
    planting_end_year = 2045
    planting_years = planting_end_year - planting_start_year
    annual_planting_area = total_area_needed / planting_years if planting_years > 0 else 0
    
    # Weighted sequestration rate for new areas
    forest_pct = input_params.forest_percent / 100
    coastal_pct = 1 - forest_pct
    weighted_rate = (forest_pct * input_params.forest_rate) + (coastal_pct * input_params.coastal_rate)
    
    if input_params.include_below_ground:
        weighted_rate *= (1 + input_params.root_to_shoot_ratio)
    
    # === Sequestration vs Other Mitigation split ===
    sequestration_pct = input_params.sequestration_percent / 100
    other_mitigation_pct = 1 - sequestration_pct
    total_reduction = input_params.emissions_2030 - input_params.target_2050

    points = []
    
    for year in years:
        # 1. Emissions Pathway (linear interpolation)
        if year <= 2030:
            progress = (year - 2023) / 7
            emissions = DEFAULT_EMISSIONS_2023 + (progress * (input_params.emissions_2030 - DEFAULT_EMISSIONS_2023))
        else:
            progress = (year - 2030) / (input_params.target_year - 2030)
            emissions = input_params.emissions_2030 - (progress * (input_params.emissions_2030 - input_params.target_2050))
            
        # 2. Existing Sink Decay (Exponential)
        t_decay = year - 2023
        decay_factor = (1 - (input_params.degradation_rate / 100)) ** t_decay
        existing_sink = -total_sink_2023_mt * decay_factor
        
        # 3. New Sink (Cohort-based: sum of all planted cohorts' contributions)
        new_sink_capacity = 0.0
        for plant_year in range(planting_start_year, min(year + 1, planting_end_year + 1)):
            if plant_year <= year:
                years_since_planting = year - plant_year
                maturity = cohort_maturity_factor(years_since_planting)
                # This cohort's contribution = area × rate × maturity
                cohort_capacity = annual_planting_area * weighted_rate * maturity
                new_sink_capacity += cohort_capacity
        
        new_sink = -new_sink_capacity / 1_000_000  # Convert to MtCO2e (negative = sink)
        
        # 4. Other Mitigation (40% of reduction, scaled by progress)
        if year <= 2030:
            other_mitigation = 0
        else:
            reduction_progress = (year - 2030) / (input_params.target_year - 2030)
            other_mitigation = -(total_reduction * other_mitigation_pct * reduction_progress)
        
        # Net Balance = Emissions + Sinks + Other Mitigation
        net_balance = emissions + existing_sink + new_sink + other_mitigation
        
        points.append(RoadmapPoint(
            year=year,
            emissions=emissions,
            existing_sink=existing_sink,
            new_sink=new_sink,
            other_mitigation=other_mitigation,
            net_balance=net_balance
        ))

    return RoadmapData(
        points=points,
        years=[p.year for p in points],
        emissions=[p.emissions for p in points],
        existing_sink=[p.existing_sink for p in points],
        new_sink=[p.new_sink for p in points],
        other_mitigation=[p.other_mitigation for p in points],
        net_balance=[p.net_balance for p in points]
    )


def validate_net_zero_pathway(roadmap_data: RoadmapData, sequestration_percent: float = 60) -> tuple:
    """
    Validate that sequestration meets its target share (default 60%).
    
    Returns:
        (is_valid, gap, expected_seq, actual_sinks)
    """
    final_emissions = roadmap_data.emissions[-1]
    initial_emissions = roadmap_data.emissions[0]
    final_existing = abs(roadmap_data.existing_sink[-1])
    final_new = abs(roadmap_data.new_sink[-1])
    final_sinks = final_existing + final_new
    
    # Expected sequestration contribution
    total_reduction = initial_emissions - final_emissions
    expected_seq = total_reduction * (sequestration_percent / 100)
    
    # Gap between expected and actual
    gap = expected_seq - final_sinks
    is_valid = abs(gap) < 50  # Within 50 MtCO2e tolerance
    
    return is_valid, gap, expected_seq, final_sinks
