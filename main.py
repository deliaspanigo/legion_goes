import click

@click.group()
def cli():
    """CLI para el procesador de imágenes GOES - MAIE Thesis 2026"""
    pass

@cli.command()
def test():
    """Comando de prueba"""
    click.echo("¡Legion GOES está operativo!")

if __name__ == "__main__":
    cli()
