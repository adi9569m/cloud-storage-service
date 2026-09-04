# Cloud Storage Service - Frontend

Production-ready React 18 Single Page Application (SPA) providing a modern, Google Drive-style user experience with drag-and-drop file management, rich modals, security controls, and responsive styling.

---

## 🚀 Tech Stack

- **Framework**: React 18+ bootstrapped with [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with custom drive color palette and animations
- **Routing**: [React Router DOM v6](https://reactrouter.com/) with protected layouts
- **Server Cache & State**: [TanStack Query v5](https://tanstack.com/query)
- **HTTP Client**: [Axios](https://axios-http.com/) with token interceptors and automatic session handling
- **File Uploads**: [React Dropzone](https://react-dropzone.js.org/)
- **Icons**: [Lucide React](https://lucide.dev/)

---

## 📂 Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── common/              # ProtectedRoute, ToastContainer
│   │   ├── drive/               # FileItem, FolderItem, Breadcrumbs, ContextMenu, ViewSwitcher, BatchActionBar
│   │   ├── layout/              # AppLayout, Navbar, Sidebar
│   │   └── modals/              # CreateFolderModal, FileUploadModal, FilePreviewModal, ShareModal,
│   │                            # FileVersionModal, FileCommentsDrawer, TagManagerModal, MoveCopyModal, RenameModal
│   ├── context/                 # AuthContext, ToastContext
│   ├── hooks/                   # useAuth, useToast
│   ├── pages/
│   │   ├── auth/                # LoginPage, RegisterPage
│   │   ├── DashboardPage.jsx    # My Drive root / folder explorer
│   │   ├── RecentPage.jsx       # Chronological recent files feed
│   │   ├── SharedPage.jsx       # Items shared with user
│   │   ├── StarredPage.jsx      # Starred/favorite files & folders
│   │   ├── TrashPage.jsx        # Trash bin with restore & empty actions
│   │   ├── TagsPage.jsx         # Tag management & tagged items explorer
│   │   ├── ActivityPage.jsx     # User audit logs and event timeline
│   │   ├── StoragePage.jsx      # Storage quota meter & category breakdown
│   │   ├── SettingsPage.jsx     # Profile, Security, Storage & System Maintenance Hub
│   │   ├── SearchPage.jsx       # Advanced file/folder query & filter page
│   │   ├── PublicSharePage.jsx  # Unauthenticated public link viewer & downloader
│   │   └── NotFoundPage.jsx     # 404 Fallback view
│   ├── services/                # Axios API services (auth, file, folder, share, star, trash, tag, comment, activity, maintenance, storage)
│   ├── styles/                  # Tailwind custom CSS styles
│   ├── utils/                   # formatters.js (byte sizes, dates, file icons)
│   ├── App.jsx                  # Root router, query & toast provider tree
│   └── main.jsx                 # DOM mount entrypoint
├── nginx.conf                   # Production Nginx reverse proxy configuration
├── Dockerfile                   # Multi-stage production container build
├── tailwind.config.js           # Tailwind theme configuration
├── vite.config.js               # Vite build configuration
└── package.json                 # Dependency definitions
```

---

## 💻 Development & Build Scripts

```bash
# Install dependencies
npm install

# Start local Vite development server (with HMR)
npm run dev

# Compile optimized production bundle
npm run build

# Preview production build locally
npm run preview
```
