"""
main.py
-------
CLI entry point for the Document Data Extractor Agent.

Usage:
    python main.py --file samples/invoice_1.txt
    python main.py --file samples/receipt_1.pdf
    python main.py --demo   (runs all sample files)
"""

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from extractor import extract_document, save_result

console = Console()

SAMPLES_DIR = Path("samples")
OUTPUTS_DIR = Path("samples/outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def process_file(file_path: str):
    """Process a single file and display results."""
    console.rule(f"[bold blue]Processing: {file_path}")

    try:
        # Run the agent
        result = extract_document(file_path)

        # Display key results in a nice table
        console.print("\n[bold green]✅ Extraction Complete!\n")

        # Summary panel
        summary = (
            f"[bold]Document Type:[/bold] {result.document_type}\n"
            f"[bold]Document ID:[/bold]   {result.document_id or 'N/A'}\n"
            f"[bold]Date:[/bold]          {result.date or 'N/A'}\n"
            f"[bold]Vendor:[/bold]        {result.vendor.name if result.vendor else 'N/A'}\n"
            f"[bold]Buyer:[/bold]         {result.buyer.name if result.buyer else 'N/A'}\n"
            f"[bold]Currency:[/bold]      {result.currency}\n"
            f"[bold]Subtotal:[/bold]      {result.subtotal}\n"
            f"[bold]Tax:[/bold]           {result.tax}\n"
            f"[bold]Total:[/bold]         {result.total}\n"
            f"[bold]Payment Method:[/bold]{result.payment_method or 'N/A'}"
        )
        console.print(Panel(summary, title="[bold]Document Summary", border_style="blue"))

        # Line items table
        if result.line_items:
            table = Table(title="Line Items", border_style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Qty", justify="right")
            table.add_column("Unit Price", justify="right")
            table.add_column("Total", justify="right", style="green")

            for item in result.line_items:
                table.add_row(
                    item.description,
                    str(item.quantity) if item.quantity is not None else "-",
                    str(item.unit_price) if item.unit_price is not None else "-",
                    str(item.total) if item.total is not None else "-",
                )
            console.print(table)

        # Validation warnings
        if result.validation_warnings:
            console.print("\n[bold yellow]⚠ Validation Warnings:")
            for w in result.validation_warnings:
                console.print(f"  {w}")
        else:
            console.print("\n[bold green]✅ All sanity checks passed!")

        # Save output JSON
        output_file = OUTPUTS_DIR / (Path(file_path).stem + "_extracted.json")
        save_result(result, str(output_file))

        return result

    except FileNotFoundError as e:
        console.print(f"[bold red]❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]❌ Extraction error: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected error: {e}")
        raise


def run_demo():
    """Run the agent on all sample files."""
    sample_files = list(SAMPLES_DIR.glob("*.txt")) + list(SAMPLES_DIR.glob("*.pdf"))

    if not sample_files:
        console.print("[bold yellow]⚠ No sample files found in samples/ directory.")
        console.print("Add .txt or .pdf files to samples/ and try again.")
        return

    console.print(f"\n[bold blue]Running demo on {len(sample_files)} sample file(s)...\n")

    for file_path in sample_files:
        process_file(str(file_path))
        console.print("\n")


def main():
    parser = argparse.ArgumentParser(
        description="📄 Document Data Extractor Agent — Extracts structured JSON from invoices, receipts & POs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --file samples/invoice_1.txt
  python main.py --file samples/receipt_1.txt
  python main.py --demo
        """
    )

    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a document file (PDF or TXT)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the agent on all files in the samples/ directory"
    )

    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold blue]📄 Document Data Extractor Agent[/bold blue]\n"
        "[dim]Powered by Groq (llama3-70b) + Pydantic validation[/dim]",
        border_style="blue"
    ))

    if args.demo:
        run_demo()
    elif args.file:
        process_file(args.file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()