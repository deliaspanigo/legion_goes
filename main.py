import click

@click.group()
def cli():
    """CLI for the GOES image processor - MAIE Thesis 2026"""
    pass

@cli.command()
def test():
    """Test command"""
    click.echo("Legion GOES esta operativo!")

if __name__ == "__main__":
    cli()
