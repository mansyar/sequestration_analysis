"""
Carbon Sequestration Calculator - FastAPI Application

A web application to calculate the required forest and coastal area
to achieve Indonesia's 2050 carbon emission targets.

Based on IPCC 2006 Guidelines Volume 4 (AFOLU) Tier 1 methodology.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated

from calculator.models import CalculatorInput, ScenarioType
from calculator.formulas import calculate_sequestration, compare_scenarios, generate_trajectory
from calculator.constants import (
    SCENARIOS,
    REFERENCES,
    DEFAULT_EMISSIONS_2030,
    DEFAULT_TARGET_2050,
    DEFAULT_SEQUESTRATION_PERCENT,
    INDONESIA_FOREST_AREA,
    INDONESIA_COASTAL_AREA,
    FOREST_SEQUESTRATION_RATE,
    COASTAL_SEQUESTRATION_RATE,
    ROOT_TO_SHOOT_RATIO,
    DEFAULT_START_YEAR,
    DEFAULT_TARGET_YEAR
)

# Initialize FastAPI app
app = FastAPI(
    title="Indonesia Carbon Sequestration Calculator",
    description="Calculate required forest and coastal area for 2050 targets",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main calculator page"""
    
    # Default values for the form
    defaults = {
        "emissions_2030": DEFAULT_EMISSIONS_2030,
        "target_2050": DEFAULT_TARGET_2050,
        "sequestration_percent": DEFAULT_SEQUESTRATION_PERCENT,
        "forest_area_available": INDONESIA_FOREST_AREA,
        "coastal_area_available": INDONESIA_COASTAL_AREA,
        "forest_percent": 80,
        "forest_rate": FOREST_SEQUESTRATION_RATE,
        "coastal_rate": COASTAL_SEQUESTRATION_RATE,
        "root_to_shoot_ratio": ROOT_TO_SHOOT_RATIO,
        "start_year": DEFAULT_START_YEAR,
        "target_year": DEFAULT_TARGET_YEAR,
        "include_below_ground": False,
        "risk_factor": 0
    }
    
    # Calculate default result
    default_input = CalculatorInput(**defaults)
    result = calculate_sequestration(default_input)
    scenarios = compare_scenarios(default_input)
    chart_data = generate_trajectory(default_input, result)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "defaults": defaults,
            "result": result,
            "scenarios": scenarios,
            "scenario_presets": SCENARIOS,
            "chart_data": chart_data.model_dump()
        }
    )


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    emissions_2030: Annotated[float, Form()],
    target_2050: Annotated[float, Form()],
    sequestration_percent: Annotated[float, Form()],
    forest_area_available: Annotated[float, Form()],
    coastal_area_available: Annotated[float, Form()],
    forest_percent: Annotated[float, Form()],
    forest_rate: Annotated[float, Form()],
    coastal_rate: Annotated[float, Form()],
    root_to_shoot_ratio: Annotated[float, Form()],
    start_year: Annotated[int, Form()],
    target_year: Annotated[int, Form()],
    include_below_ground: Annotated[bool, Form()] = False,
    risk_factor: Annotated[float, Form()] = 0,
    scenario: Annotated[str, Form()] = "custom"
):
    """Process calculation and return results"""
    
    # Build input model
    calc_input = CalculatorInput(
        emissions_2030=emissions_2030,
        target_2050=target_2050,
        sequestration_percent=sequestration_percent,
        forest_area_available=forest_area_available,
        coastal_area_available=coastal_area_available,
        forest_percent=forest_percent,
        forest_rate=forest_rate,
        coastal_rate=coastal_rate,
        root_to_shoot_ratio=root_to_shoot_ratio,
        start_year=start_year,
        target_year=target_year,
        include_below_ground=include_below_ground,
        risk_factor=risk_factor,
        scenario=ScenarioType(scenario) if scenario != "custom" else ScenarioType.CUSTOM
    )
    
    # Calculate results
    result = calculate_sequestration(calc_input)
    scenarios = compare_scenarios(calc_input)
    chart_data = generate_trajectory(calc_input, result)
    
    # Build defaults from current input
    defaults = {
        "emissions_2030": emissions_2030,
        "target_2050": target_2050,
        "sequestration_percent": sequestration_percent,
        "forest_area_available": forest_area_available,
        "coastal_area_available": coastal_area_available,
        "forest_percent": forest_percent,
        "forest_rate": forest_rate,
        "coastal_rate": coastal_rate,
        "root_to_shoot_ratio": root_to_shoot_ratio,
        "start_year": start_year,
        "target_year": target_year,
        "include_below_ground": include_below_ground,
        "risk_factor": risk_factor
    }
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "defaults": defaults,
            "result": result,
            "scenarios": scenarios,
            "scenario_presets": SCENARIOS,
            "chart_data": chart_data.model_dump()
        }
    )


@app.get("/references", response_class=HTMLResponse)
async def references(request: Request):
    """Render the references page with academic citations"""
    return templates.TemplateResponse(
        "references.html",
        {
            "request": request,
            "references": REFERENCES
        }
    )


@app.get("/api/defaults")
async def get_defaults():
    """API endpoint to get default IPCC values"""
    return {
        "emissions": {
            "baseline_2030": DEFAULT_EMISSIONS_2030,
            "target_2050": DEFAULT_TARGET_2050,
            "sequestration_percent": DEFAULT_SEQUESTRATION_PERCENT
        },
        "areas": {
            "forest_ha": INDONESIA_FOREST_AREA,
            "coastal_ha": INDONESIA_COASTAL_AREA
        },
        "rates": {
            "forest_tco2_ha_yr": FOREST_SEQUESTRATION_RATE,
            "coastal_tco2_ha_yr": COASTAL_SEQUESTRATION_RATE,
            "root_to_shoot_ratio": ROOT_TO_SHOOT_RATIO
        },
        "scenarios": {
            name: {
                "name": s.name,
                "forest_percent": s.forest_percent * 100,
                "coastal_percent": s.coastal_percent * 100,
                "include_below_ground": s.include_below_ground,
                "description": s.description
            }
            for name, s in SCENARIOS.items()
        }
    }


@app.get("/api/references")
async def get_references():
    """API endpoint to get academic references"""
    return [
        {
            "id": ref.id,
            "authors": ref.authors,
            "year": ref.year,
            "title": ref.title,
            "journal": ref.journal,
            "key_finding": ref.key_finding,
            "doi": ref.doi,
            "url": ref.url
        }
        for ref in REFERENCES
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
