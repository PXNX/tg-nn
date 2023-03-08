--drop table posts;
--ALTER TABLE posts ADD COLUMN  media_id bigint;

create table destinations
(
    channel_id bigint not null,
       name varchar(128) not null,
   group_id bigint,

    primary key (channel_id)
);

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
    destination  bigint,
    detail_id      int ,

    primary key (channel_id),

    CONSTRAINT fk_destination FOREIGN KEY(destination) REFERENCES destinations(channel_id),
     CONSTRAINT fk_account FOREIGN KEY(api_id) REFERENCES accounts(api_id)
);

create table bloats
(
    channel_id bigint not null,
    pattern text not null,

    primary key (channel_id,pattern),

    CONSTRAINT fk_channel FOREIGN KEY(channel_id) REFERENCES sources(channel_id)
);

create table posts
(
    destination bigint not null,
    message_id   int not null,
    source_channel_id bigint not null,
    source_message_id  int not null,
    backup_id  int not null,
    reply_id int,
    message_text text,
    file_id bigint,
    primary key (source_channel_id, source_message_id),

    CONSTRAINT fk_channel FOREIGN KEY(source_channel_id) REFERENCES sources(channel_id),
	CONSTRAINT fk_destination FOREIGN KEY(destination) REFERENCES destinations(channel_id)
);

create table accounts
(
    api_id bigint not null,
     api_hash text not null,
        name varchar(20) not null,
        phone_number varchar(14) not null,
        description text,

    primary key (api_id)
);