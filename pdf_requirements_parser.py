#!/usr/bin/env python3
"""
PDF Requirements Parser Script

This script parses PDF documents and separates content into:
1. Main requirements text
2. User comments/annotations

Supports both text-based and scanned PDFs with OCR capabilities.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import warnings

# Core PDF libraries
import PyPDF2
import pdfplumber

# OCR libraries
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    warnings.warn("OCR libraries not available. Scanned PDFs cannot be processed.")


class PDFRequirementsParser:
    """
    Parser for extracting requirements and annotations from PDF documents.
    """

    def __init__(self, pdf_path: str):
        """
        Initialize the parser with a PDF file path.

        Args:
            pdf_path: Path to the PDF file to parse
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.requirements = {}
        self.comments = {}

    def parse(self) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
        """
        Parse the PDF and extract requirements and comments.

        Returns:
            Tuple of (requirements_dict, comments_dict)
        """
        print(f"Processing PDF: {self.pdf_path}")

        # Extract requirements (main text content)
        self._extract_requirements()

        # Extract annotations (PDF comments)
        self._extract_annotations()

        # Extract inline comments (Word-style comments in text)
        self._extract_inline_comments()

        return self.requirements, self.comments

    def _extract_requirements(self):
        """
        Extract main text content (requirements) from the PDF.
        Handles both text-based and scanned PDFs.
        """
        try:
            # First, try extracting with pdfplumber for better structure
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_key = f"page_{page_num}"

                    # Extract text from the page
                    text = page.extract_text()

                    if text and text.strip():
                        # Text-based page - parse the content
                        requirements = self._parse_text_content(text)
                        self.requirements[page_key] = requirements
                        print(f"✓ Extracted text from page {page_num}")
                    else:
                        # Possibly a scanned page - try OCR
                        if OCR_AVAILABLE:
                            ocr_text = self._perform_ocr(page_num)
                            if ocr_text:
                                requirements = self._parse_text_content(ocr_text)
                                self.requirements[page_key] = requirements
                                print(f"✓ OCR processed page {page_num}")
                            else:
                                self.requirements[page_key] = []
                                print(f"⚠ No content found on page {page_num}")
                        else:
                            self.requirements[page_key] = []
                            print(f"⚠ Scanned page {page_num} - OCR not available")

        except Exception as e:
            print(f"Error extracting requirements: {e}", file=sys.stderr)
            raise

    def _parse_text_content(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse text content into structured requirements.

        Args:
            text: Raw text content from the page

        Returns:
            List of requirement objects
        """
        requirements = []

        # Remove inline comments before processing requirements
        cleaned_text = self._remove_inline_comments(text)

        # Split text into logical sections
        # Try multiple splitting strategies
        sections = self._split_into_sections(cleaned_text)

        for idx, section in enumerate(sections, start=1):
            if not section.strip():
                continue

            # Determine if this is a heading or regular text
            req_type = self._classify_content(section)

            requirement = {
                "id": idx,
                "type": req_type,
                "text": section.strip(),
                "line_count": len(section.split('\n'))
            }
            requirements.append(requirement)

        return requirements

    def _split_into_sections(self, text: str) -> List[str]:
        """
        Split text into logical sections.

        Args:
            text: Text to split

        Returns:
            List of text sections
        """
        import re

        # Strategy 1: Split by double newlines
        sections = [s.strip() for s in text.split('\n\n') if s.strip()]

        # Strategy 2: If we have very few sections, try splitting by bullet points
        if len(sections) <= 2:
            bullet_pattern = r'(?=^•\s)'
            sections = [s.strip() for s in re.split(bullet_pattern, text, flags=re.MULTILINE) if s.strip()]

        # Strategy 3: If still too few, split by major headings
        if len(sections) <= 2:
            heading_pattern = r'(?=^[A-Z][^\n]{0,80}$)'
            sections = [s.strip() for s in re.split(heading_pattern, text, flags=re.MULTILINE) if s.strip()]

        return sections if sections else [text]

    def _remove_inline_comments(self, text: str) -> str:
        """
        Remove inline Word-style comments from text.

        Args:
            text: Text containing inline comments

        Returns:
            Text with comments removed
        """
        import re
        # Pattern for Word comments: Commented [xxx]: comment text (until end of line or next comment)
        # Remove the entire comment including the tag and text
        cleaned = re.sub(r'Commented \[[^\]]+\]:[^\n]+', '', text, flags=re.MULTILINE)
        # Remove any inline comment tags without the colon (edge cases)
        cleaned = re.sub(r'Commented \[[^\]]+\]', '', cleaned)
        # Clean up multiple consecutive blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def _classify_content(self, text: str) -> str:
        """
        Classify content type (heading, list item, paragraph, etc.).

        Args:
            text: Text content to classify

        Returns:
            Content type as string
        """
        lines = [l for l in text.split('\n') if l.strip()]
        if not lines:
            return "paragraph"

        first_line = lines[0].strip()

        # Check if it's a heading (short, uppercase, or ends with colon)
        if len(first_line) < 100 and (first_line.isupper() or first_line.endswith(':')):
            return "heading"

        # Check if it's a field list (like "Field Name Description Data Type")
        if any(keyword in first_line for keyword in ['Field Name', 'Field List', 'Description', 'Data Type']):
            return "field_list"

        # Check if it's a list item
        if first_line.startswith(('•', '-', '*', '◦', '▪')) or (
            len(first_line) > 0 and first_line[0].isdigit() and '.' in first_line[:5]
        ):
            return "list_item"

        # Check if it's a table-like structure
        if '\t' in text or text.count('|') > 3:
            return "table"

        return "paragraph"

    def _perform_ocr(self, page_num: int) -> str:
        """
        Perform OCR on a scanned page.

        Args:
            page_num: Page number to process (1-indexed)

        Returns:
            Extracted text from OCR
        """
        if not OCR_AVAILABLE:
            return ""

        try:
            # Convert PDF page to image
            from pdf2image import convert_from_path
            images = convert_from_path(
                self.pdf_path,
                first_page=page_num,
                last_page=page_num,
                dpi=300  # High resolution for better OCR
            )

            if images:
                # Perform OCR on the image
                text = pytesseract.image_to_string(images[0], lang='eng')
                return text.strip()

        except ImportError:
            print("⚠ pdf2image not available. Install with: uv add pdf2image", file=sys.stderr)
        except Exception as e:
            print(f"OCR error on page {page_num}: {e}", file=sys.stderr)

        return ""

    def _extract_annotations(self):
        """
        Extract all annotations (comments, highlights, notes) from the PDF.
        """
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num in range(len(pdf_reader.pages)):
                    page_key = f"page_{page_num + 1}"
                    page = pdf_reader.pages[page_num]

                    # Extract annotations from the page
                    annotations = self._get_page_annotations(page, page_num + 1)

                    if annotations:
                        self.comments[page_key] = annotations
                        print(f"✓ Extracted {len(annotations)} annotation(s) from page {page_num + 1}")
                    else:
                        self.comments[page_key] = []

        except Exception as e:
            print(f"Error extracting annotations: {e}", file=sys.stderr)
            # Don't raise - annotations are optional

    def _get_page_annotations(self, page: PyPDF2.PageObject, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract annotations from a specific page.

        Args:
            page: PyPDF2 page object
            page_num: Page number (1-indexed)

        Returns:
            List of annotation objects
        """
        annotations = []

        try:
            # Access the annotations array
            if '/Annots' in page:
                annots = page['/Annots']

                # Resolve indirect references
                if hasattr(annots, 'get_object'):
                    annots = annots.get_object()

                for idx, annot_ref in enumerate(annots, start=1):
                    try:
                        # Resolve the annotation object
                        annot = annot_ref.get_object() if hasattr(annot_ref, 'get_object') else annot_ref

                        # Extract annotation details
                        annotation = {
                            "id": idx,
                            "page": page_num,
                            "type": self._get_annotation_type(annot),
                            "author": self._get_annotation_author(annot),
                            "text": self._get_annotation_text(annot),
                            "subject": self._get_annotation_subject(annot),
                            "color": self._get_annotation_color(annot)
                        }

                        # Only include if there's actual content
                        if annotation["text"] or annotation["subject"]:
                            annotations.append(annotation)

                    except Exception as e:
                        print(f"Warning: Could not parse annotation {idx} on page {page_num}: {e}", file=sys.stderr)
                        continue

        except Exception as e:
            print(f"Warning: Could not access annotations on page {page_num}: {e}", file=sys.stderr)

        return annotations

    def _get_annotation_type(self, annot: Dict) -> str:
        """Extract annotation type."""
        if '/Subtype' in annot:
            subtype = str(annot['/Subtype'])
            return subtype.replace('/', '')
        return "Unknown"

    def _get_annotation_author(self, annot: Dict) -> str:
        """Extract annotation author."""
        if '/T' in annot:
            return str(annot['/T'])
        return "Unknown"

    def _get_annotation_text(self, annot: Dict) -> str:
        """Extract annotation content text."""
        if '/Contents' in annot:
            return str(annot['/Contents'])
        return ""

    def _get_annotation_subject(self, annot: Dict) -> str:
        """Extract annotation subject."""
        if '/Subj' in annot:
            return str(annot['/Subj'])
        return ""

    def _get_annotation_color(self, annot: Dict) -> str:
        """Extract annotation color."""
        if '/C' in annot:
            try:
                color = annot['/C']
                if isinstance(color, list) and len(color) == 3:
                    # RGB color
                    r, g, b = [int(c * 255) for c in color]
                    return f"#{r:02x}{g:02x}{b:02x}"
            except:
                pass
        return None

    def _extract_inline_comments(self):
        """
        Extract inline Word-style comments from the text content.
        These are comments embedded in the text like "Commented [AK1]: comment text"
        """
        import re

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_key = f"page_{page_num}"

                    # Get the raw text
                    text = page.extract_text()
                    if not text:
                        continue

                    # More precise pattern: capture only until the next line that starts with a requirement marker
                    # or another comment
                    lines = text.split('\n')
                    inline_comments = []

                    i = 0
                    while i < len(lines):
                        line = lines[i]

                        # Check if this line contains a comment start
                        comment_match = re.match(r'Commented \[([^\]]+)\]:\s*(.*)', line)

                        if comment_match:
                            author_tag = comment_match.group(1)
                            comment_text = comment_match.group(2).strip()

                            # Look ahead to capture multi-line comments
                            # but stop at requirement markers (bullets, field names, or next comment)
                            j = i + 1
                            while j < len(lines):
                                next_line = lines[j].strip()

                                # Stop conditions: next comment, bullet point, field name, or empty line followed by structure
                                if (next_line.startswith('Commented [') or
                                    next_line.startswith(('•', 'o ', '▪', 'Field Name', 'Name ', 'Is Active')) or
                                    (not next_line and j + 1 < len(lines) and lines[j+1].strip().startswith(('•', 'Field')))):
                                    break

                                # Add this line to comment if it's not empty and doesn't look like a requirement
                                if next_line and not next_line.startswith(('User Story', 'Campaign Details')):
                                    comment_text += ' ' + next_line
                                    j += 1
                                else:
                                    break

                            # Clean up the comment text
                            comment_text = ' '.join(comment_text.split())

                            # Skip if comment is too short or looks malformed
                            if len(comment_text) >= 10:
                                comment = {
                                    "id": len(inline_comments) + 1,
                                    "page": page_num,
                                    "type": "InlineComment",
                                    "author": author_tag,
                                    "text": comment_text,
                                    "subject": "Word Comment",
                                    "color": None
                                }
                                inline_comments.append(comment)

                            i = j
                        else:
                            i += 1

                    # Store comments
                    if page_key not in self.comments:
                        self.comments[page_key] = []

                    if inline_comments:
                        self.comments[page_key].extend(inline_comments)
                        print(f"✓ Extracted {len(inline_comments)} inline comment(s) from page {page_num}")

        except Exception as e:
            print(f"Error extracting inline comments: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

    def save_to_json(self, output_dir: str):
        """
        Save requirements and comments to separate JSON files.

        Args:
            output_dir: Directory to save the output files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save requirements
        requirements_file = output_path / "requirements.json"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            json.dump(self.requirements, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Requirements saved to: {requirements_file}")

        # Save comments
        comments_file = output_path / "comments.json"
        with open(comments_file, 'w', encoding='utf-8') as f:
            json.dump(self.comments, f, indent=2, ensure_ascii=False)
        print(f"✓ Comments saved to: {comments_file}")

        # Print summary
        total_requirements = sum(len(reqs) for reqs in self.requirements.values())
        total_comments = sum(len(cmts) for cmts in self.comments.values())
        print(f"\n📊 Summary:")
        print(f"   Total pages: {len(self.requirements)}")
        print(f"   Total requirements: {total_requirements}")
        print(f"   Total comments: {total_comments}")

    def save_to_markdown(self, output_dir: str):
        """
        Save requirements and comments to a formatted Markdown file.

        Args:
            output_dir: Directory to save the output file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        markdown_file = output_path / "parsed_document.md"

        with open(markdown_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# PDF Requirements Document\n\n")
            f.write(f"**Source:** {self.pdf_path.name}\n\n")
            f.write(f"**Total Pages:** {len(self.requirements)}\n\n")
            f.write("---\n\n")

            # Write requirements by page
            f.write("## Requirements\n\n")

            for page_key in sorted(self.requirements.keys(), key=lambda x: int(x.split('_')[1])):
                page_num = page_key.split('_')[1]
                reqs = self.requirements[page_key]

                if not reqs:
                    continue

                f.write(f"### Page {page_num}\n\n")

                for req in reqs:
                    req_type = req['type'].replace('_', ' ').title()
                    f.write(f"**[{req_type} {req['id']}]**\n\n")

                    # Format text based on type
                    text = req['text']

                    if req['type'] == 'list_item':
                        # Ensure list items are properly formatted
                        lines = text.split('\n')
                        for line in lines:
                            if line.strip():
                                if not line.strip().startswith(('•', '-', '*', 'o ')):
                                    f.write(f"- {line.strip()}\n")
                                else:
                                    f.write(f"{line.strip()}\n")
                    elif req['type'] == 'heading':
                        f.write(f"**{text}**\n")
                    elif req['type'] == 'table' or req['type'] == 'field_list':
                        # Keep table formatting as code block
                        f.write(f"```text\n{text}\n```\n")
                    else:
                        # Regular paragraph
                        f.write(f"{text}\n")

                    f.write("\n")

                f.write("---\n\n")

            # Write comments by page
            total_comments = sum(len(cmts) for cmts in self.comments.values())
            if total_comments > 0:
                f.write("## Comments & Annotations\n\n")

                for page_key in sorted(self.comments.keys(), key=lambda x: int(x.split('_')[1])):
                    page_num = page_key.split('_')[1]
                    comments = self.comments[page_key]

                    if not comments:
                        continue

                    f.write(f"### Page {page_num} Comments\n\n")

                    for comment in comments:
                        f.write(f"**[{comment['author']}]** ({comment['type']})\n\n")
                        f.write(f"> {comment['text']}\n\n")

                    f.write("---\n\n")

        print(f"✓ Markdown saved to: {markdown_file}")


def main():
    """
    Main entry point for the PDF requirements parser.
    """
    parser = argparse.ArgumentParser(
        description='Parse PDF documents and separate requirements from comments/annotations.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input document.pdf --output-dir ./output
  %(prog)s -i requirements.pdf -o ./parsed_data

Notes:
  - Tesseract OCR must be installed for scanned PDF support
  - Output generates: requirements.json, comments.json, and parsed_document.md
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to the input PDF file'
    )

    parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Directory to save output JSON files'
    )

    args = parser.parse_args()

    try:
        # Initialize and run the parser
        pdf_parser = PDFRequirementsParser(args.input)
        requirements, comments = pdf_parser.parse()

        # Save results
        pdf_parser.save_to_json(args.output_dir)
        pdf_parser.save_to_markdown(args.output_dir)

        print("\n✅ Processing complete!")
        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
