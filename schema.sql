drop table posts;
--ALTER TABLE posts ADD COLUMN  media_id bigint;

create table sources
(
    channel_id bigint not null,
    channel_name varchar(128) not null,
    bias text,
    display_name varchar(128),
    invite varchar(20),
    username varchar(32),
    api_id      int,
    description text,
    rating       int,
    detail_id      int ,

    primary key (channel_id)
);

create table bloats
(
    channel_id bigint not null,
    pattern text not null,

    primary key (channel_id,pattern),

    CONSTRAINT fk_channel
      FOREIGN KEY(channel_id)
	  REFERENCES sources(channel_id)
);

create table posts
(

    channel_id bigint not null,
    message_id   int not null,
    source_channel_id bigint not null,
    source_message_id  int not null,
    backup_id  int not null,
    reply_id int,
    message_text text,
    file_id bigint,

    primary key (source_channel_id, source_message_id),

    CONSTRAINT fk_channel
      FOREIGN KEY(source_channel_id)
	  REFERENCES sources(channel_id)
);