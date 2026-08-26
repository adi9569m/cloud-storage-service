# Entity Relationship Diagram (ERD)

Below is the complete Mermaid Entity Relationship Diagram for the Cloud Storage Service database schema.

```mermaid
erDiagram
    users ||--o{ folders : "owns"
    users ||--o{ files : "owns"
    users ||--o{ file_versions : "uploads"
    users ||--o{ shares : "grants (granter)"
    users ||--o{ shares : "receives (grantee)"
    users ||--o{ link_shares : "creates"
    users ||--o{ stars : "stars"
    users ||--o{ activities : "performs"

    folders ||--o{ folders : "contains (subfolders)"
    folders ||--o{ files : "contains"
    folders ||--o{ shares : "shared via"
    folders ||--o{ link_shares : "public link"
    folders ||--o{ stars : "starred"

    files ||--o{ file_versions : "has versions"
    files ||--o{ shares : "shared via"
    files ||--o{ link_shares : "public link"
    files ||--o{ stars : "starred"

    users {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar full_name
        varchar avatar_url
        boolean is_active
        boolean is_verified
        bigint storage_used_bytes
        timestamptz created_at
        timestamptz updated_at
    }

    folders {
        uuid id PK
        varchar name
        uuid parent_id FK
        uuid owner_id FK
        varchar color
        boolean is_deleted
        timestamptz deleted_at
        timestamptz created_at
        timestamptz updated_at
    }

    files {
        uuid id PK
        varchar name
        uuid folder_id FK
        uuid owner_id FK
        varchar mime_type
        bigint size_bytes
        varchar storage_path
        boolean is_deleted
        timestamptz deleted_at
        timestamptz created_at
        timestamptz updated_at
    }

    file_versions {
        uuid id PK
        uuid file_id FK
        integer version_number
        varchar storage_path
        bigint size_bytes
        varchar mime_type
        varchar checksum_sha256
        uuid uploaded_by_id FK
        timestamptz created_at
    }

    shares {
        uuid id PK
        uuid granter_id FK
        uuid grantee_id FK
        uuid file_id FK
        uuid folder_id FK
        varchar role
        timestamptz created_at
        timestamptz updated_at
    }

    link_shares {
        uuid id PK
        varchar token UK
        uuid created_by_id FK
        uuid file_id FK
        uuid folder_id FK
        varchar role
        varchar password_hash
        timestamptz expires_at
        boolean is_active
        integer access_count
        timestamptz created_at
        timestamptz updated_at
    }

    stars {
        uuid id PK
        uuid user_id FK
        uuid file_id FK
        uuid folder_id FK
        timestamptz created_at
    }

    activities {
        uuid id PK
        uuid user_id FK
        varchar action
        varchar resource_type
        uuid resource_id
        jsonb details
        varchar ip_address
        timestamptz created_at
    }
```

---

## Relationship Summary Table

| Relationship | Cardinality | Parent Entity | Child Entity | Description / Cascade Policy |
| :--- | :--- | :--- | :--- | :--- |
| User -> Folders | 1 : N | `users` | `folders` | User owns folders (`ON DELETE RESTRICT` for safety) |
| User -> Files | 1 : N | `users` | `files` | User owns files (`ON DELETE RESTRICT` for safety) |
| Folder -> Subfolders | 1 : N | `folders` | `folders` | Recursive folder nesting (`ON DELETE RESTRICT`) |
| Folder -> Files | 1 : N | `folders` | `files` | Folder contains files (`ON DELETE SET NULL` on hard folder delete) |
| File -> Versions | 1 : N | `files` | `file_versions` | File has historic/current versions (`ON DELETE CASCADE`) |
| User -> Shares | 1 : N | `users` | `shares` | User grants or receives item shares |
| File/Folder -> Shares | 1 : N | `files`/`folders` | `shares` | Shared file/folder (`ON DELETE CASCADE`) |
| File/Folder -> Links | 1 : N | `files`/`folders` | `link_shares` | Public shareable links (`ON DELETE CASCADE`) |
| User -> Stars | 1 : N | `users` | `stars` | Starred files/folders (`ON DELETE CASCADE`) |
| User -> Activities | 1 : N | `users` | `activities` | Activity audit trail (`ON DELETE SET NULL`) |
