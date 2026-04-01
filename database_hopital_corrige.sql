CREATE TABLE "staff" (
  "id" int PRIMARY KEY,
  "first_name" varchar,
  "last_name" varchar,
  "email" varchar UNIQUE,
  "phone" varchar,
  "is_active" boolean DEFAULT true,
  "created_at" timestamp
);

CREATE TABLE "role" (
  "id" int PRIMARY KEY,
  "name" varchar
);

CREATE TABLE "staff_role" (
  "staff_id" int,
  "role_id" int,
  PRIMARY KEY ("staff_id", "role_id")
);

CREATE TABLE "specialty" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "parent_id" int
);

CREATE TABLE "staff_specialty" (
  "staff_id" int,
  "specialty_id" int,
  PRIMARY KEY ("staff_id", "specialty_id")
);

CREATE TABLE "contract_type" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "max_hours_per_week" int,
  "leave_days_per_year" int,
  "night_shift_allowed" boolean
);

CREATE TABLE "contract" (
  "id" int PRIMARY KEY,
  "staff_id" int,
  "contract_type_id" int,
  "start_date" date,
  "end_date" date,
  "workload_percent" int
);

CREATE TABLE "certification" (
  "id" int PRIMARY KEY,
  "name" varchar
);

CREATE TABLE "certification_dependency" (
  "parent_cert_id" int,
  "required_cert_id" int,
  PRIMARY KEY ("parent_cert_id", "required_cert_id")
);

CREATE TABLE "staff_certification" (
  "id" int PRIMARY KEY,
  "staff_id" int,
  "certification_id" int,
  "obtained_date" date,
  "expiration_date" date
);

CREATE TABLE "service" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "manager_id" int,
  "bed_capacity" int,
  "criticality_level" int
);

CREATE TABLE "care_unit" (
  "id" int PRIMARY KEY,
  "service_id" int,
  "name" varchar
);

CREATE TABLE "service_status" (
  "id" int PRIMARY KEY,
  "service_id" int,
  "status" varchar,
  "start_date" date,
  "end_date" date
);

CREATE TABLE "staff_service_assignment" (
  "id" int PRIMARY KEY,
  "staff_id" int,
  "service_id" int,
  "start_date" date,
  "end_date" date
);

CREATE TABLE "shift_type" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "duration_hours" int,
  "requires_rest_after" boolean
);

CREATE TABLE "shift" (
  "id" int PRIMARY KEY,
  "care_unit_id" int,
  "shift_type_id" int,
  "start_datetime" timestamp,
  "end_datetime" timestamp,
  "min_staff" int,
  "max_staff" int
);

CREATE TABLE "shift_required_certification" (
  "shift_id" int,
  "certification_id" int,
  PRIMARY KEY ("shift_id", "certification_id")
);

CREATE TABLE "shift_assignment" (
  "id" int PRIMARY KEY,
  "shift_id" int,
  "staff_id" int,
  "assigned_at" timestamp
);

CREATE TABLE "absence_type" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "impacts_quota" boolean
);

CREATE TABLE "absence" (
  "id" int PRIMARY KEY,
  "staff_id" int,
  "absence_type_id" int,
  "start_date" date,
  "expected_end_date" date,
  "actual_end_date" date,
  "is_planned" boolean
);

CREATE TABLE "preference" (
  "id" int PRIMARY KEY,
  "staff_id" int,
  "type" varchar,
  "description" varchar,
  "is_hard_constraint" boolean,
  "start_date" date,
  "end_date" date
);

CREATE TABLE "patient_load" (
  "id" int PRIMARY KEY,
  "care_unit_id" int,
  "date" date,
  "patient_count" int,
  "occupancy_rate" float
);

CREATE TABLE "staff_loan" (
  "id" int PRIMARY KEY,
  "staff_id" int,
  "from_service_id" int,
  "to_service_id" int,
  "start_date" date,
  "end_date" date
);

CREATE TABLE "rule" (
  "id" int PRIMARY KEY,
  "name" varchar,
  "description" varchar,
  "rule_type" varchar,
  "value" numeric,
  "unit" varchar,
  "valid_from" date,
  "valid_to" date
);

ALTER TABLE "specialty" ADD FOREIGN KEY ("parent_id") REFERENCES "specialty" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "contract" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "contract" ADD FOREIGN KEY ("contract_type_id") REFERENCES "contract_type" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "certification_dependency" ADD FOREIGN KEY ("parent_cert_id") REFERENCES "certification" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "certification_dependency" ADD FOREIGN KEY ("required_cert_id") REFERENCES "certification" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_certification" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_certification" ADD FOREIGN KEY ("certification_id") REFERENCES "certification" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "service" ADD FOREIGN KEY ("manager_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "care_unit" ADD FOREIGN KEY ("service_id") REFERENCES "service" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "service_status" ADD FOREIGN KEY ("service_id") REFERENCES "service" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_service_assignment" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_service_assignment" ADD FOREIGN KEY ("service_id") REFERENCES "service" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "shift" ADD FOREIGN KEY ("care_unit_id") REFERENCES "care_unit" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "shift" ADD FOREIGN KEY ("shift_type_id") REFERENCES "shift_type" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "shift_required_certification" ADD FOREIGN KEY ("shift_id") REFERENCES "shift" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "shift_required_certification" ADD FOREIGN KEY ("certification_id") REFERENCES "certification" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "shift_assignment" ADD FOREIGN KEY ("shift_id") REFERENCES "shift" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "shift_assignment" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "absence" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "absence" ADD FOREIGN KEY ("absence_type_id") REFERENCES "absence_type" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "preference" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "patient_load" ADD FOREIGN KEY ("care_unit_id") REFERENCES "care_unit" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_loan" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_loan" ADD FOREIGN KEY ("from_service_id") REFERENCES "service" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_loan" ADD FOREIGN KEY ("to_service_id") REFERENCES "service" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_role" ADD FOREIGN KEY ("role_id") REFERENCES "role" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_role" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_specialty" ADD FOREIGN KEY ("staff_id") REFERENCES "staff" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "staff_specialty" ADD FOREIGN KEY ("specialty_id") REFERENCES "specialty" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "contract_type" ADD FOREIGN KEY ("id") REFERENCES "rule" ("id") DEFERRABLE INITIALLY IMMEDIATE;
