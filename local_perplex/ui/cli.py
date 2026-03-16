import click
from local_perplex.engine import LocalPerplex

@click.command()
@click.argument('question')
@click.option('--mode', type=click.Choice(['industry_standard', 'all_references']), default='industry_standard')
def main(question, mode):
    lp = LocalPerplex()
    click.echo(f"Searching and analyzing...")
    answer, sources, related = lp.ask(question, mode=mode)

    click.echo("\n--- Answer ---")
    click.echo(answer)
    click.echo("\n--- Sources ---")
    for s in sources:
        click.echo(f"- {s['title']} ({s['url']}) [Relevance: {s['relevance']:.4f}]")

if __name__ == "__main__":
    main()
