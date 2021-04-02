Overview
========

Description
-----------

Randomization schemes in clinical trials strive to keep assignment of patients to treatment groups free of any deliberate
bias so that basis for causal inference can be established. Minimizing bias and maximizing precision of treatment
effect estimates are the two principles underpinning the design and execution of these randomization schemes. Urn
randomization as described by Wei (1978) is a widely used randomization scheme that helps overcome bias related to
unequal distribution of prognostic factors between groups. In comparison with block randomization schemes, this method is
less deterministic and is less susceptible to investigator bias due to concealed allotment. It also handles large number
of factors better than stratified randomization schemes. This scheme can also be used in trials that are already midway
in their recruitment stage to improve factor balance. While other dynamic randomization schemes such as minimization offer
more balance, this comes at the cost of being more predictable. Urn randomization schemes also have a tendency to behave
like simple randomization as the trial size increases, where imbalances that affect power in estimating treatment effects
are less likely. Urn randomization can thus be used for trials with large number of factors that require subgroup analysis,
and also to increase precision in interim analyses by ensuring balance.

Authentication
--------------

Authentication to the browser interface is handled via OAuth 2.0 using Google. Users will log in via their Google accounts.
You will need to provide your Gmail address to the person administering the app so that he or she can register you as an
authorized user.

Authentication when using the API is handled via an API key that will be
provided to you. It is critical that you store and use this key in a secure
manner.

Usage
-----

When you first login, you will be redirected to `Participants` page which displays information related to factor levels
of participants already recruited and assigned. This page has bar plots in the top half of the page, visualizing percentages
of participants assigned to each treatment group and at different factors/ factor levels (:numref:`fig-assgmt-plot`).

.. _fig-assgmt-plot:
.. figure:: figures/assgmt_plot.png
   :scale: 33%
   :align: center

   Treatment assignments plots

This page also displays factor information of all participants assigned in a tabular format (:numref:`fig-assgmt-tbl`)
in the bottom half of the page. This table has search and sort functionalities and it's contents can also be downloaded
as an excel file using the button with `Excel` icon above the table.

.. _fig-assgmt-tbl:
.. figure:: figures/assgmt_tbl.png
   :scale: 33%
   :align: center

   Treatment assignments table

Randomizing a new participant
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To randomize a new participant, click `Randomize Participant` button at the top of the page. This will redirect you to a
form (:numref:`fig-randomize-frm`) where you can input factor information related to the new participant along with their ID. Click `Submit` after
adding all factor details. This will randomize this participant if they do not exist already. Assignment treatment
information will be displayed in the next page in the form of a flash message.

.. _fig-randomize-frm:
.. figure:: figures/randomize_frm.png
   :scale: 33%
   :align: center

   Randomize new participant