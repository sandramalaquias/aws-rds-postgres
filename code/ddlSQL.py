#drop tables and DB
old_schools_table = ['course_school', 'course', 'courses', 'school', 'schools',
                     'modal', 'tech_axis', 'course_type', 'city', 'state']

drop_table = ["DROP TABLE IF EXISTS " + x + " CASCADE" for x in old_schools_table]

#Create tables
course_type = """
CREATE TABLE IF NOT EXISTS course_type (
  course_type_pk SERIAL PRIMARY KEY,
  name VARCHAR UNIQUE NOT NULL
);
"""

tech_axis = """
CREATE TABLE tech_axis (
  tech_axis_pk SERIAL PRIMARY KEY,
  name VARCHAR UNIQUE NOT NULL
);
"""

modal = """
CREATE TABLE modal (
  modal_pk SERIAL PRIMARY KEY,
  name VARCHAR UNIQUE NOT NULL
);
"""

state = """
CREATE TABLE state (
  state_pk SERIAL PRIMARY KEY,
  cod_uf VARCHAR UNIQUE NOT NULL,
  cod_ibge int NOT NULL,
  name VARCHAR NOT NULL
);
"""

city = """
CREATE TABLE city (
  city_pk SERIAL PRIMARY KEY,
  cod_ibge int NOT NULL UNIQUE,
  name VARCHAR NOT NULL,
  state_fk int NOT NULL,
  CONSTRAINT fk_state FOREIGN KEY (state_fk) REFERENCES state (state_pk)
);
"""

course = """
CREATE TABLE IF NOT EXISTS course (
  course_pk SERIAL PRIMARY KEY,
  cod_course int UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  min_workload int NOT NULL,
  tech_axis_fk int NOT NULL,
  course_type_fk int NOT NULL,
  CONSTRAINT fk_tech_axis FOREIGN KEY (tech_axis_fk) REFERENCES tech_axis (tech_axis_pk),
  CONSTRAINT fk_course_type FOREIGN KEY (course_type_fk) REFERENCES course_type (course_type_pk)
);
"""

school = """
CREATE TABLE schools (
    schools_pk SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    city_fk INT NOT NULL,
    unit_cod int NOT NULL UNIQUE,
    CONSTRAINT fk_city FOREIGN KEY (city_fk) REFERENCES city (city_pk),
    CONSTRAINT unique_schools UNIQUE (name, unit_cod)
);
"""

course_school = """
CREATE TABLE course_school (
  course_school_pk SERIAL PRIMARY KEY,
  school_fk int NOT NULL,
  course_fk int NOT NULL,
  modal_fk int NOT NULL,
  local_workload int,
  status varchar NOT NULL,
   CONSTRAINT fk_school FOREIGN KEY (school_fk) REFERENCES schools(schools_pk),
   CONSTRAINT fk_course FOREIGN KEY (course_fk) REFERENCES course(course_pk),
   CONSTRAINT fk_modal  FOREIGN KEY (modal_fk) REFERENCES modal(modal_pk),
   CONSTRAINT unique_course_school UNIQUE (school_fk, course_fk, modal_fk)
);
"""

new_tables = [course_type, tech_axis, modal, state, city, course, school, course_school]



