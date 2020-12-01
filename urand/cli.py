"""CLI for urn-randomization package"""

import click
from urand.config import config

@click.group()
def cli():
    pass

@cli.command()
def randomize():
    click.echo('Ready to randomize!')
