# PDF Requirements Parser

A standalone Python script that intelligently separates PDF content into main requirements text and user comments/annotations. Supports both text-based and scanned PDFs with OCR capabilities.

## Features

- 🔍 **Dual PDF Support**: Processes both text-based and scanned (image) PDFs
- 📝 **Content Separation**: Cleanly separates requirements from annotations
- 🎯 **Annotation Extraction**: Captures author, type, content, and metadata
- 🖼️ **OCR Pipeline**: Converts scanned pages to text using Tesseract
- 📊 **Structured Output**: Generates organized JSON files for easy processing
- ⚡ **Efficient Processing**: Page-by-page processing for large documents
- 🎨 **Content Classification**: Identifies headings, lists, tables, and paragraphs

## Prerequisites

### System Requirements

1. **Tesseract OCR** (required for scanned PDF support)
   - **Windows**: Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

2. **Python 3.11+**

### UV Installation

This project uses UV for dependency management:

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows with PowerShell:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation

1. **Clone or download the project**

2. **Install dependencies using UV**:

   ```bash
   cd pdf-parser
   uv install
   ```

This will install all required packages:

- `PyPDF2` - PDF reading and annotation extraction
- `pdfplumber` - Structured text extraction
- `pytesseract` - OCR interface
- `Pillow` - Image processing
- `python-docx` - Optional Word export

## Usage

### Basic Command

```bash
uv run python pdf_requirements_parser.py --input document.pdf --output-dir ./output
```

### Command-Line Arguments

- `--input`, `-i`: Path to the input PDF file (required)
- `--output-dir`, `-o`: Directory to save output JSON files (required)

### Examples

```bash
# Parse a requirements document
uv run python pdf_requirements_parser.py -i requirements.pdf -o ./parsed_data

# Process a scanned PDF
uv run python pdf_requirements_parser.py --input scanned_doc.pdf --output-dir ./results
```

## Output Format

The script generates two JSON files:

### 1. requirements.json

Contains main text content organized by page:

```json
{
  "page_1": [
    {
      "id": 1,
      "type": "heading",
      "text": "SYSTEM REQUIREMENTS",
      "line_count": 1
    },
    {
      "id": 2,
      "type": "paragraph",
      "text": "The system shall provide user authentication...",
      "line_count": 3
    },
    {
      "id": 3,
      "type": "list_item",
      "text": "• Support for multiple user roles",
      "line_count": 1
    }
  ],
  "page_2": [...]
}
```

### 2. comments.json

Contains all annotations with metadata:

```json
{
  "page_1": [
    {
      "id": 1,
      "page": 1,
      "type": "Highlight",
      "author": "John Doe",
      "text": "This requirement needs clarification",
      "subject": "Review",
      "color": "#ffff00"
    }
  ],
  "page_2": [...]
}
```

## Content Classification

The parser automatically classifies content types:

- **heading**: Short text, uppercase, or ending with colon
- **list_item**: Starts with bullets (•, -, *) or numbers
- **table**: Contains tabs or pipe characters
- **paragraph**: Regular text content

## Architecture

### Key Components

1. **PDFRequirementsParser**: Main parser class
   - `_extract_requirements()`: Extracts main text content
   - `_extract_annotations()`: Extracts PDF annotations
   - `_perform_ocr()`: Handles scanned page processing
   - `_parse_text_content()`: Structures extracted text

2. **Processing Pipeline**:

   ```text
   PDF Input → Text Extraction → Content Classification → JSON Output
             ↓ (if scanned)
           OCR Processing
             ↓
           Text Extraction
   ```

3. **Annotation Handling**:

   ```text
   PDF Annotations → Parse Metadata → Extract Content → JSON Output
   ```

## Error Handling

The script handles common issues:

- **Missing PDF file**: Clear error message with file path
- **Scanned pages without OCR**: Warning with graceful degradation
- **Corrupt annotations**: Skips problematic annotations with warnings
- **Unsupported content**: Logs warnings but continues processing

## Performance Considerations

- **Page-by-page processing**: Efficient memory usage for large PDFs
- **Lazy loading**: Opens files only when needed
- **High-resolution OCR**: 300 DPI for optimal text recognition
- **Structured extraction**: Uses pdfplumber for better layout preservation

## Troubleshooting

### OCR Not Working

```bash
# Verify Tesseract installation
tesseract --version

# Install pdf2image for scanned PDF support
uv add pdf2image
```

### Missing Dependencies

```bash
# Reinstall all dependencies
uv install --reinstall
```

### Permission Errors

Ensure you have write permissions for the output directory:

```bash
mkdir -p ./output
chmod 755 ./output
```

## Development

### Project Structure

```text
pdf-parser/
├── pdf_requirements_parser.py  # Main script
├── pyproject.toml               # UV configuration
├── uv.lock                      # Locked dependencies
├── README.md                    # This file
└── .venv/                       # Virtual environment
```

### Adding Dependencies

```bash
uv add package-name
```

### Running Tests

```bash
# Test with a sample PDF
uv run python pdf_requirements_parser.py -i sample.pdf -o test_output
```

## Limitations

- OCR requires Tesseract to be installed separately
- Scanned PDF processing is slower than text-based PDFs
- Very complex PDF layouts may require manual review
- Encrypted PDFs require password handling (not currently supported)

## Future Enhancements

- [ ] Support for encrypted PDFs
- [ ] Word document export functionality
- [ ] Batch processing of multiple PDFs
- [ ] GUI interface
- [ ] Custom classification rules
- [ ] Annotation type filtering

## License

This project is provided as-is for parsing PDF requirements and annotations.

## Author

Created with UV for modern Python dependency management.
