CREATE TABLE IF NOT EXISTS timeseriesdata (
    t_stamp TIMESTAMP(3) WITH TIME ZONE,
    tag VARCHAR(16),
    value numeric(8,3)
    );
SELECT create_hypertable('timeseriesdata', 't_stamp');
CREATE INDEX ix_tag_time ON timeseriesdata (tag, t_stamp ASC);

CREATE TABLE IF NOT EXISTS timeseriesnotebook (
    t_stamp TIMESTAMP(3) WITH TIME ZONE,
    note VARCHAR(16)
    );
SELECT create_hypertable('timeseriesnotebook', 't_stamp');

CREATE TABLE IF NOT EXISTS systemconfig (
    time TIMESTAMP(0) WITH TIME ZONE,
    config JSONB
    );

CREATE ROLE {user};
ALTER ROLE {user} WITH LOGIN;
ALTER ROLE {user} WITH PASSWORD '{userpassword}';
GRANT CONNECT ON DATABASE daqdb TO {user};
GRANT USAGE ON SCHEMA public TO {user};
GRANT INSERT, SELECT ON timeseriesdata TO {user};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {user};

