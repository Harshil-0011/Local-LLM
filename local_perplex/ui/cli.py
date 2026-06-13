import click
import sys
from pathlib import Path

# Robust path setup: try to import local_perplex, and if it fails, add paths
try:
    import local_perplex
except ImportError:
    # Try adding known paths to sys.path
    import site
    for site_dir in site.getsitepackages():
        if Path(site_dir).exists():
            sys.path.insert(0, site_dir)
    # Also try the directory where this script is
    script_dir = Path(__file__).parent.parent.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

from local_perplex.engine import LocalPerplex

@click.command()
@click.argument('question')
@click.option('--mode', type=click.Choice(['industry_standard', 'all_references']), default='industry_standard')
def main(question, mode):
    lp = LocalPerplex()
    click.echo(f"Searching and analyzing...")
    question, sources, context = lp.research_step(question, mode=mode)
    answer = lp.ask(question, context, mode=mode)

    click.echo("\n--- Answer ---")
    click.echo(answer)
    click.echo("\n--- Sources ---")
    for s in sources:
        click.echo(f"- {s.title} ({s.url}) [Relevance: {s.relevance:.4f}]")

if __name__ == "__main__":
    main()
