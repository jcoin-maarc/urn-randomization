"""Urn randomization for group assignment in randomized experiments"""

from urand import db
from urand import config
import json
import random
from numpy.random import Generator, PCG64
from itertools import product
from datetime import datetime, timezone
import ast
import pandas as pd
import scipy.stats as stats
import sys

plugins = config.plugins


class Study:
    """Study for which treatments are to be assigned"""

    def __init__(self, study_name, memory=False):

        self.study_name = study_name
        config, self.participant, self.session = db.get_tables(study_name, memory)

        # TODO Allow w, alpha and beta to be sequence of integers
        self.w = int(db.get_param(config, self.session, "w"))
        self.alpha = int(db.get_param(config, self.session, "alpha"))
        self.beta = int(db.get_param(config, self.session, "beta"))
        starting_seed = db.get_param(config, self.session, "starting_seed")
        self.starting_seed = int(starting_seed) if starting_seed else None
        self.D = db.get_param(config, self.session, "D")
        self.urn_selection = db.get_param(config, self.session, "urn_selection")
        self.treatments = json.loads(db.get_param(config, self.session, "treatments"))
        self.factors = json.loads(db.get_param(config, self.session, "factors"))

    def get_bg_state(self):
        """Returns last state of NumPy BitGenerator

        This is equal to the state after the last assignment, or the state
        after initialization with the study's random number seed before any
        assignments have been made.
        """
        last_state = db.get_last_state(self.participant, self.session)
        if not last_state:
            bg = PCG64(self.starting_seed)
            return bg.state
        else:
            return last_state.bg_state

    def generate_dummy_participants(self, n_participants, seed):
        """Adds dummy participants to study database for using in development mode"""
        rng = Generator(PCG64(seed))
        lst_factorlevels = [
            self.factors[factor] for factor in sorted(self.factors.keys())
        ]
        lst_factor_combos = list(set(product(*lst_factorlevels)))
        lstdct_participants = [
            dict(
                [
                    (factor, tpl_participant[factor_index])
                    for factor_index, factor in enumerate(lst_factor)
                ]
                + [
                    ("user", "dummy"),
                    # ('datetime', datetime.now(timezone.utc)),
                    # ('seed', pickle.dumps(np.random.RandomState()))
                ]
            )
            for lst_factor, tpl_participant in product(
                [["f_" + factor for factor in sorted(self.factors.keys())] + ["id"]],
                [
                    tpl + (idx,)
                    for idx, tpl in enumerate(
                        [
                            lst_factor_combos[i]
                            for i in rng.choice(
                                len(lst_factor_combos), n_participants, replace=True
                            )
                        ]
                    )
                ],
            )
        ]
        self.upload_new_participants(pdf=pd.DataFrame(lstdct_participants))
        return

    def print_config(self):
        attrs = [
            "study_name",
            "w",
            "alpha",
            "beta",
            "starting_seed",
            "D",
            "urn_selection",
            "treatments",
            "factors",
        ]
        for attr in attrs:
            print("{}: {}".format(attr, getattr(self, attr)))

    def _get_assignments(self, fdict):
        """Assignments for those matching each factor, in urn format"""

        # Start with empty data frame with all treatment columns in order
        idx = pd.MultiIndex.from_tuples([], names=["factor", "factor_level"])
        dfs = [pd.DataFrame(columns=["trt_" + t for t in self.treatments], index=idx)]

        df = db.get_participants(self.participant, self.session, **fdict)
        for factor in self.factors.keys():
            for factor_level in (
                [fdict["f_" + factor]] if bool(fdict) else self.factors[factor]
            ):
                subset = df.loc[
                    df["f_" + factor] == factor_level, ["f_" + factor, "trt"]
                ]
                if not subset.empty:
                    subset.rename(columns={"f_" + factor: "factor_level"}, inplace=True)
                    subset["factor"] = factor
                    subset["trt"] = "trt_" + subset.trt
                    dfs.append(
                        subset.value_counts(["factor", "factor_level", "trt"])
                        .to_frame()
                        .unstack(level=-1, fill_value=0)
                        .droplevel(level=0, axis=1)
                    )
                else:
                    idx = pd.MultiIndex.from_tuples(
                        [(factor, factor_level)], names=["factor", "factor_level"]
                    )
                    dfs.append(
                        pd.DataFrame(
                            {"trt_{}".format(t): 0 for t in self.treatments}, index=idx
                        )
                    )

        return pd.concat(dfs).fillna(0).astype(int).reset_index()

    def compute_no_balls(self, urns):
        """Add no_balls columns"""

        # TODO Modify calculation to accommodate vector-valued w, alpha and beta
        trt_cols = ["trt_" + t for t in self.treatments]
        for col in trt_cols:
            urns["balls_" + col] = (
                self.w
                + (self.alpha * urns[col])
                + (self.beta * (urns[trt_cols].sum(axis=1) - urns[col]))
            )

        ball_cols = ["balls_" + c for c in trt_cols]
        urns["total_balls"] = urns[ball_cols].sum(axis=1)
        return urns

    def compute_d(self, urns):
        """ "Compute D for urns"""
        ball_cols = ["balls_trt_" + trt for trt in self.treatments]
        if self.D == "range":
            urns = urns.assign(
                d=(urns[ball_cols].max(axis=1) - urns[ball_cols].min(axis=1)).div(
                    urns["total_balls"]
                )
            )
        elif self.D == "variance":
            urns = urns.assign(
                d=(urns[ball_cols].div(urns["total_balls"], axis=0).var(axis=1))
            )
        else:
            trt_cols = ["trt_" + t for t in self.treatments]
            # urns['total_asgmt'] = urns[trt_cols].sum(axis=1)
            # urns = urns.assign(d=urns['total_asgmt'].where(urns['total_asgmt'] == 0,
            #                                                stats.chisquare(urns[trt_cols], axis=1)[0]))
            # del urns['total_asgmt']
            urns = urns.assign(
                d=stats.chisquare(
                    urns[ball_cols].div(urns["total_balls"], axis=0), axis=1
                )[0]
            )
        return urns

    def get_urns(self, participant):
        """Returns list of urns associsated with the participant,
        constructed from their assignment history"""

        fdict = {
            col: getattr(participant, col)
            for col in participant.__table__.columns.keys()
            if col.startswith("f_")
        }
        urns = self._get_assignments(fdict)
        urns = self.compute_no_balls(urns)
        urns = self.compute_d(urns)
        return urns

    def get_study_urns(self):
        """Get all possible urns related to study
        Build list of urns from assignment history.
        """
        pdf_urns = self._get_assignments({})
        pdf_urns = self.compute_no_balls(pdf_urns)
        pdf_urns = self.compute_d(pdf_urns)
        return pdf_urns

    def export_history(self, file=None):
        """Exports patient assignment history table as a csv file"""
        pdf = db.get_participants(self.participant, self.session)
        if file is not None:
            pdf.to_csv(file, index=False)
        else:
            return pdf

    def upload_existing_history(self, **kwargs):
        """Load existing history from study that has already started recruiting"""
        assert ("file" in kwargs) | ("pdf" in kwargs), (
            "Neither filename nor dataframe with assignment " "info provided as input"
        )
        pdf_asgmt = (
            kwargs["pdf"]
            if ("pdf" in kwargs)
            else pd.read_csv(
                kwargs["file"], dtype=object, encoding="utf8"
            )
        )
        assert all(
            [
                a == b
                for a, b in zip(
                    sorted([col for col in pdf_asgmt.columns if col != "bg_state"]),
                    sorted(
                        ["id", "user", "trt", "datetime"]
                        + ["f_" + factor for factor in self.factors]
                    ),
                )
            ]
        ), "Input file does not match study schema"
        pdf_asgmt = pdf_asgmt.assign(
            datetime=pd.to_datetime(pdf_asgmt["datetime"], utc=True)
        )
        if "bg_state" in pdf_asgmt.columns:
            pdf_asgmt = pdf_asgmt.assign(
                bg_state=pdf_asgmt["bg_state"].apply(ast.literal_eval)
            )
            db.add_participants(
                self.participant,
                pdf_asgmt.to_dict("records"),
                self.session,
            )
        else:
            lstdct_participants = pdf_asgmt.to_dict("records")
            db.add_participants(
                self.participant,
                lstdct_participants[: (pdf_asgmt.shape[0] - 1)],
                self.session,
            )
            dct_participant = lstdct_participants[pdf_asgmt.shape[0] - 1]
            dct_participant["bg_state"] = self.get_bg_state()
            db.add_participants(
                self.participant,
                [dct_participant],
                self.session,
            )
        return

    # TODO: get study status - multiple studies, npatients, print urn assignments
    def upload_new_participants(self, **dct_participants):

        assert ("file" in dct_participants) | (
            "pdf" in dct_participants
        ), "Neither filename nor dataframe eith patient info provided as input"
        pdf_asgmt = (
            dct_participants["pdf"]
            if ("pdf" in dct_participants)
            else pd.read_csv(dct_participants["file"], dtype=object, encoding="utf8")
        )
        assert all(
            [
                a == b
                for a, b in zip(
                    sorted(pdf_asgmt.columns),
                    sorted(
                        [
                            "id",
                            "user",
                        ]
                        + ["f_" + factor for factor in self.factors]
                    ),
                )
            ]
        ), "Input file does not match study schema"

        lstdct_participants = pdf_asgmt.to_dict("records")
        for dct in lstdct_participants:
            dct_participant = dict(dct)
            dct_participant["datetime"] = datetime.now(timezone.utc)
            self.randomize(self.participant(**dct_participant))
        return

    def get_participant(self, id):
        df_participant = db.get_participants(
            self.participant, self.session, **{"id": id}
        )
        return df_participant

    def get_config(self):
        study_config = db.config[self.study_name].get()
        study_config["w"] = self.w
        study_config["alpha"] = self.alpha
        study_config["beta"] = self.beta
        study_config["D"] = self.D
        study_config["urn_selection"] = self.urn_selection
        study_config["starting_seed"] = self.starting_seed
        return study_config

    def randomize(self, participant):
        """Randomize new participant

        1. Calculate d (level of imbalance) for all urns matching participant's
           characteristics
        2. Pick the urn with the least imbalance (ties are broken with random
           selection) with probability p_l as per urn_selection method
        3. Randomly pick one of the treatment balls, k_i, in the selected urn
        4. Participant assigned to the treatment type represented by the ball
        """

        # Initialize RNG
        bg = PCG64()
        bg.state = self.get_bg_state()
        rng = Generator(bg)

        urns = self.get_urns(participant)

        # Select urn with greatest imbalance
        # Start by getting urns with maximum imbalance and sorting them by
        # factor columns
        ball_cols = ["balls_trt_" + trt for trt in self.treatments]
        candidate_urns = (
            urns.loc[urns["d"] == urns["d"].max()]
            .sort_values(by=["factor"], ascending=True)
            .reset_index(drop=True)
        )
        selected_urn = candidate_urns.iloc[
            rng.choice(candidate_urns.index.tolist(), 1).tolist()
        ]

        trt = rng.choice(
            ball_cols,
            1,
            p=selected_urn[ball_cols]
            .div(selected_urn["total_balls"].values, axis=0)
            .values.flatten()
            .tolist(),
        )[0]
        participant.trt = trt.lstrip("balls_trt_")

        for plugin_name in plugins.list_plugins():
            plugin = plugins.load_plugin(plugin_name)
            participant = plugin.randomize(self, participant)
        participant.datetime = datetime.now(timezone.utc)
        participant.bg_state = bg.state
        db.add_participant(participant, self.session)

        return participant
