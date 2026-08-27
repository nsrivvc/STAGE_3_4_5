"""Local mock of the NatGasHub API.

Serves the JSON fixtures in /data verbatim over HTTP so downstream consumers
(web apps, the Bronze ETL) can develop against a stable local endpoint. This
package is fully independent of the Neon/Postgres write path — it never
imports the db layer and represents the *upstream* source, not the sink.
"""
