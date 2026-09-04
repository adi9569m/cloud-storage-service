# Cloud Storage & Media Service

A modern, cloud-native, Google Drive-style media and file storage service engineered with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **React 18**, **Tailwind CSS**, and **Docker**.

---

## 🚀 10-Day Engineering Roadmap Summary

| Phase | Description | Key Deliverables |
|---|---|---|
| **Day 1** | **MVP Architecture & Database Models** | Base entities, declarative SQLAlchemy 2.0 schemas, UUID primary keys, and async session management. |
| **Day 2** | **Authentication & User Management** | Stateless JWT authentication, argon2/bcrypt hashing, login/register flows, and user profile management. |
| **Day 3** | **Folder Hierarchy & Organization** | Recursive nested tree hierarchies, breadcrumbs traversal, circular-move prevention, and directory management. |
| **Day 4** | **File Storage & Versioning** | Presigned upload/download pipelines, binary/metadata separation, multi-version tracking, and rollback APIs. |
| **Day 5** | **Sharing, Collaboration & Trash** | User-to-user RBAC sharing (`Owner`/`Editor`/`Viewer`), tokenized public links, starred favorites, soft deletion & trash bin. |
| **Day 6** | **Search, Analytics & Batch Operations** | Faceted full-text search, storage quota calculation by MIME category, batch operations (move, delete, star), and preview streaming. |
| **Day 7** | **Tags, Comments, Maintenance & Security** | Tagging system, threaded file comments, automated background maintenance tasks, rate limiting, and security headers. |
| **Day 8** | **Frontend Application & Auth Flow** | React 18 SPA (Vite + Tailwind CSS), TanStack Query, AuthContext, Protected Routes, and responsive Google Drive layout. |
| **Day 9** | **Interactive Drive Explorer & Rich Modals** | Grid/List view explorer, drag-and-drop uploads, context menus, file previewer, version history modal, share dialogs, and public link viewer. |
| **Day 10** | **Production Readiness & Containerization** | Activity audit trail UI, Recent files view, Settings & Profile hub, system maintenance telemetry, global toast notifications, multi-stage Dockerfiles, Docker Compose, and CI/CD pipelines. |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Tier (React + Vite)"]
        UI["Single Page Application"]
        Dropzone["Drag & Drop Upload Zone"]
        Context["Auth & Toast Providers"]
    end

    subgraph ReverseProxy ["Reverse Proxy (Nginx)"]
        Nginx["Nginx Web Server (:3000 / :80)"]
    end

    subgraph Backend ["Backend API Tier (FastAPI)"]
        API["FastAPI App (:8000)"]
        AuthMid["Security & Rate Limiter"]
        Router["Routers: Auth, Files, Folders, Shares, Tags, Maintenance"]
        Service["Service Layer (Business Logic & Audit Logging)"]
    end

    subgraph Data ["Data & Storage Tier"]
        DB[("PostgreSQL 16 (Relational Metadata Store)")]
        Storage[("Object Storage (Supabase / S3-Compatible)")]
    end

    UI -- "Static Assets / REST" --> Nginx
    Nginx -- "/api/* & /health" --> API
    API --> AuthMid --> Router --> Service
    Service -- "SQLAlchemy 2.0 ORM" --> DB
    Service -- "Signed Upload / Download URLs" --> Storage
    Dropzone -. "Direct Binary Transfer via Signed URL" .-> Storage
```

---

## ⚡ Quick Start with Docker Compose

Ensure [Docker](https://www.docker.com/) and Docker Compose are installed on your system.

```bash
# 1. Clone repository
git clone https://github.com/adi9569m/cloud-storage-service.git
cd cloud-storage-service

# 2. Launch multi-container stack (Database + Backend + Frontend)
docker compose up -d --build

# 3. Access the application
# Frontend Dashboard: http://localhost:3000
# Backend OpenAPI Docs: http://localhost:8000/docs
# Backend Health Check: http://localhost:8000/health
```

---

## 🛠️ Local Development Setup

### Backend (FastAPI + Python 3.12+)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run automated test suite
pytest -v

# Start development API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React 18 + Vite + Tailwind CSS)

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev

# Build production bundle
npm run build
```

---

## 📡 REST API Route Overview

| Module | Route Prefix | Key Endpoints | Description |
|---|---|---|---|
| **Auth** | `/api/v1/auth` | `POST /register`, `POST /login`, `GET /me`, `PUT /me`, `POST /change-password` | JWT token authentication & profile management |
| **Folders** | `/api/v1/folders` | `POST /`, `GET /`, `GET /{id}/contents`, `PUT /{id}`, `DELETE /{id}`, `POST /move` | Hierarchical directory organization |
| **Files** | `/api/v1/files` | `POST /init-upload`, `POST /complete-upload`, `GET /{id}/download`, `GET /{id}/versions` | File storage, versioning, and presigned transfers |
| **Sharing** | `/api/v1/shares` | `POST /`, `GET /shared-with-me`, `PUT /{id}`, `DELETE /{id}` | User-to-user RBAC file/folder permissions |
| **Public Links** | `/api/v1/public/links` | `POST /`, `GET /{token}`, `POST /{token}/download`, `DELETE /{id}` | Tokenized public link sharing with password & expiration |
| **Stars** | `/api/v1/stars` | `POST /`, `DELETE /`, `GET /` | Favorite items management |
| **Trash** | `/api/v1/trash` | `GET /`, `POST /restore-all`, `DELETE /empty` | Soft-deleted item recovery and permanent purging |
| **Search** | `/api/v1/search` | `GET /` | Query files and folders by name, MIME type, and date |
| **Storage** | `/api/v1/storage` | `GET /summary`, `POST /recalculate` | Quota consumption metrics and category distribution |
| **Tags** | `/api/v1/tags` | `POST /`, `GET /`, `POST /assign`, `DELETE /remove` | File and folder taxonomy labeling |
| **Comments** | `/api/v1/comments` | `POST /`, `GET /file/{file_id}`, `DELETE /{id}` | Threaded discussions on files |
| **Activity** | `/api/v1/activities` | `GET /`, `GET /resource/{type}/{id}` | Comprehensive security and audit logging |
| **Maintenance** | `/api/v1/maintenance` | `POST /cleanup-trash`, `POST /cleanup-expired-links`, `POST /sync-storage`, `GET /system-status` | Automated cleanup tasks & platform telemetry |

---

## 🧪 Verification & Testing

- **Backend Pytest Suite**: 126+ unit and integration tests covering database models, security, JWT authentication, hierarchical folder logic, file versioning, public link hashing, rate limiting, and maintenance routines.
- **Frontend Build**: Zero-warning production build compiled using Vite with minification, tree-shaking, and Gzip optimization.
- **Continuous Integration**: GitHub Actions pipeline validating backend tests and frontend production builds on every pull request.

---

## 📄 License
MIT License. Developed for learning and production cloud storage architectures.
