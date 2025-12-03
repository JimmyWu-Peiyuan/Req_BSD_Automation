# BSD Document Generator

> Automatically generate Business Solution Documents (BSDs) from requirements spreadsheets using AI-powered content generation.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

The BSD Document Generator is a web-based application that automates the creation of Business Solution Documents from requirements spreadsheets. It uses AI (OpenAI GPT) to generate comprehensive business solution overviews, function summaries, and step-by-step implementations, significantly reducing the time and effort required for manual document creation.

### Key Features

- **Automated Document Generation**: Convert requirements spreadsheets into professional BSD documents
- **AI-Powered Content**: Uses OpenAI GPT to generate summaries and implementations
- **Multiple Format Support**: Accepts Excel (.xlsm, .xlsx) and CSV files

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Req_BSD_Automation
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
```

## Quick Start

1. **Start the Flask application:**

```bash
python app.py
```

2. **Open your browser:**

Navigate to `http://localhost:5001`

3. **Upload a requirements file:**

   - Drag and drop or click to select an Excel (.xlsm, .xlsx) or CSV file
   - Click "Analyze Requirements" to preview the analysis
   - Click "Generate BSD Documents" to start generation
   - Monitor progress in real-time
   - Download your generated documents when complete

## Usage

### Requirements File Format

Your requirements file should contain the following columns:

- **Requirement ID**: Unique identifier for each requirement
- **Description**: Detailed description of the requirement
- **Function**: Function name associated with the requirement
- **Requirement Type**: Either "Functional" or "Non-functional"
- **Product**: Product name
- **Domain**: Domain name

### Workflow

1. **Upload**: Select your requirements file (.xlsm, .xlsx, or .csv)
2. **Analyze**: Review the analysis results showing:
   - Number of BSDs to generate
   - Products and domains identified
   - Number of requirements per BSD
   - Unique functions found
3. **Generate**: Start document generation and monitor progress:
   - Business Solution Overview generation
   - Function summaries (one per unique function)
   - Function implementations (one per unique function)
   - Document assembly
4. **Download**: Retrieve your generated BSD documents

### Generated Document Structure

The program will fill out information below:

- **Business Solution Overview**: High-level summary of the solution
- **Function Blocks**: For each unique function:
  - Function name
  - Summary: Brief overview of the function
  - Implementation: Detailed step-by-step implementation guide
- **Non-Functional Requirements**: List of all non-functional requirements

## Project Structure

```
Req_BSD_Automation/
├── app.py                      # Flask web application
├── config.json                 # Configuration file for paths
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── .gitignore                  # Git ignore rules
│
├── frontend/                   # Frontend files
│   ├── templates/
│   │   └── index.html         # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css      # Styles
│       ├── js/
│       │   └── app.js         # Frontend JavaScript
│       └── images/
│           └── peak3logo.avif  # Logo
│
├── src/                        # Core application logic
│   ├── app.py                 # Main document generation logic
│   ├── bsd_mapping.py         # Requirements separation and BSD grouping
│   ├── doc_editor.py          # Document template rendering
│   ├── llm.py                 # LLM integration (OpenAI)
│   └── prompts.py             # LLM prompt templates
│
├── data/                       # Data directory (ignored by git)
│   ├── templates/             # Word document templates
│   │   ├── bsd_template_clean.docx
│   │   └── bsd_function_block.docx
│   ├── output/                # Generated documents
│   └── ReqListExample.xlsm    # Example requirements file
│
└── README.md                   # This file
```

## Configuration

### config.json

The `config.json` file contains paths to templates and data directories, feel free to modify them when making changes:

```json
{
  "paths": {
    "requirements_file": "data/ReqListExample.xlsm",
    "template_file": "data/templates/bsd_template_clean.docx",
    "block_template_file": "data/templates/bsd_function_block.docx",
    "output_directory": "data/output",
    "data_directory": "data",
    "templates_directory": "data/templates"
  }
}
```

### Web Interface

- `GET /` - Main web interface

## Development

### Running in Development Mode

The Flask app runs in debug mode by default. To run:

```bash
python app.py
```

### Running in Production

Disable debug mode in `app.py`:

```python
app.run(debug=False, host='0.0.0.0', port=5001)
```

### Code Structure

- **`src/app.py`**: Core document generation logic, LLM orchestration
- **`src/bsd_mapping.py`**: Requirements separation and BSD grouping logic
- **`src/doc_editor.py`**: Document template rendering using `docxtpl`
- **`src/llm.py`**: OpenAI API integration
- **`src/prompts.py`**: LLM prompt templates
- **`app.py`**: Flask web application with API endpoints

### Key Technologies

- **Flask**: Web framework
- **docxtpl**: Word document template rendering
- **OpenAI API**: AI content generation
- **Pandas**: Data manipulation and analysis
- **Jinja2**: Template engine (used by docxtpl)

## License

See [LICENSE](LICENSE) file for details.

## Acknowledgments

- CMU Capstone Program
- Peak3 Team
- OpenAI for GPT API
