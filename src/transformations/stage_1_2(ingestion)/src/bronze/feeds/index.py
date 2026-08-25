"""
index.py
========
Index of Customers -> bronze.gindex.

One flat row per index record: no nested arrays, hence no `nested_sections`.

DORMANT DOWNSTREAM. This feed ingests to Bronze correctly, but NO stage 3, 4 or
5 transformation is registered for it -- `run.py --list --source ioc` returns
nothing. Rows land in bronze.gindex and go no further until those are written.
"""

from __future__ import annotations

from .spec import FeedDefinition

FEED = FeedDefinition(
    feed_type="gINDEX",
    table="gindex",
    records_keys=("records", "Records", "IndexOfCustomers"),
    parent_id_field="ID",
    parent_required=("ID", "Pipe"),
    header_keys=(),
    nested_sections=(),
    columns=[
        ("ID", "int"),
        ("FercID", "varchar"),
        ("Pipe", "varchar"),
        ("ReportDate", "datetime"),
        ("OrigRevised", "int"),
        ("TporUOM", "varchar"),
        ("StorUOM", "varchar"),
        ("Contact", "varchar"),
        ("ContactNumber", "varchar"),
        ("Shipper", "varchar"),
        ("ShipperDuns", "int"),
        ("RateSched", "varchar"),
        ("K", "varchar"),
        ("KStart", "date"),
        ("KExp", "date"),
        ("NegRate", "varchar"),
        ("TportMDQ", "int"),
        ("StorMSQ", "int"),
        ("AgentAMA", "varchar"),
        ("AgentAMAAffiliation", "varchar"),
        ("PtIDCode", "varchar"),
        ("PtName", "varchar"),
        ("PtIDCodeQual", "varchar"),
        ("PtIdenCode", "int"),
        ("Zone", "varchar"),
        ("LocTportMDQ", "int"),
        ("LocStorMSQ", "int"),
        ("CreatedDate", "datetime"),
        ("RateSchedID", "int"),
        ("State", "varchar"),
        ("County", "varchar"),
        ("DUNPCE", "int"),
    ],
)
