CREATE TABLE entries (
  id int(11) unsigned NOT NULL AUTO_INCREMENT,
  title text,
  content text,
  posted_on datetime DEFAULT NULL,
  published int(11) NOT NULL DEFAULT '0',
  trash int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (id)
);

CREATE TABLE users (
  id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  user varchar(80) NOT NULL,
  pass char(40) NOT NULL,
  salt char(40) NOT NULL,
  email varchar(100) NOT NULL,
  privilege int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (id),
  UNIQUE KEY id (id)
);