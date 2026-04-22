-- ============================================
-- Schéma SQL – Base de données Lycée RGPD
-- Exporté le 22/04/2026 à 13:53:21
-- Base : SQLite
--
-- Classification RGPD des tables :
--   [IDENTITÉ]  eleves_eleve, eleves_parent, eleves_eleve_parents
--   [SCOLAIRE]  eleves_scolarite, eleves_note, eleves_matiere
--   [SENSIBLE]  eleves_sante, eleves_medecintraitant
-- ============================================

-- ============================================================
-- DONNÉES D'IDENTITÉ — Art. 6 §1 e RGPD — Accès : Administration
-- ============================================================

-- [TABLE] eleves_eleve
CREATE TABLE "eleves_eleve" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nom" varchar(100) NOT NULL, "prenom" varchar(100) NOT NULL, "date_naissance" date NULL, "adresse" text NOT NULL, "email" varchar(254) NOT NULL, "telephone" varchar(20) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL);

-- [TABLE] eleves_eleve_parents
CREATE TABLE "eleves_eleve_parents" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "eleve_id" bigint NOT NULL REFERENCES "eleves_eleve" ("id") DEFERRABLE INITIALLY DEFERRED, "parent_id" bigint NOT NULL REFERENCES "eleves_parent" ("id") DEFERRABLE INITIALLY DEFERRED);

-- [TABLE] eleves_parent
CREATE TABLE "eleves_parent" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nom" varchar(100) NOT NULL, "prenom" varchar(100) NOT NULL, "telephone" varchar(20) NOT NULL, "email" varchar(254) NOT NULL, "lien" varchar(20) NOT NULL);


-- ============================================================
-- DONNÉES SCOLAIRES — Art. 6 §1 e RGPD — Accès : Professeurs & Scolarité
-- ============================================================

-- [TABLE] eleves_matiere
CREATE TABLE "eleves_matiere" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nom" varchar(100) NOT NULL, "coefficient" decimal NOT NULL);

-- [TABLE] eleves_note
CREATE TABLE "eleves_note" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "note" decimal NOT NULL, "appreciation" text NOT NULL, "trimestre" integer NOT NULL, "date" date NOT NULL, "eleve_id" bigint NOT NULL REFERENCES "eleves_eleve" ("id") DEFERRABLE INITIALLY DEFERRED, "matiere_id" bigint NOT NULL REFERENCES "eleves_matiere" ("id") DEFERRABLE INITIALLY DEFERRED);

-- [TABLE] eleves_scolarite
CREATE TABLE "eleves_scolarite" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "classe" varchar(20) NOT NULL, "options" text NOT NULL, "eleve_id" bigint NOT NULL UNIQUE REFERENCES "eleves_eleve" ("id") DEFERRABLE INITIALLY DEFERRED);


-- ============================================================
-- DONNÉES SENSIBLES — Art. 9 RGPD — Accès RESTREINT : Pôle médical & Cantine
-- ============================================================

-- [TABLE] eleves_medecintraitant
CREATE TABLE "eleves_medecintraitant" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nom" varchar(100) NOT NULL, "prenom" varchar(100) NOT NULL, "telephone" varchar(20) NOT NULL, "adresse" text NOT NULL);

-- [TABLE] eleves_sante
CREATE TABLE "eleves_sante" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "allergies" text NOT NULL, "habitudes_alimentaires" text NOT NULL, "eleve_id" bigint NOT NULL UNIQUE REFERENCES "eleves_eleve" ("id") DEFERRABLE INITIALLY DEFERRED, "medecin_id" bigint NULL REFERENCES "eleves_medecintraitant" ("id") DEFERRABLE INITIALLY DEFERRED);


-- ============================================================
-- TABLES SYSTÈMES / DJANGO
-- ============================================================

-- [TABLE] auth_group
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

-- [TABLE] auth_group_permissions
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- [TABLE] auth_permission
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

-- [TABLE] auth_user
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);

-- [TABLE] auth_user_groups
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

-- [TABLE] auth_user_user_permissions
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

-- [TABLE] django_admin_log
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

-- [TABLE] django_content_type
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

-- [TABLE] django_migrations
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

-- [TABLE] django_session
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

-- [TABLE] sqlite_sequence
CREATE TABLE sqlite_sequence(name,seq);

-- [INDEX] auth_group_permissions_group_id_b120cbf9
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");

-- [INDEX] auth_group_permissions_group_id_permission_id_0cd325b0_uniq
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");

-- [INDEX] auth_group_permissions_permission_id_84c5c92e
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");

-- [INDEX] auth_permission_content_type_id_2f476e4b
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");

-- [INDEX] auth_permission_content_type_id_codename_01ab375a_uniq
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");

-- [INDEX] auth_user_groups_group_id_97559544
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");

-- [INDEX] auth_user_groups_user_id_6a12ed8b
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");

-- [INDEX] auth_user_groups_user_id_group_id_94350c0c_uniq
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");

-- [INDEX] auth_user_user_permissions_permission_id_1fbb5f2c
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");

-- [INDEX] auth_user_user_permissions_user_id_a95ead1b
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");

-- [INDEX] auth_user_user_permissions_user_id_permission_id_14a6b632_uniq
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");

-- [INDEX] django_admin_log_content_type_id_c4bce8eb
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");

-- [INDEX] django_admin_log_user_id_c564eba6
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");

-- [INDEX] django_content_type_app_label_model_76bd3d3b_uniq
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");

-- [INDEX] django_session_expire_date_a5c62663
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");

-- [INDEX] eleves_eleve_parents_eleve_id_1ac0a8d8
CREATE INDEX "eleves_eleve_parents_eleve_id_1ac0a8d8" ON "eleves_eleve_parents" ("eleve_id");

-- [INDEX] eleves_eleve_parents_eleve_id_parent_id_633254bd_uniq
CREATE UNIQUE INDEX "eleves_eleve_parents_eleve_id_parent_id_633254bd_uniq" ON "eleves_eleve_parents" ("eleve_id", "parent_id");

-- [INDEX] eleves_eleve_parents_parent_id_8e189e09
CREATE INDEX "eleves_eleve_parents_parent_id_8e189e09" ON "eleves_eleve_parents" ("parent_id");

-- [INDEX] eleves_note_eleve_id_a38103c3
CREATE INDEX "eleves_note_eleve_id_a38103c3" ON "eleves_note" ("eleve_id");

-- [INDEX] eleves_note_matiere_id_b144981e
CREATE INDEX "eleves_note_matiere_id_b144981e" ON "eleves_note" ("matiere_id");

-- [INDEX] eleves_sante_medecin_id_d98d389f
CREATE INDEX "eleves_sante_medecin_id_d98d389f" ON "eleves_sante" ("medecin_id");