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
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from calculator.models import CalculatorInput
from calculator.formulas import calculate_sequestration, generate_all_chart_data
from calculator.constants import (
    REFERENCES,
    DEFAULT_EMISSIONS_INITIAL,
    DEFAULT_EMISSIONS_PEAK,
    DEFAULT_TARGET_2050,
    DEFAULT_SEQUESTRATION_PERCENT,
    INDONESIA_FOREST_AREA,
    INDONESIA_COASTAL_AREA,
    FOREST_SEQUESTRATION_RATE,
    COASTAL_SEQUESTRATION_RATE,
    ROOT_TO_SHOOT_RATIO,
    DEFAULT_INITIAL_YEAR,
    DEFAULT_PEAK_YEAR,
    DEFAULT_TARGET_YEAR,
    DEFAULT_NEW_PLANTING_START_YEAR,
    DEFAULT_NEW_PLANTING_FOREST_PERCENT,
    DEFAULT_EXISTING_FOREST_STATUS,
    EXISTING_FOREST_STATUS_OPTIONS,
    SEQUESTRATION_DEGRADATION_RATE
)

# Initialize FastAPI app
app = FastAPI(
    title="Indonesia Carbon Sequestration Calculator",
    description="Calculate required forest and coastal area for 2050 targets",
    version="1.0.0"
)

# Add middleware to handle HTTPS behind reverse proxy (Coolify/Traefik)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Get the directory where main.py is located (works in Docker)
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Configure templates with absolute path
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main calculator page"""
    
    # Default values for the form (3-point emission model)
    defaults = {
        # Emission Data Points
        "emissions_initial": DEFAULT_EMISSIONS_INITIAL,
        "emissions_peak": DEFAULT_EMISSIONS_PEAK,
        "target_2050": DEFAULT_TARGET_2050,
        "sequestration_percent": DEFAULT_SEQUESTRATION_PERCENT,
        
        # Year Parameters
        "initial_year": DEFAULT_INITIAL_YEAR,
        "peak_year": DEFAULT_PEAK_YEAR,
        "target_year": DEFAULT_TARGET_YEAR,
        "new_planting_start_year": DEFAULT_NEW_PLANTING_START_YEAR,
        
        # Existing Forest
        "forest_area_available": INDONESIA_FOREST_AREA,
        "coastal_area_available": INDONESIA_COASTAL_AREA,
        "existing_forest_status": DEFAULT_EXISTING_FOREST_STATUS,
        "existing_forest_status_options": EXISTING_FOREST_STATUS_OPTIONS,
        
        # New Planting Allocation
        "new_planting_forest_percent": DEFAULT_NEW_PLANTING_FOREST_PERCENT,
        
        # Sequestration Rates
        "forest_rate": FOREST_SEQUESTRATION_RATE,
        "coastal_rate": COASTAL_SEQUESTRATION_RATE,
        "root_to_shoot_ratio": ROOT_TO_SHOOT_RATIO,
        "include_below_ground": False,
        "degradation_rate": SEQUESTRATION_DEGRADATION_RATE * 100.0,
        
        # Risk Factor
        "risk_factor": 0
    }
    
    # Calculate default result
    default_input = CalculatorInput()
    result = calculate_sequestration(default_input)
    chart_data = generate_all_chart_data(default_input)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "defaults": defaults,
            "result": result,
            "chart_data": chart_data.model_dump()
        }
    )


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    # Emission Data Points (3-point model)
    emissions_initial: Annotated[float, Form()],
    emissions_peak: Annotated[float, Form()],
    target_2050: Annotated[float, Form()],
    sequestration_percent: Annotated[float, Form()],
    
    # Year Parameters
    initial_year: Annotated[int, Form()],
    peak_year: Annotated[int, Form()],
    target_year: Annotated[int, Form()],
    new_planting_start_year: Annotated[int, Form()],
    
    # Existing Forest
    forest_area_available: Annotated[float, Form()],
    coastal_area_available: Annotated[float, Form()],
    existing_forest_status: Annotated[str, Form()] = "mixed",
    
    # New Planting Allocation
    new_planting_forest_percent: Annotated[float, Form()] = 80,
    
    # Sequestration Rates
    forest_rate: Annotated[float, Form()] = FOREST_SEQUESTRATION_RATE,
    coastal_rate: Annotated[float, Form()] = COASTAL_SEQUESTRATION_RATE,
    root_to_shoot_ratio: Annotated[float, Form()] = ROOT_TO_SHOOT_RATIO,
    include_below_ground: Annotated[bool, Form()] = False,
    
    # Risk Factor
    risk_factor: Annotated[float, Form()] = 0,
    
    # Degradation Rate (from range slider)
    degradation_rate: Annotated[float, Form()] = SEQUESTRATION_DEGRADATION_RATE * 100.0
):
    """Process calculation and return results"""
    
    # Build input model
    calc_input = CalculatorInput(
        emissions_initial=emissions_initial,
        emissions_peak=emissions_peak,
        target_2050=target_2050,
        sequestration_percent=sequestration_percent,
        initial_year=initial_year,
        peak_year=peak_year,
        target_year=target_year,
        new_planting_start_year=new_planting_start_year,
        forest_area_available=forest_area_available,
        coastal_area_available=coastal_area_available,
        existing_forest_status=existing_forest_status,
        new_planting_forest_percent=new_planting_forest_percent,
        forest_rate=forest_rate,
        coastal_rate=coastal_rate,
        root_to_shoot_ratio=root_to_shoot_ratio,
        include_below_ground=include_below_ground,
        risk_factor=risk_factor,
        degradation_rate=degradation_rate
    )
    
    # Calculate results
    result = calculate_sequestration(calc_input)
    chart_data = generate_all_chart_data(calc_input)
    
    # Build defaults from current input
    defaults = {
        "emissions_initial": emissions_initial,
        "emissions_peak": emissions_peak,
        "target_2050": target_2050,
        "sequestration_percent": sequestration_percent,
        "initial_year": initial_year,
        "peak_year": peak_year,
        "target_year": target_year,
        "new_planting_start_year": new_planting_start_year,
        "forest_area_available": forest_area_available,
        "coastal_area_available": coastal_area_available,
        "existing_forest_status": existing_forest_status,
        "existing_forest_status_options": EXISTING_FOREST_STATUS_OPTIONS,
        "new_planting_forest_percent": new_planting_forest_percent,
        "forest_rate": forest_rate,
        "coastal_rate": coastal_rate,
        "root_to_shoot_ratio": root_to_shoot_ratio,
        "include_below_ground": include_below_ground,
        "risk_factor": risk_factor,
        "degradation_rate": degradation_rate
    }
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "defaults": defaults,
            "result": result,
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


@app.get("/methodology", response_class=HTMLResponse)
async def methodology(request: Request):
    """Render the methodology and theory page"""
    return templates.TemplateResponse(
        "methodology.html",
        {
            "request": request
        }
    )


@app.get("/api/defaults")
async def get_defaults():
    """API endpoint to get default IPCC values"""
    return {
        "emissions": {
            "initial": DEFAULT_EMISSIONS_INITIAL,
            "initial_year": DEFAULT_INITIAL_YEAR,
            "peak": DEFAULT_EMISSIONS_PEAK,
            "peak_year": DEFAULT_PEAK_YEAR,
            "target_2050": DEFAULT_TARGET_2050,
            "target_year": DEFAULT_TARGET_YEAR,
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
        "new_planting": {
            "start_year": DEFAULT_NEW_PLANTING_START_YEAR,
            "forest_percent": DEFAULT_NEW_PLANTING_FOREST_PERCENT
        },
        "degradation_rate": SEQUESTRATION_DEGRADATION_RATE * 100.0,
        "existing_forest_status_options": EXISTING_FOREST_STATUS_OPTIONS,
        "default_existing_forest_status": DEFAULT_EXISTING_FOREST_STATUS
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
