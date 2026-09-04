import React, { useState } from 'react';
import { Outlet, useNavigate, useSearchParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import CreateFolderModal from '../modals/CreateFolderModal';
import FileUploadModal from '../modals/FileUploadModal';

export const AppLayout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isNewFolderOpen, setIsNewFolderOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const currentFolderId = searchParams.get('folder') || null;

  const handleActionSuccess = () => {
    queryClient.invalidateQueries();

    window.dispatchEvent(new Event('drive-refresh'));
  };

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-white">

      <Navbar onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />

      <div className="flex flex-1 overflow-hidden">

        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          onNewFolder={() => setIsNewFolderOpen(true)}
          onUploadFile={() => setIsUploadOpen(true)}
        />

        <main className="flex-1 overflow-y-auto bg-surface-light p-4 md:p-6">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>

      <CreateFolderModal
        isOpen={isNewFolderOpen}
        onClose={() => setIsNewFolderOpen(false)}
        parentId={currentFolderId}
        onSuccess={handleActionSuccess}
      />

      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        folderId={currentFolderId}
        onSuccess={handleActionSuccess}
      />
    </div>
  );
};

export default AppLayout;
