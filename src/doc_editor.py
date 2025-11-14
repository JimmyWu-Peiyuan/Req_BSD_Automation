from pathlib import Path
from typing import Dict, Any, Optional
from docxtpl import DocxTemplate
import json
import logging
from datetime import datetime

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def replace_placeholders(
    placeholders: Dict[str, Any],
    output_filename: str,
    template_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    config_path: Optional[str] = None
) -> Path:
    """
    Load template, replace placeholders, and save as a new document.
    
    Args:
        placeholders: Dictionary of placeholder names and their replacement values.
        Placeholders in template should use Jinja2 syntax: {{ placeholder_name }}
        Example: {"title": "My Document", "author": "John Doe"}
        output_filename: Name for the output file (e.g., "my_document.docx")
        template_path: Path to template file. If None, loads from config.json
        output_dir: Output directory. If None, uses output_directory from config.json
        config_path: Path to config.json. If None, looks for config.json in project root.
    
    Returns:
        Path to the generated document
    
    Example:
        replace_placeholders(
            placeholders={"title": "My Document", "date": "2024-01-15"},
            output_filename="my_document.docx"
        )
    """
    # Load config if needed
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.json"
    else:
        config_path = Path(config_path)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        paths = config.get("paths", {})
    else:
        paths = {}
    
    # Get template path
    if template_path is None:
        template_file = paths.get("template_file")
        if not template_file:
            raise ValueError("template_path not provided and template_file not found in config.json")
        template_path_obj = Path(template_file)
        if not template_path_obj.is_absolute():
            template_path_obj = Path(__file__).parent.parent / template_path_obj
        template_path = str(template_path_obj)
    
    template_file = Path(template_path)
    
    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    if not template_file.suffix.lower() == '.docx':
        raise ValueError(f"Template must be a .docx file, got: {template_file.suffix}")
    
    # Get output directory
    if output_dir is None:
        output_dir = paths.get("output_directory", "output")
    
    output_dir_path = Path(output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = Path(__file__).parent.parent / output_dir_path
    
    # Ensure output filename has .docx extension
    if not output_filename.endswith('.docx'):
        output_filename = f"{output_filename}.docx"
    
    output_file = output_dir_path / output_filename
    
    # Load template
    doc = DocxTemplate(str(template_file))
    logger.info(f"Loaded template: {template_file}")
    
    # Add date placeholder if not already provided
    if "DDMMYYYY" not in placeholders:
        today_date = datetime.now().strftime("%d %B %Y")  # e.g., "13 November 2025"
        placeholders["DDMMYYYY"] = today_date
    
    # Replace placeholders
    try:
        logger.info(f"Rendering with placeholders: {list(placeholders.keys())}")
        doc.render(placeholders)
        logger.info(f"Replaced {len(placeholders)} placeholders")
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        logger.error(f"Placeholders provided: {list(placeholders.keys())}")
        # Log first 200 chars of each placeholder value for debugging
        for key, value in placeholders.items():
            value_preview = str(value)[:200] if value else "None"
            logger.error(f"  {key}: {value_preview}...")
        raise
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save document
    doc.save(str(output_file))
    logger.info(f"Saved document to: {output_file}")
    
    return output_file


# Example usage
if __name__ == "__main__":
    import sys
    
    try:
        # Example placeholders
        example_placeholders = {
            "title": "Business Solution Document",
            "product_name": "Travel Insurance",
            "domain": "Policy Issuance",
            "version": "1.0",
            "date": "2024-01-15"
        }
        
        # Replace placeholders and save with specified filename
        output_file = replace_placeholders(
            placeholders=example_placeholders,
            output_filename="bsd_travel_policy.docx"
        )
        
        print(f"\n✓ Document rendered successfully!")
        print(f"  Output: {output_file}")
        print(f"\n  Placeholders used: {list(example_placeholders.keys())}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
