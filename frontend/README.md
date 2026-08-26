# Cloud Storage Service - Frontend

## Overview

The frontend will be implemented in **Week 2 (Day 8+)** using:

- **Framework**: React 18+ with [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **State & Server Cache**: [TanStack Query](https://tanstack.com/query)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **File Uploads**: [React Dropzone](https://react-dropzone.js.org/)
- **Icons**: Lucide React / Heroicons

---

## Planned Architecture & UX (Week 2 Preview)

```
frontend/
├── src/
│   ├── components/         # Shared UI components (Modals, Dropzone, Buttons, Navbar)
│   ├── pages/              # Views (Dashboard, Shared, Starred, Trash, Auth)
│   ├── services/           # Axios API service clients
│   ├── hooks/              # Custom React hooks (useAuth, useFiles, useFolders)
│   ├── context/            # Global context (AuthContext, ThemeContext)
│   ├── styles/             # Tailwind & CSS custom stylesheets
│   ├── App.jsx             # Root routing and provider hierarchy
│   └── main.jsx            # DOM mount entrypoint
├── index.html
├── tailwind.config.js
├── vite.config.js
└── package.json
```

---

## Core UX Features
1. **Google Drive-style Layout**: Collapsible sidebar with navigation to *My Drive*, *Shared with Me*, *Starred*, and *Trash*.
2. **File Explorer**: Grid view and List view with sorting by name, date modified, and file size.
3. **Breadcrumbs**: Hierarchical folder path traversal with instant click navigation.
4. **Drag & Drop Uploading**: React Dropzone zone overlaying the main view with progress indicator.
5. **Share Dialog**: Granular email sharing (Viewer/Editor) and tokenized public link generator with optional password/expiry.
6. **Trash & Restore**: Dedicated Trash view with restore and purge actions.
