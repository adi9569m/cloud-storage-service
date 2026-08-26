# Cloud Storage Service - Database Schema Documentation

## 1. Overview & Design Principles

The database schema is engineered for a high-performance, role-based cloud storage application built on **PostgreSQL (Supabase)** and managed via **SQLAlchemy 2.0**.

### Key Architectural Tenets
1. **Universally Unique Identifiers (UUIDv4)**: All primary keys use UUIDs (`uuid_generate_v4()` or Python `uuid.uuid4`). This eliminates enumeration attacks, enables distributed ID generation, and decouples internal IDs from sequential predictability.
2. **Strict Time Zone Handling**: All timestamp columns use `TIMESTAMPTZ` (UTC) with default value `CURRENT_TIMESTAMP`.
3. **Safe Deletion & Non-Destructive Cascades**:
   - Files and folders implement soft deletion (`is_deleted`, `deleted_at`) to support the MVP Trash and Restore feature.
   - Foreign keys pointing from critical entities (e.g., `files.owner_id`, `folders.owner_id`) use `ON DELETE RESTRICT` or `ON DELETE SET NULL` rather than `CASCADE`, preventing accidental catastrophic file drops.
   - Child records tied strictly to the lifecycle of a single parent entity (e.g. `file_versions` for a file, `shares` for an item) use `ON DELETE CASCADE` only when hard-deleting that specific parent item.
4. **Normalized Access Control**: Direct user-to-user shares (`shares`) and tokenized public links (`link_shares`) are explicitly modeled with role definitions (`VIEWER`, `EDITOR`).
5. **Targeted Indexing**: Composite indexes optimize common query patterns such as folder navigation (`owner_id, parent_id, is_deleted`), file searching (`name, owner_id`), and activity timelines.

---

## 2. Entity Summaries & Data Dictionary

```
+-----------------------------------------------------------------------------------+
| Table Name     | Purpose                                                          |
+----------------+------------------------------------------------------------------+
| users          | Core user identity, credentials, status, and storage metrics     |
| folders        | Hierarchical directory tree structure                            |
| files          | File metadata, storage keys, active version references           |
| file_versions  | Historic and current file binary version tracking                |
| shares         | Direct user-to-user sharing with role-based access control       |
| link_shares    | Public tokenized share links with expiry & password protection   |
| stars          | User bookmarks/favorites for files and folders                   |
| activities     | Audit log for file and folder actions                            |
+----------------+------------------------------------------------------------------+
```

---

### 2.1 Table: `users`
Represents registered users in the platform.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `email` | `VARCHAR(255)` | No | - | **Unique**, Indexed, Lowercase trimmed email |
| `hashed_password` | `VARCHAR(255)` | No | - | Bcrypt/Argon2 password hash |
| `full_name` | `VARCHAR(150)` | Yes | `NULL` | User's display name |
| `avatar_url` | `VARCHAR(500)` | Yes | `NULL` | Profile avatar URL |
| `is_active` | `BOOLEAN` | No | `TRUE` | Account active state |
| `is_verified` | `BOOLEAN` | No | `FALSE` | Email verification status |
| `storage_used_bytes` | `BIGINT` | No | `0` | Aggregated storage consumption in bytes |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update timestamp |

- **Indexes**:
  - `idx_users_email` ON (`email`) UNIQUE
- **Relationships**:
  - `folders`: 1-to-Many with `folders.owner_id`
  - `files`: 1-to-Many with `files.owner_id`
  - `shares_received`: 1-to-Many with `shares.grantee_id`
  - `shares_granted`: 1-to-Many with `shares.granter_id`
  - `stars`: 1-to-Many with `stars.user_id`
  - `activities`: 1-to-Many with `activities.user_id`

---

### 2.2 Table: `folders`
Represents folder hierarchy. Folders can be nested arbitrarily by referencing `parent_id`.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `name` | `VARCHAR(255)` | No | - | Folder display name |
| `parent_id` | `UUID` | Yes | `NULL` | Foreign Key -> `folders.id` (`ON DELETE RESTRICT`), `NULL` = Root |
| `owner_id` | `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE RESTRICT`) |
| `color` | `VARCHAR(30)` | Yes | `NULL` | UI folder accent color (hex/keyword) |
| `is_deleted` | `BOOLEAN` | No | `FALSE` | Soft-delete flag (Trash) |
| `deleted_at` | `TIMESTAMPTZ` | Yes | `NULL` | Timestamp when moved to Trash |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update timestamp |

- **Indexes & Constraints**:
  - `idx_folders_owner_parent` ON (`owner_id`, `parent_id`, `is_deleted`)
  - `idx_folders_is_deleted` ON (`is_deleted`, `deleted_at`)
- **Relationships**:
  - `owner`: Many-to-1 with `User`
  - `parent`: Many-to-1 with `Folder`
  - `subfolders`: 1-to-Many with `Folder` (`parent_id`)
  - `files`: 1-to-Many with `File` (`folder_id`)
  - `shares`: 1-to-Many with `Share` (`folder_id`)
  - `link_shares`: 1-to-Many with `LinkShare` (`folder_id`)

---

### 2.3 Table: `files`
Represents stored files and their primary metadata.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `name` | `VARCHAR(255)` | No | - | File name with extension (e.g. `report.pdf`) |
| `folder_id` | `UUID` | Yes | `NULL` | Foreign Key -> `folders.id` (`ON DELETE SET NULL`), `NULL` = Root |
| `owner_id` | `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE RESTRICT`) |
| `mime_type` | `VARCHAR(127)` | No | - | MIME format (e.g. `application/pdf`, `image/png`) |
| `size_bytes` | `BIGINT` | No | `0` | Size of current version in bytes |
| `storage_path` | `VARCHAR(1024)` | No | - | Object key path in Supabase Storage bucket |
| `is_deleted` | `BOOLEAN` | No | `FALSE` | Soft-delete flag (Trash) |
| `deleted_at` | `TIMESTAMPTZ` | Yes | `NULL` | Timestamp when moved to Trash |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update timestamp |

- **Indexes & Constraints**:
  - `idx_files_owner_folder` ON (`owner_id`, `folder_id`, `is_deleted`)
  - `idx_files_name` ON (`name`)
  - `idx_files_mime_type` ON (`mime_type`)
  - `idx_files_is_deleted` ON (`is_deleted`, `deleted_at`)
- **Relationships**:
  - `owner`: Many-to-1 with `User`
  - `folder`: Many-to-1 with `Folder`
  - `versions`: 1-to-Many with `FileVersion` (`file_id`, `ON DELETE CASCADE`)
  - `shares`: 1-to-Many with `Share` (`file_id`)
  - `link_shares`: 1-to-Many with `LinkShare` (`file_id`)
  - `stars`: 1-to-Many with `Star` (`file_id`)

---

### 2.4 Table: `file_versions`
Maintains a log of file revisions. Each file starts at version 1.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `file_id` | `UUID` | No | - | Foreign Key -> `files.id` (`ON DELETE CASCADE`) |
| `version_number`| `INTEGER` | No | `1` | Sequential version index for the file |
| `storage_path` | `VARCHAR(1024)` | No | - | Unique storage object key for this version |
| `size_bytes` | `BIGINT` | No | - | Version byte count |
| `mime_type` | `VARCHAR(127)` | No | - | Version MIME format |
| `checksum_sha256`| `VARCHAR(64)` | Yes | `NULL` | SHA-256 hash for data integrity |
| `uploaded_by_id`| `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE RESTRICT`) |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |

- **Indexes & Constraints**:
  - `idx_file_versions_file_ver` ON (`file_id`, `version_number`) UNIQUE
  - `idx_file_versions_uploaded_by` ON (`uploaded_by_id`)

---

### 2.5 Table: `shares`
Direct user-to-user item sharing with granular permission levels.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `granter_id` | `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE RESTRICT`) |
| `grantee_id` | `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE CASCADE`) |
| `file_id` | `UUID` | Yes | `NULL` | Foreign Key -> `files.id` (`ON DELETE CASCADE`) |
| `folder_id` | `UUID` | Yes | `NULL` | Foreign Key -> `folders.id` (`ON DELETE CASCADE`) |
| `role` | `VARCHAR(20)` | No | - | Enum: `VIEWER`, `EDITOR` |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update timestamp |

- **Check Constraints**:
  - `chk_shares_target`: Exactly one of `file_id` or `folder_id` must be non-null: `(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)`
- **Unique Indexes**:
  - Partial unique index on `(grantee_id, file_id)` where `file_id IS NOT NULL`
  - Partial unique index on `(grantee_id, folder_id)` where `folder_id IS NOT NULL`
- **Relationships**:
  - `granter`: Many-to-1 with `User`
  - `grantee`: Many-to-1 with `User`
  - `file`: Many-to-1 with `File`
  - `folder`: Many-to-1 with `Folder`

---

### 2.6 Table: `link_shares`
Public shareable URL tokens for external or unrestricted access.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `token` | `VARCHAR(64)` | No | - | **Unique**, URL-safe random token string |
| `created_by_id` | `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE RESTRICT`) |
| `file_id` | `UUID` | Yes | `NULL` | Foreign Key -> `files.id` (`ON DELETE CASCADE`) |
| `folder_id` | `UUID` | Yes | `NULL` | Foreign Key -> `folders.id` (`ON DELETE CASCADE`) |
| `role` | `VARCHAR(20)` | No | `'VIEWER'` | Enum: `VIEWER`, `EDITOR` |
| `password_hash` | `VARCHAR(255)` | Yes | `NULL` | Optional bcrypt hash if protected |
| `expires_at` | `TIMESTAMPTZ` | Yes | `NULL` | Optional link expiry date |
| `is_active` | `BOOLEAN` | No | `TRUE` | Enable/disable link toggle |
| `access_count` | `INTEGER` | No | `0` | Number of times link has been opened |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Last update timestamp |

- **Check Constraints**:
  - `chk_link_shares_target`: `(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)`
- **Indexes**:
  - `idx_link_shares_token` ON (`token`) UNIQUE
  - `idx_link_shares_file` ON (`file_id`)
  - `idx_link_shares_folder` ON (`folder_id`)

---

### 2.7 Table: `stars`
User-specific favorites/starred items.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `user_id` | `UUID` | No | - | Foreign Key -> `users.id` (`ON DELETE CASCADE`) |
| `file_id` | `UUID` | Yes | `NULL` | Foreign Key -> `files.id` (`ON DELETE CASCADE`) |
| `folder_id` | `UUID` | Yes | `NULL` | Foreign Key -> `folders.id` (`ON DELETE CASCADE`) |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Creation timestamp |

- **Check Constraints**:
  - `chk_stars_target`: `(file_id IS NOT NULL AND folder_id IS NULL) OR (file_id IS NULL AND folder_id IS NOT NULL)`
- **Unique Indexes**:
  - Partial unique index on `(user_id, file_id)` where `file_id IS NOT NULL`
  - Partial unique index on `(user_id, folder_id)` where `folder_id IS NOT NULL`

---

### 2.8 Table: `activities`
Audit log tracking user actions and resource modifications.

| Column | Type | Nullable | Default | Constraints & Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `uuid4()` | **Primary Key** |
| `user_id` | `UUID` | Yes | `NULL` | Foreign Key -> `users.id` (`ON DELETE SET NULL`) |
| `action` | `VARCHAR(50)` | No | - | Action type (e.g. `FILE_UPLOAD`, `FILE_DELETE`, `FOLDER_CREATE`, `SHARE_ADD`) |
| `resource_type` | `VARCHAR(20)` | No | - | Target type: `FILE`, `FOLDER`, `SHARE` |
| `resource_id` | `UUID` | No | - | UUID of the targeted entity |
| `details` | `JSONB` | Yes | `NULL` | Action context (old/new names, share recipient, etc.) |
| `ip_address` | `VARCHAR(45)` | Yes | `NULL` | Client IP address for security audits |
| `created_at` | `TIMESTAMPTZ` | No | `CURRENT_TIMESTAMP` | Event timestamp |

- **Indexes**:
  - `idx_activities_user_id` ON (`user_id`)
  - `idx_activities_resource` ON (`resource_type`, `resource_id`)
  - `idx_activities_created_at` ON (`created_at` DESC)
