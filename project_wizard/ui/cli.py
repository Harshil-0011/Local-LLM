import click
import os
import sys
from pathlib import Path
from ..config import get_config
from ..interview.manager import InterviewManager
from ..spec.builder import SpecBuilder
from ..codegen.generator import CodeGenerator

@click.group()
@click.option('--config', type=click.Path(), help='Custom config file path.')
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj['config'] = get_config(config)

@cli.command()
@click.option('--output', type=click.Path(), help='Output directory for the project.')
@click.pass_context
def interview(ctx, output):
    """Run interactive interview in the terminal."""
    config = ctx.obj['config']
    output_dir = Path(output or config.default_output_dir)
    manager = InterviewManager(output_dir)

    click.echo(f"Starting interview. Answers will be saved to {manager.answers_file}")

    for q in manager.get_questions():
        existing = manager.answers.get(q['id'])
        prompt = f"{q['text']}"
        if existing:
            prompt += f" [{existing}]"
        elif q['default']:
            prompt += f" [{q['default']}]"

        answer = click.prompt(prompt, default=existing or q['default'], show_default=False)
        manager.update_answer(q['id'], answer)

    click.echo("Interview complete.")

@cli.command()
@click.option('--output', type=click.Path(), help='Output directory for the project.')
@click.option('--model', help='Override planner model.')
@click.pass_context
def build_spec(ctx, output, model):
    """Read answers.json and generate project_spec.md."""
    config = ctx.obj['config']
    output_dir = Path(output or config.default_output_dir)
    manager = InterviewManager(output_dir)

    if not manager.answers_file.exists():
        click.echo("Error: answers.json not found. Run 'wizard interview' first.")
        sys.exit(1)

    builder = SpecBuilder(config.ollama_base_url, model or config.planner_model)
    click.echo(f"Generating spec using {builder.model}...")
    spec_content = builder.build_spec(manager.answers)
    spec_file = builder.save_spec(output_dir, spec_content)
    click.echo(f"Spec saved to {spec_file}")

@cli.command()
@click.option('--output', type=click.Path(), help='Output directory for the project.')
@click.option('--model', help='Override coder model.')
@click.option('--dry-run', is_flag=True, help='Show what would be done without writing files.')
@click.pass_context
def generate_code(ctx, output, model, dry_run):
    """Read project_spec.md and generate project files."""
    config = ctx.obj['config']
    output_dir = Path(output or config.default_output_dir)
    spec_file = output_dir / "project_spec.md"

    if not spec_file.exists():
        click.echo("Error: project_spec.md not found. Run 'wizard build-spec' first.")
        sys.exit(1)

    with open(spec_file, "r", encoding="utf-8") as f:
        spec_content = f.read()

    generator = CodeGenerator(config.ollama_base_url, model or config.coder_model)
    click.echo(f"Generating code using {generator.model}...")
    llm_output = generator.generate_code(spec_content)
    generator.parse_and_save(output_dir, llm_output, dry_run=dry_run)
    click.echo("Code generation complete.")

@cli.command()
@click.option('--output', type=click.Path(), help='Output directory for the project.')
@click.option('--dry-run', is_flag=True, help='Show what would be done without writing files.')
@click.pass_context
def full_run(ctx, output, dry_run):
    """Run interview, build-spec, and generate-code in sequence."""
    ctx.invoke(interview, output=output)
    if click.confirm("Proceed to build specification?"):
        ctx.invoke(build_spec, output=output)
        if click.confirm("Proceed to generate code?"):
            ctx.invoke(generate_code, output=output)

def main():
    cli(obj={})

if __name__ == '__main__':
    main()
