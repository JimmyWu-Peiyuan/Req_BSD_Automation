from pathlib import Path
from typing import Dict, Any, Optional, List
from docxtpl import DocxTemplate, Subdoc
import json
import logging
from datetime import datetime
import tempfile
import os

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _resolve_path(path_str: str, base_dir: Path) -> Path:
    """Resolve relative path to absolute path."""
    path = Path(path_str)
    return path if path.is_absolute() else base_dir / path
  

def _load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load config.json and return paths dictionary."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"
    else:
        config_path = Path(config_path)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f).get("paths", {})
    return {}



def replace_placeholders(
    placeholders: Dict[str, Any],
    output_filename: str,
    template_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    config_path: Optional[str] = None
) -> Path:
    """
    Load template, replace placeholders, and save as a new document.
    """
    base_dir = Path(__file__).parent.parent
    paths = _load_config(config_path)
    
    # Resolve template path FIRST (needed for Subdoc creation)
    if template_path is None:
        template_file = paths.get("template_file")
        if not template_file:
            raise ValueError("template_path not provided and template_file not found in config.json")
        template_path = template_file
    
    template_file = _resolve_path(template_path, base_dir)
    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")
    if template_file.suffix.lower() != '.docx':
        raise ValueError(f"Template must be a .docx file, got: {template_file.suffix}")
    
    # Load main template FIRST (needed for Subdoc creation)
    doc = DocxTemplate(str(template_file))
    logger.info(f"Loaded template: {template_file}")
    
    # NOTE Step 1: Create function blocks using main document
    if placeholders.get('function_contents'):
        function_contents = placeholders.pop('function_contents')
        block_template_path = paths.get("block_template_file")
        
        if block_template_path:
            block_path = _resolve_path(block_template_path, base_dir)
            if block_path.exists():
                logger.info(f"Creating function blocks from template: {block_path}")
                # Create Subdocs using main document's new_subdoc method
                function_blocks = []
                for func_data in function_contents:
                    # First, render the block template with function-specific data
                    block_template = DocxTemplate(str(block_path))
                    block_template.render({
                        'function_name': func_data['function_name'],
                        'summary': func_data['summary'],
                        'implementation': func_data['implementation'],
                    })
                    
                    # Save rendered block to temporary location
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
                    temp_file.close()
                    block_template.save(temp_file.name)
                    
                    # Create subdoc from the rendered document
                    subdoc = doc.new_subdoc(temp_file.name)
                    function_blocks.append(subdoc)
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
                
                placeholders['function_blocks'] = function_blocks
                logger.info(f"Created {len(function_blocks)} function blocks")
            else:
                logger.warning(f"Block template not found: {block_path} - skipping function blocks")
                placeholders['function_blocks'] = []
        else:
            logger.warning("block_template_file not found in config.json - skipping function blocks")
            placeholders['function_blocks'] = []
    else:
        placeholders['function_blocks'] = []
    
    # Resolve output directory
    if output_dir is None:
        output_dir = paths.get("output_directory", "output")
    
    output_dir_path = _resolve_path(output_dir, base_dir)
    
    # Ensure output filename has .docx extension
    if not output_filename.endswith('.docx'):
        output_filename = f"{output_filename}.docx"
    
    output_file = output_dir_path / output_filename
    
    # NOTE Step 2.1 Add date placeholder
    placeholders["DDMMYYYY"] = datetime.now().strftime("%d %B %Y")
    
    # NOTE Step 2.2 Replace placeholders  
    try:
        logger.info(f"Rendering with placeholders: {list(placeholders.keys())}")
        doc.render(placeholders)
        logger.info(f"Replaced {len(placeholders)} placeholders")
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        logger.error(f"Placeholders provided: {list(placeholders.keys())}")
        for key, value in placeholders.items():
            logger.error(f"  {key}: {str(value)[:200] if value else 'None'}...")
        raise
    
    # NOTE Step 3: Save document
    output_file.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_file))
    logger.info(f"Saved document to: {output_file}")
    
    return output_file


# Example usage
if __name__ == "__main__":
    import sys
    
    try:
        # Dummy test data - matches the structure from app.py
        example_placeholders = {
            "business_solution_overview": """
            This chapter outlines the motor insurance workflows, detailing its functionality, 
            step-by-step process, data handling, field definitions, and specific business rules. 
            It provides clarity on how customers interact with the system, the integrations involved, 
            and the differences across regions. The system supports comprehensive policy management 
            including product definition, premium calculation, and policy issuance capabilities.
            """,
            
            "function_contents": [
                {
                    "function_name": "Product Definition",
                    "summary": """
                    The Product Definition function enables the creation and management of insurance products 
                    within the system. Each product must have a unique code and name to ensure clear identification. 
                    Products define specific coverage types such as Comprehensive, Auto Liability, and Liability Coverage. 
                    Additionally, each product supports multiple plans with varying benefits and coverage limits, 
                    typically categorized as Basic, Standard, and Premium tiers.
                    """,
                    "implementation": """
                    Step 1: Create a new product with a unique product code and name.
                    Step 2: Define the coverage types available for this product (e.g., Comprehensive, Liability).
                    Step 3: Configure product-specific business rules and validation criteria.
                    Step 4: Set up plan tiers (Basic, Standard, Premium) with their respective benefits.
                    Step 5: Define coverage limits and exclusions for each plan tier.
                    Step 6: Activate the product for use in policy issuance workflows.
                    """,
                    "requirement_count": 5
                },
                {
                    "function_name": "Premium Definition",
                    "summary": """
                    The Premium Definition function handles the calculation and configuration of insurance premiums 
                    based on various risk factors and coverage selections. It supports dynamic pricing models that 
                    adjust premiums according to customer risk profiles, coverage options, and regional variations.
                    """,
                    "implementation": """
                    Step 1: Define base premium rates for each product and coverage type.
                    Step 2: Configure risk factor multipliers (age, driving history, vehicle type).
                    Step 3: Set up regional pricing variations and surcharges.
                    Step 4: Implement premium calculation algorithms based on selected coverage.
                    Step 5: Apply discounts and promotional pricing rules.
                    Step 6: Validate calculated premiums against business rules and limits.
                    """,
                    "requirement_count": 4
                }
            ],
            
            "non_functional_requirements": "REQ-001: The system shall support a minimum of 10,000 concurrent users without performance degradation.\nREQ-002: All user data must be encrypted using AES-256 encryption standards."
        }
        
        # Replace placeholders and save with specified filename
        output_file = replace_placeholders(
            placeholders=example_placeholders,
            output_filename="test_bsd_document.docx"
        )
        
        print(f"\n✓ Document rendered successfully!")
        print(f"  Output: {output_file}")
        print(f"\n  Placeholders used: {list(example_placeholders.keys())}")
        print(f"  Function blocks created: {len(example_placeholders.get('function_contents', []))}")
        print(f"  Non-functional requirements: {len(example_placeholders.get('non_functional_requirements', []))}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
