--drop table posts;
--ALTER TABLE posts ADD COLUMN  media_id bigint;
CREATE TABLE destinations
  (
     channel_id BIGINT NOT NULL,
     name       VARCHAR(128) NOT NULL,
     group_id   BIGINT,
     footer     TEXT,
     PRIMARY KEY (channel_id)
  );

CREATE TABLE sources
  (
     channel_id   BIGINT NOT NULL,
     channel_name VARCHAR(128) NOT NULL,
     bias         TEXT,
     display_name VARCHAR(128),
     invite       VARCHAR(20),
     username     VARCHAR(32),
     api_id       INT,
     description  TEXT,
     rating       INT,
     destination  BIGINT,
     detail_id    INT,
     is_spread boolean  default true,
     is_active boolean  default false,
     PRIMARY KEY (channel_id),
     CONSTRAINT fk_destination FOREIGN KEY(destination) REFERENCES destinations(
     channel_id),
     CONSTRAINT fk_account FOREIGN KEY(api_id) REFERENCES accounts(api_id)
  );

CREATE TABLE bloats
  (
     channel_id BIGINT NOT NULL,
     pattern    TEXT NOT NULL,
     PRIMARY KEY (channel_id, pattern),
     CONSTRAINT fk_channel FOREIGN KEY(channel_id) REFERENCES sources(channel_id
     )
  );

CREATE TABLE posts
  (
     destination       BIGINT NOT NULL,
     message_id        INT NOT NULL,
     source_channel_id BIGINT NOT NULL,
     source_message_id INT NOT NULL,
     backup_id         INT NOT NULL,
     reply_id          INT,
     message_text      TEXT,
     file_id           BIGINT,
     PRIMARY KEY (source_channel_id, source_message_id),
     CONSTRAINT fk_channel FOREIGN KEY(source_channel_id) REFERENCES sources(
     channel_id),
     CONSTRAINT fk_destination FOREIGN KEY(destination) REFERENCES destinations(
     channel_id)
  );

CREATE TABLE accounts
  (
     api_id       BIGINT NOT NULL,
     api_hash     TEXT NOT NULL,
     name         VARCHAR(20) NOT NULL,
     phone_number VARCHAR(14) NOT NULL,
     description  TEXT,
     PRIMARY KEY (api_id)
  );