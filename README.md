# Requirements to BSD Document Automation

**CMU Capstone Project - Peak3 Team**

An automated system that generates Business Solution Documents (BSD) from requirement specifications using Large Language Models (LLMs). This tool processes requirement spreadsheets, groups requirements by function, and generates comprehensive BSD documents with function-specific summaries and implementation guides.

## Features

- **Automated BSD Generation**: Converts requirement spreadsheets into professional BSD documents
- **Function-Based Organization**: Groups requirements by function and generates function-specific content blocks
- **LLM-Powered Content**: Uses OpenAI API to generate business solution overviews, function summaries, and step-by-step implementations
- **Dynamic Document Assembly**: Creates Word documents with dynamic function blocks using `docxtpl` and subdocuments
- **Non-Functional Requirements**: Automatically Extracted**: Separates and lists non-functional requirements at the end of documents
- **Case-Insensitive Function Matching**: Handles function names regardless of case variations

## Project Structure

```
Req_BSD_Automation/
├── src/
│   ├── app.py              # Main orchestration logic, LLM content generation
│   ├── bsd_mapping.py
│              #, Requirement separation and BSD grouping
│   ├── doc_editor.py
│              #, Word document template rendering and Subdoc creation
│   ├── llm.py
│              #, LLM interface and API integration
│   └── prompts.py
│              #, Prompt templates for LLM content generation
├── data/
│   ├── ReqListExample.xlsm
│              #, Example requirements spreadsheet
│   ├── templates/
│   │   ├── bsd_template_clean.docx
│   │              #, Main BSD document template
│   │   └── bsd_function_block.docx
│   │              #, Function block sub-template
│   └── output/
│              #, Generated BSD documents
├── config.json
│              #, Configuration file for paths and settings
├── requirements.txt
│              #, Python dependencies
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/JimmyWu-Peiyuan/Req_BSD_Automation.git
   cd Req_BSD_Automation
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

## Configuration

Edit `config.json` to configure file paths:

```json
{
  "paths": {
    "requirements_file": "data/ReqListExample.xlsm",
    "template_file": "data/templates/bsd_template_clean.docx",
    "block_template_file": "data/templates/bsd_function_block.docx",
    "output_directory": "data/output"
  }
}
```

## Usage

### Basic Usage

Run the main script to generate BSD documents:

```bash
python src/app.py
```

The script will:
1. Load requirements from the configured Excel file
2. Separate requirements into BSD groups
3. Generate content using the LLM for each BSD
4. Create function-specific blocks for each unique function
5. Generate and save BSD documents to the output directory

### Requirements File Format

Your requirements Excel file should include the following columns:
- **BSD ID**: Identifier for grouping requirements into BSDs
- **Requirement**: Requirement ID or identifier
- **Description**: Detailed requirement description
- **Requirement type**: "Functional" or "Non-functional"
- **Function**: Function name (for functional requirements)

### Template Files

#### Main Template (`bsd_template_clean.docx`)

Should include placeholders:
- `{{ business_solution_overview }}` - Business solution overview
- `{% for block in function_blocks %}{{p block }}{% endfor %}` - Function blocks loop
- `{{ non_functional_requirements }}` - Non-functional requirements list
- `{{ DDMMYYYY }}` - Date (automatically added)

#### Function Block Template (`bsd_function_block.docx`)

Should include placeholders:
- `{{ function_name }}` - Function name
- `{{ summary }}` - Function summary
- `{{ implementation }}` - Step-by-step implementation

## How It Works

1. **Requirement Separation** (`bsd_mapping.py`):
   - Reads requirements from Excel file
   - Groups requirements by BSD ID
   - Extracts unique functions (case-insensitive)
   - Separates functional and non-functional requirements

2. **Content Generation** (`app.py`):
   - For each BSD group:
     - Generates business solution overview using LLM
     - For each unique function:
       - Filters requirements for that function
       - Generates function summary using LLM
       - Generates step-by-step implementation using LLM
   - Extracts non-functional requirements

3. **Document Assembly** (`doc_editor.py`):
   - Loads main template
   - Creates Subdoc instances for each function block
   - Renders function blocks with generated content
   - Inserts blocks into main template
   - Saves final document

## Dependencies

- `docxtpl[subdoc]` - Word document template rendering with subdocument support
- `openai` - OpenAI API client
- `pandas` - Data manipulation and Excel reading
- `openpyxl` - Excel file support for pandas
- `python-dotenv` - Environment variable management

## Testing

Test the document generation without LLM calls:

```bash
python src/doc_editor.py
```

This runs with dummy data to test template rendering and Subdoc insertion.

## Troubleshooting

### Common Issues

1. **`ImportError: cannot import name 'Subdoc'`**
   - Solution: Install `docxtpl[subdoc]` instead of just `docxtpl`
   ```bash
   pip install 'docxtpl[subdoc]'
   ```

2. **Function blocks not appearing in document**
   - Ensure template uses `{{p block }}` syntax (not `{{ block }}`)
   - Check that `block_template_file` is configured in `config.json`
   - Verify block template file exists

3. **LLM API errors**
   - Verify `OPENAI_API_KEY` is set in `.env` file
   - Check API quota and billing status

## Contributing

This is a CMU Capstone project. For questions or contributions, please contact the Peak3 team.

## License

See LICENSE file for details.

## Authors

CMU Capstone Project - Peak3 Team
