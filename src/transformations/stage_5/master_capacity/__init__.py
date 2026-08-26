"""
master_capacity
===============
Master capacity assembly -- folds each transport type into the unified master
capacity model, then emits the three FINAL tables.

LAYOUT
------
    awards/ firms/ index/ interruptibles/   per-type assembly (inputs)
    final/core/                             -> final_core_master_capacity
    final/locations/                        -> final_locations_master_capacity
    final/rates/                            -> final_rates_master_capacity

Per-type folders hold the work of getting each feed into the common shape;
`final/` holds the transformations that emit the unified output tables. The
split mirrors the FINAL section of the pipeline dashboard.

WHAT EXISTS TODAY
-----------------
EMPTY OF CODE: every folder here is scaffolding with an empty logic.txt.

Only ONE of the three final tables exists in the database:

    public.final_core_master_capacity     27 columns, 20 rows
    final_locations_master_capacity       does not exist
    final_rates_master_capacity           does not exist

So `final_core_master_capacity` is the one concrete target to build toward; its
columns are the shape to match:

    NGHContractID, PipelineDuns, PipelineName, ContractNumber, AwardNumber,
    OfferNumber, BidNumber, ReleaserContractNumber, PostedDate, BeginDate,
    EndDate, ContractQuantity, RateSchedule, ContractHolder, ContractHolderDuns,
    ReleaserName, ReleaserDuns, Evergreen, NoticePeriodDays, CalculatedEndDate,
    ReplacementShipperRoleIndicator, TermNotes, ContractType, CreatedDate,
    UpdateDate, Source

Two things worth settling before writing any of this:

  * It lives in `public`, not in the Silver schema, and uses PascalCase column
    names -- unlike everything else this repo writes. Decide whether these
    transformations target `public.final_*` as-is or a Silver-schema equivalent.
  * Evergreen / NoticePeriodDays / CalculatedEndDate / TermNotes are term
    fields, so the term transform hook in ../../stage_4/rec_del_pairing/pairing_base.py
    most likely feeds this table. Settle that before implementing either.

TO ADD ONE
----------
Drop a module in the relevant folder with a @register-ed PipelineTransformation
subclass. The parent package discovers subfolders recursively, so no imports are
needed here. See ../../stage_4/rec_del_pairing/ for a multi-type component sharing one base
class, or ../../silver_firm_transport_rate.py for a standalone one.

See logic.txt in each folder for the business rules.
"""
