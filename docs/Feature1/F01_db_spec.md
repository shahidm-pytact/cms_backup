# DATABASE DESIGN DOCUMENT
## CMS — F-001 Core Platform Administration

---

## SECTION 1 — COVER PAGE

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                               │
│                          DATABASE DESIGN DOCUMENT                                            │
│                                                                                               │
│                          CMS Platform                                                        │
│                          Feature: F-001 — Core Platform Administration                      │
│                                                                                               │
│                          PostgreSQL Database Specification                                   │
│                          Version: 1.0                                                        │
│                          Date: 2024-01-20                                                    │
│                                                                                               │
│                          Multi-Tenant Prospect Engagement & Outreach Platform                │
│                          Core Platform Administration Database Design                        │
│                                                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

---

## SECTION 2 — DOCUMENT CONTROL

| Field | Value |
|-------|-------|
| **Document Title** | Database Design Document — CMS F-001 Core Platform Administration |
| **Document Version** | 1.0 |
| **Date** | 2024-01-20 |
| **Author** | Database Architect |
| **Status** | Draft |
| **Classification** | Internal |
| **Database System** | PostgreSQL |
| **Database Version** | 14+ |
| **Feature** | F-001 — Core Platform Administration |
| **Project** | CMS Platform |

---

## SECTION 3 — INTRODUCTION

### 3.1 Purpose

This document specifies the database design for the Core Platform Administration feature (F-001) of the CMS multi-tenant B2B platform. This database provides the foundational administrative layer that governs users, roles, permissions, authentication access, and audit logging.

### 3.2 Scope

This database design covers:

- **Users**: Invitation-driven user lifecycle management with authentication
- **Roles**: Role-based access control with system and custom role types
- **Permissions**: Reference data for permission definitions
- **Audit Logs**: Immutable audit trail for all administrative actions

### 3.3 Database Technology

- **Database System**: PostgreSQL 14+
- **Character Set**: UTF-8
- **Timezone**: UTC (all timestamps stored in UTC)
- **Normalization**: Third Normal Form (3NF)

### 3.4 Design Principles

- **Multi-Tenancy**: Organization-based tenant isolation
- **Hard Delete Only**: No soft delete (deleted_at) fields
- **Audit Trail**: Complete audit logging with created_by, updated_by, created_at, updated_at
- **Referential Integrity**: Foreign key constraints with appropriate ON DELETE/ON UPDATE actions
- **Data Integrity**: CHECK constraints for ENUM values, UNIQUE constraints for business keys
- **Performance**: Strategic indexing on foreign keys, updated_at, and query patterns

---

## SECTION 4 — SYSTEM OVERVIEW

### 4.1 Business Context

The CMS platform is a multi-tenant B2B system supporting content management and publishing workflows. The Core Platform Administration feature establishes the secure, auditable administrative foundation required by all other features.

### 4.2 Key Business Rules

1. **User Lifecycle**: Invitation-driven onboarding only. No self-registration.
2. **Access Control**: Role-based access control (RBAC) with permission-based authorization.
3. **Status Lifecycle**: Users and roles have active/inactive status that controls access.
4. **Audit Requirements**: All administrative actions generate immutable audit log entries.
5. **Hard Delete**: No soft delete. Hard delete cascades to dependent data but preserves audit logs.

### 4.3 Entity Relationships

- **User M..1 Role**: Many users belong to one role
- **User 1..M AuditLog**: One user generates many audit logs
- **Permissions**: Reference table (permissions stored as JSON in roles.permissions_json)

### 4.4 User Roles

- **SuperAdmin**: System-wide authority across all users and roles
- **Operator**: Execution-focused role, no administrative authority

---

## SECTION 5 — NON-FUNCTIONAL REQUIREMENTS

### 5.1 Performance Requirements

- **Query Performance**: Sub-second response time for list queries with pagination
- **Indexing Strategy**: Indexes on all foreign keys, updated_at fields, and frequently queried columns
- **Pagination**: All list endpoints support pagination (default 20 items per page, max 100)

### 5.2 Scalability Requirements

- **Audit Log Growth**: Audit logs are append-only and will grow indefinitely (consider archival strategy)
- **Concurrent Access**: Support for concurrent read/write operations with ETag-based concurrency control

### 5.3 Security Requirements

- **Password Storage**: Passwords stored as hashed values (never plaintext)
- **Token Security**: Invitation and password reset tokens stored securely with expiration
- **Audit Trail**: Immutable audit logs for compliance and security monitoring

### 5.4 Data Integrity Requirements

- **Referential Integrity**: Foreign key constraints with appropriate cascade/restrict actions
- **Business Rules**: CHECK constraints for ENUM values, UNIQUE constraints for business keys
- **Nullability Rules**: Enforced based on business logic (e.g., password NULL when status = invited)
- **Data Validation**: Application-level validation for complex business rules

### 5.5 Availability Requirements

- **Backup Strategy**: Regular database backups (implementation-dependent)
- **Disaster Recovery**: Audit logs survive hard deletes (preserved for compliance)

---

## SECTION 6 — LOGICAL DATA MODEL

### 6.1 Entity Overview

The logical data model consists of four core entities:

1. **users**: Authenticated system participants with invitation-driven lifecycle
2. **roles**: Access profiles defining permissions (system and custom roles)
3. **permissions**: Reference data for permission definitions
4. **audit_logs**: Immutable audit trail for all administrative actions

### 6.2 Entity Relationships

```
users (M) ────────> (1) roles
users (1) ────────< (M) audit_logs
users (1) ────────< (M) users (self-reference: invited_by, created_by, updated_by)
```

### 6.3 Key Attributes

**users:**
- Primary Key: id
- Business Key: email (unique, globally)
- Status: invited, active, inactive, expired, cancelled
- Foreign Keys: role_id, invited_by, created_by, updated_by
- Audit: created_at, created_by, updated_at, updated_by, invited_at, invite_accepted_at

**roles:**
- Primary Key: id
- Business Key: slug (unique)
- Status: active, inactive
- Role Type: system, custom
- Audit: created_at, created_by, updated_at, updated_by

**permissions:**
- Primary Key: id
- Status: active, inactive (reference data)
- Audit: created_at, created_by, updated_at, updated_by

**audit_logs:**
- Primary Key: id
- Foreign Keys: user_id (nullable)
- Composite Index: (entity_type, entity_id) for traceability
- Immutable: Append-only, never updated or deleted

---

## SECTION 7 — PHYSICAL DATA MODEL


### 7.2 Table: users

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique user identifier |
| email | VARCHAR(255) | No | No | No | - | NOT NULL, UNIQUE | Unique login identifier, RFC 5322 format, max 254 chars, case-insensitive unique globally |
| name | VARCHAR(255) | No | No | No | - | NOT NULL | User full name, required |
| role_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE | Assigned role, required |
| status | VARCHAR(20) | No | No | No | 'invited' | NOT NULL, CHECK (status IN ('invited', 'active', 'inactive', 'expired', 'cancelled')) | Invitation & account lifecycle status, required |
| password | VARCHAR(255) | No | No | Yes | NULL | - | Hashed user password (never plaintext), NULLABLE only when status = invited |
| invite_token | VARCHAR(255) | No | No | Yes | NULL | - | One-time invitation token, must be present when status = invited |
| invite_expires_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Invitation expiry timestamp (UTC), must be present when status = invited |
| password_reset_token | VARCHAR(255) | No | No | Yes | NULL | - | One-time password reset token, must both be present or both NULL with password_reset_token_expires_at |
| password_reset_token_expires_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Password reset token expiry timestamp (UTC), must both be present or both NULL with password_reset_token |
| invited_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Invitation sent time (UTC) |
| invited_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who sent the invitation |
| invite_accepted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Invitation acceptance time (UTC) |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created (UTC) |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated (UTC) |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |

**Foreign Key Constraints:**
- `role_id` → REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE
- `invited_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
- `created_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `email` (case-insensitive uniqueness enforced at application level)
- CHECK constraint on `status` to ensure only valid status values
- Business rules (enforced at application level):
  - `password` → NULLABLE only when status = invited
  - `invite_token` & `invite_expires_at` → must both be present only when status = invited
  - `password_reset_token` & `password_reset_token_expires_at` → must both be present or both NULL

---

### 7.3 Table: roles

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique role identifier |
| slug | VARCHAR(100) | No | No | No | - | NOT NULL, UNIQUE | Unique role identifier, lowercase alphanumeric and hyphens only, case-insensitive unique |
| name | VARCHAR(255) | No | No | No | - | NOT NULL | Role display name, required |
| status | VARCHAR(20) | No | No | No | 'active' | NOT NULL, CHECK (status IN ('active', 'inactive')) | Role activation status, required |
| role_type | VARCHAR(20) | No | No | No | 'custom' | NOT NULL, CHECK (role_type IN ('system', 'custom')) | Role type: system (inbuilt, immutable except status) or custom (can be updated) |
| permissions_json | JSONB | No | No | No | '{}' | NOT NULL | Assigned permissions as JSON object with structure: { "modules": {...}, "system": {...} } |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created (UTC) |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated (UTC) |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |

**Foreign Key Constraints:**
- `created_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `slug` (case-insensitive uniqueness enforced at application level)
- CHECK constraint on `status` to ensure only 'active' or 'inactive' values
- CHECK constraint on `role_type` to ensure only 'system' or 'custom' values
- Business rule (enforced at application level): System roles are immutable except for status field

---

### 7.4 Table: permissions

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique permission identifier |
| module | VARCHAR(100) | No | No | No | - | NOT NULL | Functional module (e.g., 'organization', 'user'), required |
| action | VARCHAR(100) | No | No | No | - | NOT NULL | Allowed action (e.g., 'read', 'create', 'update', 'delete'), required |
| name | VARCHAR(255) | No | No | No | - | NOT NULL | Permission display name, required |
| description | TEXT | No | No | Yes | NULL | - | Detailed permission meaning, optional |
| status | VARCHAR(20) | No | No | No | 'active' | NOT NULL, CHECK (status IN ('active', 'inactive')) | Reference status, required (treated as always active in domain) |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created (UTC) |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated (UTC) |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |

**Foreign Key Constraints:**
- `created_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- CHECK constraint on `status` to ensure only 'active' or 'inactive' values
- Business rule: Permissions are treated as always active references in the domain (lifecycle changes not part of F-001 behavior)

---

### 7.5 Table: audit_logs

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique audit log identifier |
| user_id | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | Actor who performed the action (nullable for system-generated actions) |
| action | VARCHAR(100) | No | No | No | - | NOT NULL | Action performed (e.g., 'create', 'update', 'delete', 'invite', 'activate'), required |
| entity_type | VARCHAR(50) | No | No | No | - | NOT NULL | Affected entity type (e.g., 'user', 'organization', 'role'), required |
| entity_id | UUID | No | No | No | - | NOT NULL | Affected record identifier (UUID format), required |
| old_values | JSONB | No | No | Yes | NULL | - | Before state (JSON object), nullable for create actions |
| new_values | JSONB | No | No | Yes | NULL | - | After state (JSON object), nullable for delete actions |
| ip_address | VARCHAR(45) | No | No | Yes | NULL | - | Actor IP address (supports IPv4 and IPv6), optional |
| user_agent | TEXT | No | No | Yes | NULL | - | Client information (browser, device, etc.), optional |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Action timestamp (UTC), immutable |
| description | TEXT | No | No | Yes | NULL | - | Human-readable summary of the action, optional |

**Foreign Key Constraints:**
- `user_id` → REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- CHECK constraint: `action` → NOT NULL
- CHECK constraint: `entity_type` → NOT NULL
- Composite index on (entity_type, entity_id) for traceability (see Section 9)
- Business rule: Audit logs are immutable and append-only (never updated or deleted)

---

## SECTION 8 — NORMALIZATION

### 8.1 First Normal Form (1NF) Verification

**users:**
- [x] All columns contain atomic values (no arrays, no comma-separated lists)
- [x] Each column contains only one type of data
- [x] Each column has a unique name
- [x] Order of rows/columns doesn't matter
- [x] No repeating groups of columns

**roles:**
- [x] All columns contain atomic values (no arrays, no comma-separated lists)
- [x] Each column contains only one type of data
- [x] Each column has a unique name
- [x] Order of rows/columns doesn't matter
- [x] No repeating groups of columns
- **Note:** `permissions_json` is a JSONB object, which is acceptable as it represents a structured document (not a repeating group)

**permissions:**
- [x] All columns contain atomic values (no arrays, no comma-separated lists)
- [x] Each column contains only one type of data
- [x] Each column has a unique name
- [x] Order of rows/columns doesn't matter
- [x] No repeating groups of columns

**audit_logs:**
- [x] All columns contain atomic values (no arrays, no comma-separated lists)
- [x] Each column contains only one type of data
- [x] Each column has a unique name
- [x] Order of rows/columns doesn't matter
- [x] No repeating groups of columns
- **Note:** `old_values` and `new_values` are JSONB objects, which is acceptable as they represent structured document snapshots (not repeating groups)

### 8.2 Second Normal Form (2NF) Verification

**users:**
- [x] Table is in 1NF
- [x] All non-key columns depend on the entire primary key (id)
- [x] No partial dependencies (single-column primary key)

**roles:**
- [x] Table is in 1NF
- [x] All non-key columns depend on the entire primary key (id)
- [x] No partial dependencies (single-column primary key)

**permissions:**
- [x] Table is in 1NF
- [x] All non-key columns depend on the entire primary key (id)
- [x] No partial dependencies (single-column primary key)

**audit_logs:**
- [x] Table is in 1NF
- [x] All non-key columns depend on the entire primary key (id)
- [x] No partial dependencies (single-column primary key)

### 8.3 Third Normal Form (3NF) Verification

**users:**
- [x] Table is in 2NF
- [x] No transitive dependencies (non-key columns don't depend on other non-key columns)
- [x] All non-key columns depend directly on the primary key
- **Note:** Foreign keys (role_id, organization_id) are references, not dependencies

**roles:**
- [x] Table is in 2NF
- [x] No transitive dependencies (non-key columns don't depend on other non-key columns)
- [x] All non-key columns depend directly on the primary key

**permissions:**
- [x] Table is in 2NF
- [x] No transitive dependencies (non-key columns don't depend on other non-key columns)
- [x] All non-key columns depend directly on the primary key

**audit_logs:**
- [x] Table is in 2NF
- [x] No transitive dependencies (non-key columns don't depend on other non-key columns)
- [x] All non-key columns depend directly on the primary key

### 8.4 Acceptable Denormalization

**JSONB Fields:**
- `roles.permissions_json`: JSONB object storing permission assignments. This is acceptable denormalization as it:
  - Represents a structured document (permission configuration)
  - Improves read performance (no joins required)
  - Permissions are reference data, not frequently updated
  - Documented as intentional denormalization for performance

- `audit_logs.old_values` and `audit_logs.new_values`: JSONB objects storing state snapshots. This is acceptable denormalization as it:
  - Represents immutable historical snapshots
  - Preserves complete state even if referenced entities are deleted
  - Required for audit trail integrity
  - Documented as intentional denormalization for audit compliance

**Rationale:** Both JSONB fields serve specific purposes (configuration storage and audit snapshots) and are justified by performance and compliance requirements.

---

## SECTION 9 — INDEX STRATEGY

### 9.1 Primary Key Indexes

All primary keys are automatically indexed by PostgreSQL. Explicit definitions for documentation:

```sql
-- Primary Key Indexes (automatically created by PostgreSQL)
CREATE UNIQUE INDEX pk_users ON users(id);
CREATE UNIQUE INDEX pk_roles ON roles(id);
CREATE UNIQUE INDEX pk_permissions ON permissions(id);
CREATE UNIQUE INDEX pk_audit_logs ON audit_logs(id);
```

### 9.2 Foreign Key Indexes

**CRITICAL:** Every foreign key column MUST have an index for JOIN performance and referential integrity checks.

```sql
-- Foreign Key Indexes
-- users table
CREATE INDEX idx_users_role_id ON users(role_id);
CREATE INDEX idx_users_invited_by ON users(invited_by);
CREATE INDEX idx_users_created_by ON users(created_by);
CREATE INDEX idx_users_updated_by ON users(updated_by);

-- roles table
CREATE INDEX idx_roles_created_by ON roles(created_by);
CREATE INDEX idx_roles_updated_by ON roles(updated_by);

-- permissions table
CREATE INDEX idx_permissions_created_by ON permissions(created_by);
CREATE INDEX idx_permissions_updated_by ON permissions(updated_by);

-- audit_logs table
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
```

### 9.3 Audit Field Indexes

**MANDATORY:** Every table with `updated_at` MUST have an index for incremental sync and change tracking.

```sql
-- Audit Field Indexes (updated_at)
CREATE INDEX idx_users_updated_at ON users(updated_at);
CREATE INDEX idx_roles_updated_at ON roles(updated_at);
CREATE INDEX idx_permissions_updated_at ON permissions(updated_at);
-- Note: audit_logs uses created_at (immutable), indexed below
```

### 9.4 Unique Constraint Indexes

```sql
-- Unique Constraint Indexes
CREATE UNIQUE INDEX uq_users_email ON users(email);
CREATE UNIQUE INDEX uq_roles_slug ON roles(slug);
```

### 9.5 Composite Indexes

```sql
-- Composite Indexes for Common Query Patterns

-- audit_logs: Traceability index (entity_type, entity_id) - REQUIRED per domain model
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- audit_logs: Filter by user and date range (user activity queries)
CREATE INDEX idx_audit_logs_user_created ON audit_logs(user_id, created_at) WHERE user_id IS NOT NULL;

-- audit_logs: Filter by entity type and action (common audit queries)
CREATE INDEX idx_audit_logs_entity_action ON audit_logs(entity_type, action);

-- audit_logs: Sort by created_at (default sort for audit log listing)
CREATE INDEX idx_audit_logs_created_at_desc ON audit_logs(created_at DESC);
```

### 9.6 Text Search Indexes

```sql
-- Text Search Indexes (if full-text search is required)
-- Enable pg_trgm extension for trigram matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- users: Search by email or name
CREATE INDEX idx_users_email_trgm ON users USING gin(email gin_trgm_ops);
CREATE INDEX idx_users_name_trgm ON users USING gin(name gin_trgm_ops);

-- roles: Search by name or slug
CREATE INDEX idx_roles_name_trgm ON roles USING gin(name gin_trgm_ops);
CREATE INDEX idx_roles_slug_trgm ON roles USING gin(slug gin_trgm_ops);
```

### 9.7 Partial Indexes

```sql
-- Partial Indexes for Common Filtered Queries

-- users: Active users only (common query pattern)
CREATE INDEX idx_users_active ON users(id, role_id) WHERE status = 'active';

-- users: Invited users only (invitation management)
CREATE INDEX idx_users_invited ON users(id, email, invite_expires_at) WHERE status = 'invited';

-- roles: Active roles only
CREATE INDEX idx_roles_active ON roles(id, slug, name) WHERE status = 'active';
```

### 9.8 Index Summary

| Table | Index Count | Index Types |
|-------|------------|-------------|
| users | 10 | PK, FK (4), Unique (1), updated_at (1), Text Search (2), Partial (2) |
| roles | 6 | PK, FK (2), Unique (1), updated_at (1), Text Search (2) |
| permissions | 4 | PK, FK (2), updated_at (1) |
| audit_logs | 6 | PK, FK (1), Composite (4), created_at (1) |

**Total Indexes:** 26 indexes across 4 tables

---

## SECTION 10 — PROFESSIONAL ASCII ER DIAGRAM

```
ENTITY RELATIONSHIP DIAGRAM (ERD)
CMS - F-001 Core Platform Administration
Crow's Foot Notation - PK and FK Fields Only

+----------------------+              +----------------------+
|       users          |   1     M    |    audit_logs        |
+----------------------+              +----------------------+
| id (PK)              |<------------>| id (PK)              |
| role_id (FK)         |              | user_id (FK)         |
| invited_by (FK)      |              |                      |
| created_by (FK)      |              |                      |
| updated_by (FK)      |              |                      |
+----------------------+              +----------------------+
                                              |
                                              | 1
                                              |
                                              |
                                              | M
                                              |
                                              v
                                    +----------------------+
                                    |       roles          |
                                    +----------------------+
                                    | id (PK)              |
                                    |                      |
                                    |                      |
                                    +----------------------+
                                              |
                                              |
                                              |
                                              |
                                              v
                                    +----------------------+
                                    |    permissions       |
                                    +----------------------+
                                    | id (PK)              |
                                    |                      |
                                    |                      |
                                    +----------------------+

RELATIONSHIP CARDINALITY:
- User M..1 Role (many users belong to one role)
- User 1..M AuditLog (one user generates many audit logs)
- User self-reference: invited_by, created_by, updated_by → users.id
- Permissions: Reference table (no direct FK relationship, permissions stored as JSON in roles.permissions_json)

FOREIGN KEY ACTIONS:
- users.role_id → roles.id: ON DELETE RESTRICT ON UPDATE CASCADE
- users.invited_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- users.created_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- users.updated_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- roles.created_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- roles.updated_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- permissions.created_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- permissions.updated_by → users.id: ON DELETE SET NULL ON UPDATE CASCADE
- audit_logs.user_id → users.id: ON DELETE SET NULL ON UPDATE CASCADE
```

---

## APPENDIX A — DATA TYPE MAPPING

### A.1 Domain Model to PostgreSQL Mapping

| Domain Model Type | PostgreSQL Type | Notes |
|------------------|----------------|-------|
| INTEGER (Primary Key) | UUID | Using UUID for primary keys with gen_random_uuid() |
| INTEGER (Foreign Key) | UUID | Foreign keys reference UUID primary keys |
| VARCHAR(n) | VARCHAR(n) | String fields with specified length |
| TEXT | TEXT | Unlimited length text fields |
| ENUM | VARCHAR(n) with CHECK | ENUM values enforced via CHECK constraints |
| TIMESTAMP | TIMESTAMPTZ | All timestamps in UTC timezone |
| JSON | JSONB | JSON fields use JSONB for better performance |

### A.2 Default Values

- **Primary Keys**: `gen_random_uuid()` for UUID generation
- **Timestamps**: `CURRENT_TIMESTAMP` for created_at and updated_at
- **Status Fields**: Default to 'active' or 'invited' based on entity type
- **Audit Fields**: NULL for created_by, updated_by (set by application)

---

## APPENDIX B — CONSTRAINTS SUMMARY

### B.1 CHECK Constraints

- `users.status`: IN ('invited', 'active', 'inactive', 'expired', 'cancelled')
- `roles.status`: IN ('active', 'inactive')
- `roles.role_type`: IN ('system', 'custom')
- `permissions.status`: IN ('active', 'inactive')

### B.2 UNIQUE Constraints

- `users.email`: UNIQUE (case-insensitive at application level)
- `roles.slug`: UNIQUE (case-insensitive at application level)

### B.3 Foreign Key Constraints

All foreign keys have appropriate ON DELETE/ON UPDATE actions as specified in Section 7.

---

**END OF DOCUMENT**

