#!/usr/bin/env python3
"""
Example usage of the PDF Requirements Parser
"""

import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_requirements_parser import PDFRequirementsParser


def example_usage():
    """
    Demonstrate how to use the PDF parser programmatically.
    """

    # Example 1: Basic usage
    print("=" * 60)
    print("Example 1: Basic PDF Parsing")
    print("=" * 60)

    try:
        parser = PDFRequirementsParser("sample.pdf")
        requirements, comments = parser.parse()
        parser.save_to_json("./example_output")
        parser.save_to_markdown("./example_output")

        print("\n✓ Successfully parsed PDF")
        print(f"   Pages processed: {len(requirements)}")
        print(f"   Total requirements: {sum(len(r) for r in requirements.values())}")
        print(f"   Total comments: {sum(len(c) for c in comments.values())}")
        print(f"   Output: JSON files + Markdown document")

    except FileNotFoundError:
        print("ℹ  Note: Place a 'sample.pdf' in the current directory to run this example")
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Access parsed data programmatically
    print("\n" + "=" * 60)
    print("Example 2: Accessing Parsed Data")
    print("=" * 60)

    # You can work with the returned dictionaries directly
    sample_requirements = {
        "page_1": [
            {
                "id": 1,
                "type": "heading",
                "text": "FUNCTIONAL REQUIREMENTS",
                "line_count": 1
            },
            {
                "id": 2,
                "type": "paragraph",
                "text": "The system shall provide secure user authentication.",
                "line_count": 1
            }
        ]
    }

    sample_comments = {
        "page_1": [
            {
                "id": 1,
                "page": 1,
                "type": "Highlight",
                "author": "Reviewer",
                "text": "Need to define authentication method",
                "subject": "Question",
                "color": "#ffff00"
            }
        ]
    }

    print("\nSample Requirements Structure:")
    print(f"  Pages: {list(sample_requirements.keys())}")
    print(f"  First requirement: {sample_requirements['page_1'][0]['text']}")

    print("\nSample Comments Structure:")
    print(f"  Pages: {list(sample_comments.keys())}")
    print(f"  First comment: {sample_comments['page_1'][0]['text']}")

    # Example 3: Filtering and processing
    print("\n" + "=" * 60)
    print("Example 3: Filtering Requirements by Type")
    print("=" * 60)

    # Filter headings
    headings = [
        req for page_reqs in sample_requirements.values()
        for req in page_reqs
        if req['type'] == 'heading'
    ]
    print(f"\nFound {len(headings)} heading(s):")
    for heading in headings:
        print(f"  - {heading['text']}")

    # Filter comments by author
    print("\nFiltering comments by author:")
    author_filter = "Reviewer"
    filtered_comments = [
        comment for page_comments in sample_comments.values()
        for comment in page_comments
        if comment['author'] == author_filter
    ]
    print(f"Found {len(filtered_comments)} comment(s) from '{author_filter}'")


if __name__ == "__main__":
    example_usage()
