"""
Core calculation formulas for Carbon Sequestration Calculator

Based on IPCC 2006 Guidelines Volume 4 (AFOLU) Tier 1 methodology
"""

import math
from typing import List, Optional
from .models import (
    CalculatorInput, 
    CalculatorResult, 
    FeasibilityResult,
    RiskScenarioData,
    MultiRiskChartData,
    RoadmapPoint,
    RoadmapData,
    ExistingForestSequestrationChartData,
    GrossEmissionChartData,
    CarbonBalanceChartData,
    NewPlantingChartData,
    NetZeroBalanceChartData,
    AllChartData
)
from .constants import (
    FOREST_SEQUESTRATION_RATE,
    COASTAL_SEQUESTRATION_RATE,
    ROOT_TO_SHOOT_RATIO,
    EXISTING_FOREST_STATUS_OPTIONS,
    SEQUESTRATION_DEGRADATION_RATE,
    MATURITY_PHASES,
    DEFAULT_NEW_PLANTING_FOREST_PERCENT,
    INDONESIA_FOREST_AREA,
    INDONESIA_COASTAL_AREA
)


# =============================================================================
# Emission Interpolation Functions
# =============================================================================

def interpolate_emissions(
    initial_year: int, initial_value: float,
    peak_year: int, peak_value: float,
    target_year: int, target_value: float
) -> dict:
    """
    Generate linear emission interpolation for 3-point trajectory.
    
    Returns dict with years as keys and emission values.
    Initial → Peak: linear increase (or stable)
    Peak → Target: linear decrease
    """
    emissions = {}
    
    # Phase 1: Initial to Peak (linear interpolation)
    for year in range(initial_year, peak_year + 1):
        if peak_year > initial_year:
            progress = (year - initial_year) / (peak_year - initial_year)
        else:
            progress = 1.0
        emissions[year] = initial_value + progress * (peak_value - initial_value)
    
    # Phase 2: Peak to Target (linear interpolation)
    for year in range(peak_year + 1, target_year + 1):
        if target_year > peak_year:
            progress = (year - peak_year) / (target_year - peak_year)
        else:
            progress = 1.0
        emissions[year] = peak_value - progress * (peak_value - target_value)
    
    return emissions


# =============================================================================
# Existing Forest Degradation Functions
# =============================================================================

def calculate_existing_forest_degradation(
    base_rate: float,
    years_from_start: int,
    activity_factor: float,
    degradation_rate: float = SEQUESTRATION_DEGRADATION_RATE
) -> float:
    """
    Calculate degrading sequestration rate for existing forests.
    
    Formula: rate_year_n = base_rate × activity_factor × (1 - degradation_rate)^n
    
    Args:
        base_rate: Starting sequestration rate (tCO2/ha/year)
        years_from_start: Number of years since initial year
        activity_factor: 0.0 (mature), 0.5 (mixed), or 1.0 (active)
        degradation_rate: Annual degradation rate (default 2%)
    
    Returns:
        Degraded sequestration rate (tCO2/ha/year)
    """
    decay_factor = (1 - degradation_rate) ** years_from_start
    return base_rate * activity_factor * decay_factor


def calculate_existing_forest_sequestration_series(
    forest_area: float,
    coastal_area: float,
    forest_rate: float,
    coastal_rate: float,
    activity_factor: float,
    years: List[int],
    degradation_rate: float = SEQUESTRATION_DEGRADATION_RATE,
    include_below_ground: bool = False,
    root_to_shoot_ratio: float = 0.37,
    risk_factor: float = 0.0
) -> List[float]:
    """
    Calculate annual sequestration from existing forests with degradation and risk adjustments.
    
    Returns list of annual sequestration values (MtCO2e) for each year.
    """
    # Apply global rate multipliers (BG biomass and risk discount)
    eff_forest_rate = forest_rate
    eff_coastal_rate = coastal_rate
    
    if include_below_ground:
        eff_forest_rate *= (1 + root_to_shoot_ratio)
        eff_coastal_rate *= (1 + root_to_shoot_ratio)
    
    risk_discount = 1 - (risk_factor / 100)
    eff_forest_rate *= risk_discount
    eff_coastal_rate *= risk_discount

    base_year = years[0]
    sequestration_series = []
    
    for year in years:
        years_elapsed = year - base_year
        
        # Apply degradation to effective rates
        forest_rate_degraded = calculate_existing_forest_degradation(
            eff_forest_rate, years_elapsed, activity_factor, degradation_rate
        )
        coastal_rate_degraded = calculate_existing_forest_degradation(
            eff_coastal_rate, years_elapsed, activity_factor, degradation_rate
        )
        
        # Calculate total annual sequestration (convert to MtCO2e)
        annual_sequestration = (
            (forest_area * forest_rate_degraded) + 
            (coastal_area * coastal_rate_degraded)
        ) / 1_000_000
        
        sequestration_series.append(annual_sequestration)
    
    return sequestration_series


# =============================================================================
# New Planting Maturity Functions
# =============================================================================

def calculate_maturity_factor(years_since_planting: int) -> float:
    """
    Returns fraction of full sequestration capacity for a forest cohort.
    
    Biological growth phases (IPCC-based):
    - Years 0-5: 0% (establishment phase - roots developing)
    - Years 5-15: Sigmoid growth to 80% (rapid growth phase)
    - Years 15-40: Linear to 100% (full maturity)
    - Years 40+: Apply 2% annual degradation
    
    Reference: Chapin et al. (2002), Baldocchi (2008), IPCC 2006
    """
    if years_since_planting < 5:
        # Establishment phase - no sequestration
        return 0.0
    elif years_since_planting < 15:
        # Rapid growth phase - sigmoid curve to 80%
        t = years_since_planting - 5
        return 0.8 * (1 / (1 + math.exp(-0.5 * (t - 5))))
    elif years_since_planting < 40:
        # Full maturity phase - linear from 80% to 100%
        t = years_since_planting - 15
        return 0.8 + (0.2 * t / 25)  # Linear from 0.8 to 1.0 over 25 years
    else:
        # Degradation phase - apply 2% annual degradation after year 40
        years_past_maturity = years_since_planting - 40
        return (1 - SEQUESTRATION_DEGRADATION_RATE) ** years_past_maturity


def calculate_sequestration(input_params: CalculatorInput) -> CalculatorResult:
    """
    Calculate required sequestration area based on input parameters.
    
    Updated Formula (3-point emission model):
    1. Generate emission trajectory: initial → peak → target (linear interpolation)
    2. Calculate cumulative gross emissions over the period
    3. sequestration_target = cumulative_emissions × sequestration_percent
    4. weighted_rate = (forest% × forest_rate) + (coastal% × coastal_rate)
    5. Account for existing forest sequestration (with degradation)
    6. area_needed = remaining_sequestration_target / weighted_rate
    """
    
    # Calculate time period
    years = input_params.target_year - input_params.initial_year
    if years <= 0:
        years = 1  # Minimum 1 year
    
    # Step 1: Generate emission trajectory using 3-point model
    emissions_by_year = interpolate_emissions(
        input_params.initial_year, input_params.emissions_initial,
        input_params.peak_year, input_params.emissions_peak,
        input_params.target_year, input_params.target_2050
    )
    
    # Step 2: Calculate CUMULATIVE gross emissions (sum of all yearly emissions)
    cumulative_emissions = sum(emissions_by_year.values())
    
    # Total reduction = cumulative gross emissions (this is what sinks must offset for net-zero)
    total_reduction = cumulative_emissions
    
    # Step 2: Calculate sequestration contribution (60% of cumulative emissions)
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
    
    # Step 4: Calculate weighted average rate for new plantings
    forest_fraction = input_params.new_planting_forest_percent / 100
    coastal_fraction = 1 - forest_fraction
    
    weighted_rate = (forest_fraction * effective_forest_rate) + (coastal_fraction * effective_coastal_rate)
    
    # Step 5: Calculate carbon loss from existing forest degradation and absorption
    # We use a year-by-year summation (Integration) for higher accuracy
    forest_existing_base = input_params.forest_area_available * effective_forest_rate
    coastal_existing_base = input_params.coastal_area_available * effective_coastal_rate
    degradation_rate_decimal = input_params.degradation_rate / 100.0
    
    existing_factor = EXISTING_FOREST_STATUS_OPTIONS.get(
        input_params.existing_forest_status, {}
    ).get("factor", 0.0)

    total_existing_absorption_tonnes = 0
    total_degradation_loss_tonnes = 0
    remaining_capacity = 1.0
    
    for _ in range(years):
        # Combined existing sink potential this year based on remaining capacity
        annual_sink_potential = (forest_existing_base + coastal_existing_base) * remaining_capacity
        
        # 1. Sequestration credit from existing forest
        total_existing_absorption_tonnes += annual_sink_potential * existing_factor
        
        # 2. Capacity loss due to degradation (this is the "carbon debt" created)
        total_degradation_loss_tonnes += annual_sink_potential * degradation_rate_decimal
        
        # Update compound degradation for next year
        remaining_capacity *= (1 - degradation_rate_decimal)
    
    # Step 6: Calculate annual and cumulative sequestration needs
    # Convert MtCO2e target to tonnes
    sequestration_target_tonnes = sequestration_target * 1_000_000
    
    # Adjusted sequestration target = original target - existing absorption credit
    # If existing forest is "Active", it does a lot of work, reducing the need for new planting
    adjusted_sequestration_target = max(0, sequestration_target_tonnes - total_existing_absorption_tonnes)
    
    # New reforestation must:
    # 1. Achieve the adjusted sequestration target
    # 2. Compensate for carbon lost from existing forest degradation
    total_sequestration_needed = adjusted_sequestration_target + total_degradation_loss_tonnes
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

# =============================================================================
# Chart Data Generation Functions
# =============================================================================

def generate_all_chart_data(input_params: CalculatorInput) -> AllChartData:
    """
    Generate data for all 5 new charts.
    
    Charts:
    1. Existing Forest Sequestration Rate vs Year (degrading over time)
    2. Gross Emissions (bars for data points + interpolation line + policy target line)
    3. Carbon Balance (gross emissions vs existing forest sequestration)
    4a/4b. New Planting Area (annual and cumulative with target projection)
    """
    
    # Get activity factor from existing forest status
    activity_factor = EXISTING_FOREST_STATUS_OPTIONS.get(
        input_params.existing_forest_status, {}
    ).get("factor", 0.5)
    
    # Generate year range
    years = list(range(input_params.initial_year, input_params.target_year + 1))
    
    # ----- Chart 1: Existing Forest Sequestration Rate (now MtCO2/yr) -----
    base_rate = (input_params.forest_rate + input_params.coastal_rate) / 2
    # Reuse the series calculation which already returns MtCO2e
    existing_sequestration_mt = calculate_existing_forest_sequestration_series(
        input_params.forest_area_available,
        input_params.coastal_area_available,
        input_params.forest_rate,
        input_params.coastal_rate,
        activity_factor,
        years,
        input_params.degradation_rate / 100.0,
        include_below_ground=input_params.include_below_ground,
        root_to_shoot_ratio=input_params.root_to_shoot_ratio,
        risk_factor=input_params.risk_factor
    )
    
    chart1 = ExistingForestSequestrationChartData(
        years=years,
        total_sequestration_mt=existing_sequestration_mt,
        base_rate=base_rate,
        activity_factor=activity_factor
    )
    
    # ----- Chart 2: Gross Emissions -----
    emissions_by_year = interpolate_emissions(
        input_params.initial_year, input_params.emissions_initial,
        input_params.peak_year, input_params.emissions_peak,
        input_params.target_year, input_params.target_2050
    )
    
    interpolated_emissions = [emissions_by_year.get(y, 0) for y in years]
    policy_target_line = [e * (input_params.sequestration_percent / 100) for e in interpolated_emissions]
    
    # Generate sparse data points for the bar chart (only show at key years)
    data_points_map = {
        input_params.initial_year: input_params.emissions_initial,
        input_params.peak_year: input_params.emissions_peak,
        input_params.target_year: input_params.target_2050
    }
    sparse_data_points = [data_points_map.get(y) for y in years]
    
    chart2 = GrossEmissionChartData(
        years=years,
        sparse_data_points=sparse_data_points,
        data_point_years=[input_params.initial_year, input_params.peak_year, input_params.target_year],
        data_point_values=[input_params.emissions_initial, input_params.emissions_peak, input_params.target_2050],
        interpolated_emissions=interpolated_emissions,
        policy_target_line=policy_target_line
    )
    
    # ----- Chart 3: Carbon Balance -----
    # Make existing sequestration negative (as requested by user)
    negated_existing = [-val for val in existing_sequestration_mt]
    
    # Net balance = gross emissions + (negative sequestration)
    # This reflects the actual atmospheric balance
    net_balance = [
        interpolated_emissions[i] + negated_existing[i]
        for i in range(len(years))
    ]
    
    chart3 = CarbonBalanceChartData(
        years=years,
        gross_emissions=interpolated_emissions,
        existing_forest_sequestration=negated_existing,
        net_balance=net_balance
    )
    
    # ----- Chart 4: New Planting Requirements -----
    chart4 = _generate_new_planting_chart_data(input_params, chart2, chart3)
    
    # ----- Figure 6: Net Zero Balance -----
    # Combined balance = Gross Emissions - Existing Sinks - New Sinks
    # For the chart, we want sinks as negative values
    new_sinks_negated = [-val for val in chart4.annual_new_sequestration_mt]
    
    # Calculate final net balance considering both sinks
    # We extend the existing forest sequestration to cover the projection years
    fig6_existing = calculate_existing_forest_sequestration_series(
        input_params.forest_area_available,
        input_params.coastal_area_available,
        input_params.forest_rate,
        input_params.coastal_rate,
        activity_factor,
        chart4.years,
        input_params.degradation_rate / 100.0,
        include_below_ground=input_params.include_below_ground,
        root_to_shoot_ratio=input_params.root_to_shoot_ratio,
        risk_factor=input_params.risk_factor
    )
    
    fig6_existing_negated = [-val for val in fig6_existing]
    
    fig6_emissions = []
    for y in chart4.years:
        # Interpolated emissions for this year
        em = emissions_by_year.get(y, emissions_by_year.get(input_params.target_year, 0))
        fig6_emissions.append(em)

    final_net_balance = [
        fig6_emissions[i] + fig6_existing_negated[i] + new_sinks_negated[i]
        for i in range(len(chart4.years))
    ]
    
    chart6 = NetZeroBalanceChartData(
        years=chart4.years,
        gross_emissions=fig6_emissions,
        existing_forest_sequestration=fig6_existing_negated,
        new_planting_sequestration=new_sinks_negated,
        net_balance=final_net_balance
    )

    return AllChartData(
        existing_forest_sequestration=chart1,
        gross_emissions=chart2,
        carbon_balance=chart3,
        new_planting=chart4,
        net_zero_balance=chart6
    )
    


def _generate_new_planting_chart_data(
    input_params: CalculatorInput,
    emission_chart: GrossEmissionChartData,
    balance_chart: CarbonBalanceChartData
) -> NewPlantingChartData:
    """
    Generate new planting requirement data aligned with main calculator results.
    Ensures that cumulative area matches the 'Total Area Needed' in the summary.
    """
    # 1. Get authoritative results from main engine for consistency
    main_res = calculate_sequestration(input_params)
    total_area_target = main_res.total_area_needed
    
    years = emission_chart.years.copy()
    new_planting_start = input_params.new_planting_start_year
    target_year = input_params.target_year
    
    # Calculate planting installments
    # We plant from new_planting_start to target_year
    planting_period = [y for y in years if y >= new_planting_start and y <= target_year]
    num_years = len(planting_period)
    annual_installment = total_area_target / num_years if num_years > 0 else 0
    
    # 2. Process existing sequestration (use absolute values for logic)
    # Even if they are negative in the chart, we need them positive for the gap math
    abs_existing_seq = [abs(val) for val in balance_chart.existing_forest_sequestration]
    
    cumulative_target = []
    running_target = 0
    sequestration_policy_pct = input_params.sequestration_percent / 100
    for emission in emission_chart.interpolated_emissions:
        running_target += emission * sequestration_policy_pct
        cumulative_target.append(running_target)
        
    cumulative_existing = []
    running_existing = 0
    for seq in abs_existing_seq:
        running_existing += seq
        cumulative_existing.append(running_existing)
        
    # 3. Generate annual and cumulative area series
    annual_planting = []
    cumulative_planted = []
    total_planted = 0
    
    for year in years:
        if year >= new_planting_start and year <= target_year:
            area_this_year = annual_installment
        else:
            area_this_year = 0
            
        annual_planting.append(area_this_year)
        total_planted += area_this_year
        cumulative_planted.append(total_planted)
        
    annual_new_seq_mt = []
        
    # 4. Target analysis (Mass-based)
    target_emission_reduction = cumulative_target[-1] if cumulative_target else 0
    
    # Cumulative gap for visualization (Total debt remaining)
    # We need to calculate what the new plantings contribute
    weighted_rate = (input_params.new_planting_forest_percent/100 * input_params.forest_rate) + \
                    ((1 - input_params.new_planting_forest_percent/100) * input_params.coastal_rate)
    weighted_rate *= (1 - input_params.risk_factor/100)
    if input_params.include_below_ground:
        weighted_rate *= (1 + input_params.root_to_shoot_ratio)
        
    cumulative_new_seq = []
    running_new = 0
    for i, year in enumerate(years):
        # Simplification: cohort-based sequestration mass
        # Total mass = Area * Rate * years_active_so_far
        annual_new_cont = 0
        for y_idx, y in enumerate(years[:i+1]):
            if y >= new_planting_start:
                years_since = year - y
                if years_since >= 0:
                    maturity = calculate_maturity_factor(years_since)
                    annual_new_cont += annual_planting[y_idx] * weighted_rate * maturity / 1_000_000
        
        running_new += annual_new_cont
        annual_new_seq_mt.append(annual_new_cont)
        cumulative_new_seq.append(running_new)
        
    cumulative_gap = [
        max(0, target_emission_reduction - cumulative_existing[i] - cumulative_new_seq[i])
        for i in range(len(years))
    ]
    
    is_target_achieved = (cumulative_existing[-1] + cumulative_new_seq[-1]) >= target_emission_reduction
    target_reached_year = target_year if is_target_achieved else None
    
    # Projection beyond target if not achieved
    if not is_target_achieved:
        for proj_year in range(target_year + 1, target_year + 51):
            years.append(proj_year)
            
            # Annual contribution from existing cohorts
            annual_new_cont = 0
            for y_idx, y in enumerate(years):
                if y >= new_planting_start and y <= target_year:
                    years_since = proj_year - y
                    if years_since >= 0:
                        maturity = calculate_maturity_factor(years_since)
                        annual_new_cont += annual_planting[y_idx] * weighted_rate * maturity / 1_000_000
                if y > target_year: break
            
            running_new += annual_new_cont
            annual_new_seq_mt.append(annual_new_cont)
            cumulative_new_seq.append(running_new)
            
            # Use current existing capacity (assuming stable or continued slight decay)
            # For simplicity, we just use the last value
            cumulative_gap.append(max(0, target_emission_reduction - cumulative_existing[-1] - running_new))
            annual_planting.append(0)
            cumulative_planted.append(total_planted)
            
            if cumulative_existing[-1] + running_new >= target_emission_reduction:
                target_reached_year = proj_year
                is_target_achieved = True
                break

    return NewPlantingChartData(
        years=years,
        annual_planting_area=annual_planting,
        cumulative_planted_area=cumulative_planted,
        cumulative_sequestration_gap=cumulative_gap,
        target_reached_year=target_reached_year,
        target_emission_reduction=target_emission_reduction,
        is_target_achieved=is_target_achieved,
        annual_new_sequestration_mt=annual_new_seq_mt
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
            
        # 2. Existing Sink (applies existing_forest_status factor)
        # Mature forests (0%): No sink contribution
        # Active forests (100%): Full sink with decay
        existing_factor = EXISTING_FOREST_STATUS_OPTIONS.get(
            input_params.existing_forest_status, {}
        ).get("factor", 0.0)
        
        t_decay = year - 2023
        decay_factor = (1 - (input_params.degradation_rate / 100)) ** t_decay
        existing_sink = -total_sink_2023_mt * decay_factor * existing_factor
        
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
