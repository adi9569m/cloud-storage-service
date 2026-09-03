/**
 * Collaboration and public share link generator modal.
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Share2,
  Link2,
  Users,
  Copy,
  Check,
  Trash2,
  Lock,
  Clock,
  Shield,
  Key,
} from 'lucide-react';
import shareService from '../../services/shareService';
import linkShareService from '../../services/linkShareService';

export const ShareModal = ({ isOpen, onClose, item, isFolder = false }) => {
  const [activeTab, setActiveTab] = useState('users'); // 'users' | 'link'
  const [granteeEmail, setGranteeEmail] = useState('');
  const [role, setRole] = useState('VIEWER');
  const [collaborators, setCollaborators] = useState([]);
  const [publicLinks, setPublicLinks] = useState([]);
  const [copiedToken, setCopiedToken] = useState(null);

  // New public link states
  const [linkPassword, setLinkPassword] = useState('');
  const [hasPassword, setHasPassword] = useState(false);
  const [linkExpiryDays, setLinkExpiryDays] = useState('30');
  const [isCreatingLink, setIsCreatingLink] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (isOpen && item) {
      loadSharesAndLinks();
    }
  }, [isOpen, item]);

  if (!isOpen || !item) return null;

  const loadSharesAndLinks = async () => {
    setIsLoading(true);
    setError('');
    try {
      if (isFolder) {
        const [shares, links] = await Promise.all([
          shareService.listFolderShares(item.id),
          linkShareService.listFolderLinks(item.id),
        ]);
        setCollaborators(shares || []);
        setPublicLinks(links || []);
      } else {
        const [shares, links] = await Promise.all([
          shareService.listFileShares(item.id),
          linkShareService.listFileLinks(item.id),
        ]);
        setCollaborators(shares || []);
        setPublicLinks(links || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCollaborator = async (e) => {
    e.preventDefault();
    if (!granteeEmail.trim()) return;

    setError('');
    setSuccessMessage('');
    try {
      await shareService.createShare({
        grantee_email: granteeEmail.trim(),
        role,
        ...(isFolder ? { folder_id: item.id } : { file_id: item.id }),
      });
      setGranteeEmail('');
      setSuccessMessage('Share invite sent successfully!');
      loadSharesAndLinks();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to grant share. Verify user email.');
    }
  };

  const handleRevokeShare = async (shareId) => {
    try {
      await shareService.revokeShare(shareId);
      loadSharesAndLinks();
    } catch (err) {
      setError('Failed to revoke share permission.');
    }
  };

  const handleCreatePublicLink = async () => {
    setIsCreatingLink(true);
    setError('');
    setSuccessMessage('');

    try {
      let expiresAt = null;
      if (linkExpiryDays && linkExpiryDays !== 'never') {
        const d = new Date();
        d.setDate(d.getDate() + parseInt(linkExpiryDays, 10));
        expiresAt = d.toISOString();
      }

      await linkShareService.createLink({
        role: 'VIEWER',
        password: hasPassword && linkPassword.trim() ? linkPassword.trim() : null,
        expires_at: expiresAt,
        ...(isFolder ? { folder_id: item.id } : { file_id: item.id }),
      });

      setLinkPassword('');
      setHasPassword(false);
      setSuccessMessage('Public share link generated!');
      loadSharesAndLinks();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate public share link.');
    } finally {
      setIsCreatingLink(false);
    }
  };

  const handleRevokePublicLink = async (linkId) => {
    try {
      await linkShareService.revokeLink(linkId);
      loadSharesAndLinks();
    } catch (err) {
      setError('Failed to revoke public link.');
    }
  };

  const handleCopyLink = (token) => {
    const fullUrl = `${window.location.origin}/share/${token}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-modal transition-all animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-drive-50 text-drive-600">
              <Share2 className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-800">
                Share "{item.name}"
              </h3>
              <p className="text-xs text-slate-500">Manage permissions and public access</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="mt-4 flex border-b border-slate-100">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors ${
              activeTab === 'users'
                ? 'border-drive-600 text-drive-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Collaborators ({collaborators.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('link')}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-xs font-semibold transition-colors ${
              activeTab === 'link'
                ? 'border-drive-600 text-drive-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Link2 className="h-4 w-4" />
            <span>Public Links ({publicLinks.length})</span>
          </button>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-600 border border-red-200">
            {error}
          </div>
        )}
        {successMessage && (
          <div className="mt-3 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-700 border border-emerald-200">
            {successMessage}
          </div>
        )}

        {/* Tab 1: Direct Collaborators */}
        {activeTab === 'users' && (
          <div className="mt-4 space-y-4">
            <form onSubmit={handleAddCollaborator} className="flex gap-2">
              <input
                type="email"
                value={granteeEmail}
                onChange={(e) => setGranteeEmail(e.target.value)}
                placeholder="Enter collaborator email..."
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-drive-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-drive-100"
              />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-drive-100"
              >
                <option value="VIEWER">Viewer</option>
                <option value="EDITOR">Editor</option>
              </select>
              <button
                type="submit"
                disabled={!granteeEmail.trim()}
                className="rounded-xl bg-drive-600 px-4 py-2 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
              >
                Invite
              </button>
            </form>

            {/* List of existing direct shares */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-700">People with access</h4>
              {collaborators.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-2">
                  No collaborators added yet. Only you have access.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white max-h-48 overflow-y-auto">
                  {collaborators.map((share) => (
                    <div
                      key={share.id}
                      className="flex items-center justify-between p-3 text-xs"
                    >
                      <div className="overflow-hidden">
                        <p className="font-semibold text-slate-800 truncate">
                          {share.grantee_email || `User ID: ${share.grantee_id}`}
                        </p>
                        <span className="inline-block mt-0.5 rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
                          {share.role}
                        </span>
                      </div>
                      <button
                        onClick={() => handleRevokeShare(share.id)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                        title="Remove Access"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Public Share Links */}
        {activeTab === 'link' && (
          <div className="mt-4 space-y-4">
            {/* Create new public link controls */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                  <Link2 className="h-4 w-4 text-drive-600" /> Generate New Share Link
                </span>
                <button
                  onClick={handleCreatePublicLink}
                  disabled={isCreatingLink}
                  className="rounded-xl bg-drive-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-drive-700 disabled:opacity-50 transition-colors shadow-sm"
                >
                  {isCreatingLink ? 'Creating...' : 'Create Link'}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Expiration
                  </label>
                  <select
                    value={linkExpiryDays}
                    onChange={(e) => setLinkExpiryDays(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none"
                  >
                    <option value="7">7 Days</option>
                    <option value="30">30 Days</option>
                    <option value="90">90 Days</option>
                    <option value="never">Never expires</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1 flex items-center gap-1">
                    <Lock className="h-3 w-3 text-slate-400" /> Password Protect
                  </label>
                  <input
                    type="password"
                    placeholder="Optional password"
                    value={linkPassword}
                    onChange={(e) => {
                      setLinkPassword(e.target.value);
                      setHasPassword(e.target.value.length > 0);
                    }}
                    className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* List of active public links */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-700">Active Public Links</h4>
              {publicLinks.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-2">
                  No public links generated yet.
                </p>
              ) : (
                <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white max-h-48 overflow-y-auto">
                  {publicLinks.map((link) => {
                    const isCopied = copiedToken === link.token;
                    return (
                      <div key={link.id} className="p-3 text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {link.is_password_protected && (
                              <span className="flex items-center gap-1 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700">
                                <Lock className="h-3 w-3" /> Password
                              </span>
                            )}
                            {link.expires_at && (
                              <span className="flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                                <Clock className="h-3 w-3" /> Expires soon
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleCopyLink(link.token)}
                              className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
                                isCopied
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : 'bg-drive-50 text-drive-700 hover:bg-drive-100'
                              }`}
                            >
                              {isCopied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                              <span>{isCopied ? 'Copied' : 'Copy'}</span>
                            </button>
                            <button
                              onClick={() => handleRevokePublicLink(link.id)}
                              className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                              title="Delete Link"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                        <div className="truncate rounded-lg bg-slate-50 p-2 font-mono text-[11px] text-slate-600">
                          {window.location.origin}/share/{link.token}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 flex justify-end border-t border-slate-100 pt-4">
          <button
            onClick={onClose}
            className="rounded-xl bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareModal;
