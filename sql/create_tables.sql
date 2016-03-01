CREATE TABLE user (
  id int(11) NOT NULL AUTO_INCREMENT,
  email varchar(255) DEFAULT NULL,
  password varchar(255) DEFAULT NULL,
  active tinyint(1) DEFAULT NULL,
  confirmed_at datetime DEFAULT NULL,
  last_login_at datetime DEFAULT NULL,
  current_login_at datetime DEFAULT NULL,
  last_login_ip varchar(255) DEFAULT NULL,
  current_login_ip varchar(255) DEFAULT NULL,
  login_count int(11) DEFAULT NULL,
  first_name varchar(30) DEFAULT '',
  last_name varchar(30) DEFAULT '',
  current_hours int(11) DEFAULT '0',
  goal_hours int(11) DEFAULT '0',
  zipcode int(5) DEFAULT NULL,
  profile_pic_url varchar(255) DEFAULT NULL,
  lat float(20,17) DEFAULT NULL,
  lon float(20,17) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY email (email)
);

CREATE TABLE event (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) DEFAULT NULL,
  short_desc varchar(255) DEFAULT NULL,
  description varchar(255) DEFAULT NULL,
  start_date datetime DEFAULT NULL,
  end_date datetime DEFAULT NULL,
  max_volunteers_needed int(11) DEFAULT NULL,
  current_num_volunteers int(11) DEFAULT NULL,
  close_date datetime DEFAULT NULL,
  creator_id int(11) DEFAULT NULL,
  created_date datetime DEFAULT NULL,
  last_updated_date datetime DEFAULT NULL,
  pic_url varchar(255) DEFAULT NULL,
  street_addr varchar(255) DEFAULT NULL,
  city varchar(255) DEFAULT NULL,
  state varchar(255) DEFAULT NULL,
  zipcode varchar(10) DEFAULT NULL,
  organization varchar(255) DEFAULT NULL,
  lat float(20,17) DEFAULT NULL,
  lon float(20,17) DEFAULT NULL,
  PRIMARY KEY (id),
  KEY creator_id (creator_id),
  CONSTRAINT event_ibfk_1 FOREIGN KEY (creator_id) REFERENCES user (id)
);

CREATE TABLE role (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(80) DEFAULT NULL,
  description varchar(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
);

CREATE TABLE skill (
  id int(11) NOT NULL AUTO_INCREMENT,
  name varchar(255) DEFAULT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE events_users (
  event_id int(11) NOT NULL,
  user_id int(11) NOT NULL,
  KEY user_fk (user_id),
  KEY event_fk (event_id),
  CONSTRAINT event_fk FOREIGN KEY (event_id) REFERENCES event (id) ON DELETE CASCADE,
  CONSTRAINT user_fk FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE roles_users (
  user_id int(11) DEFAULT NULL,
  role_id int(11) DEFAULT NULL,
  KEY user_id (user_id),
  KEY role_id (role_id),
  CONSTRAINT roles_users_ibfk_1 FOREIGN KEY (user_id) REFERENCES user (id),
  CONSTRAINT roles_users_ibfk_2 FOREIGN KEY (role_id) REFERENCES role (id)
);

CREATE TABLE skills_events (
  skill_id int(11) DEFAULT NULL,
  event_id int(11) DEFAULT NULL,
  KEY skill_id (skill_id),
  KEY skills_events_ibfk_2 (event_id),
  CONSTRAINT skills_events_ibfk_1 FOREIGN KEY (skill_id) REFERENCES skill (id),
  CONSTRAINT skills_events_ibfk_2 FOREIGN KEY (event_id) REFERENCES event (id) ON DELETE CASCADE
);