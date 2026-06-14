from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
WEB_EXPORT_DIR = DATA_DIR / "web_exports"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DOCS_DIR = PROJECT_ROOT / "docs"

SEED = 42

PLANTS = ["North Plant", "South Plant", "West Plant"]
SHIFTS = ["Day", "Swing", "Night"]
SHIFT_WEIGHTS = {"Day": 0.40, "Swing": 0.35, "Night": 0.25}

MACHINE_SPECS = [
    {"machine_id": "M-101", "plant": "North Plant", "production_line": "Line A", "machine_type": "Press", "install_year": 2012, "criticality": "High"},
    {"machine_id": "M-102", "plant": "North Plant", "production_line": "Line A", "machine_type": "Weld", "install_year": 2017, "criticality": "Medium"},
    {"machine_id": "M-103", "plant": "North Plant", "production_line": "Line B", "machine_type": "CNC", "install_year": 2015, "criticality": "High"},
    {"machine_id": "M-201", "plant": "South Plant", "production_line": "Line C", "machine_type": "Press", "install_year": 2018, "criticality": "Medium"},
    {"machine_id": "M-202", "plant": "South Plant", "production_line": "Line C", "machine_type": "Assembler", "install_year": 2010, "criticality": "High"},
    {"machine_id": "M-203", "plant": "South Plant", "production_line": "Line D", "machine_type": "Robot", "install_year": 2019, "criticality": "Low"},
    {"machine_id": "M-301", "plant": "West Plant", "production_line": "Line E", "machine_type": "CNC", "install_year": 2014, "criticality": "High"},
    {"machine_id": "M-302", "plant": "West Plant", "production_line": "Line E", "machine_type": "Pack", "install_year": 2016, "criticality": "Medium"},
]

PRODUCTS = [
    {"product_id": "P-100", "product_name": "Drive Shaft", "product_family": "Powertrain", "standard_cycle_time_seconds": 42.0, "unit_margin": 14.0},
    {"product_id": "P-200", "product_name": "Bracket Assembly", "product_family": "Structural", "standard_cycle_time_seconds": 55.0, "unit_margin": 10.0},
    {"product_id": "P-300", "product_name": "Sensor Housing", "product_family": "Electronics", "standard_cycle_time_seconds": 36.0, "unit_margin": 18.0},
    {"product_id": "P-400", "product_name": "Valve Body", "product_family": "Fluid", "standard_cycle_time_seconds": 48.0, "unit_margin": 12.0},
    {"product_id": "P-500", "product_name": "Control Panel", "product_family": "Electronics", "standard_cycle_time_seconds": 39.0, "unit_margin": 16.0},
    {"product_id": "P-600", "product_name": "Gear Carrier", "product_family": "Powertrain", "standard_cycle_time_seconds": 51.0, "unit_margin": 11.0},
]
