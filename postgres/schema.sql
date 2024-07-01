/*
  This will partition the device data table by time, on a daily basis.
  TODO: explore partitioning based on workspace_id/property_id/device_id too. Maybe an index will suffice?
	Lifted from `github.com/sensand/data-pipeline`
*/

-- Setup Partman
CREATE SCHEMA partman;

CREATE EXTENSION pg_partman SCHEMA partman;

-- Create device data parent table
CREATE TABLE partman.device_data(
  workspace_id uuid NOT NULL,
  property_id uuid NOT NULL,
  device_id text NOT NULL,
  ts timestamp(6) NOT NULL DEFAULT now(),
  reading jsonb NOT NULL
)
PARTITION BY RANGE (ts);

CREATE INDEX ON partman.device_data(ts);
CREATE INDEX ON partman.device_data USING btree (workspace_id, property_id, device_id, ts DESC);
CREATE INDEX ON partman.device_data USING btree (workspace_id, property_id, ts DESC);
CREATE INDEX ON partman.device_data USING btree (workspace_id, ts DESC);

-- Create device data template table
CREATE TABLE partman.device_data_template (LIKE partman.device_data);

-- Create the partition table
SELECT partman.create_parent(
    p_parent_table := 'partman.device_data'
    , p_control := 'ts'
    , p_interval := '1 day'
    , p_premake := 1
    , p_template_table := 'partman.device_data_template'
);
