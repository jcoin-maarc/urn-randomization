"""CLI for urn-randomization package"""

import sys
import click
from confuse import exceptions as ce

from urand.config import config
from urand import Study


@click.group()
@click.pass_context
@click.option("-s", "--study-name", required=True, help="Name of study")
def cli(ctx, study_name):
    """Perform urn randomization as described by Wei (1978)"""

    try:
        factors = config[study_name]["factors"].get()
    except ce.NotFoundError:
        raise click.UsageError(
            'Participant factors for study "{}" not found'.format(study_name)
        )

    ctx.ensure_object(dict)
    ctx.obj["study_name"] = study_name
    ctx.obj["factors"] = factors


def get_factor_val(levels, prompt):
    while True:
        val = str(input(prompt))
        if val in levels:
            return val


# TODO Allow factor levels to be specified as options
@cli.command()
@click.pass_context
@click.option("--id", prompt="Participant ID", help="Participant ID")
@click.option("-u", "--user", prompt="Username", help="Username")
def randomize(ctx, id, user):
    """Randomize new participant"""

    factor_vals = {}
    for factor in ctx.obj["factors"]:
        levels = [str(s) for s in ctx.obj["factors"][factor]]
        prompt = "{} ({}): ".format(factor.capitalize(), ", ".join(levels))
        factor_vals["f_{}".format(factor)] = get_factor_val(levels, prompt)
    study = Study(ctx.obj["study_name"])
    participant = study.participant(id=id, user=user, **factor_vals)
    trt = study.randomize(participant).trt
    print("\nTreatment assigned: {}".format(trt))


@cli.command()
@click.pass_context
@click.argument("outfile", type=click.Path(exists=False))
def export(ctx, outfile):
    """Export study history to OUTFILE"""
    study = Study(ctx.obj["study_name"])
    study.export_history(outfile)


@cli.command()
@click.pass_context
@click.argument("infile", type=click.Path(exists=False))
def upload_participants(ctx, infile):
    """Export study history to OUTFILE"""
    study = Study(ctx.obj["study_name"])
    study.upload_existing_history(file=infile)


@cli.command()
@click.pass_context
@click.option(
    "--n_participants",
    type=int,
    required=True,
    prompt="No. of participants",
    help="Study size",
)
@click.option(
    "--seed",
    type=int,
    required=True,
    prompt="Random number generator seed",
    help="Seed",
)
def dummy_study(ctx, n_participants, seed):
    """Populate a study with dummy data"""
    study = Study(ctx.obj["study_name"], memory=False)
    study.generate_dummy_participants(n_participants, seed)


if __name__ == "__main__":
    cli(obj={})
