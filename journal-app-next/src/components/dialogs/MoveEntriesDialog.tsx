import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { FolderIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { organizationApi } from '@/lib/api';

interface MoveEntriesDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onMove: (destinationFolder: string | null) => Promise<void>;
  entryCount: number;
  currentFolder?: string;
}

export default function MoveEntriesDialog({
  isOpen,
  onClose,
  onMove,
  entryCount,
  currentFolder
}: MoveEntriesDialogProps) {
  const [folders, setFolders] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  // Fetch available folders
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        setLoading(true);
        const folderList = await organizationApi.getFolders();
        // Filter out the current folder
        const filteredFolders = currentFolder
          ? folderList.filter(folder => folder !== currentFolder)
          : folderList;
        setFolders(filteredFolders);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch folders:', err);
        setError('Failed to load folders. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      fetchFolders();
      // Reset selection when dialog opens
      setSelectedFolder(null);
      setError(null);
    }
  }, [isOpen, currentFolder]);

  // Handle move action
  const handleMove = async () => {
    try {
      setProcessing(true);
      await onMove(selectedFolder);
      onClose();
    } catch (err) {
      console.error('Failed to move entries:', err);
      setError('Failed to move entries. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  // Handle remove from folder option (move to no folder)
  const handleRemoveFromFolder = async () => {
    try {
      setProcessing(true);
      await onMove(null); // null means no folder
      onClose();
    } catch (err) {
      console.error('Failed to remove entries from folder:', err);
      setError('Failed to remove entries from folder. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-card p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="h3"
                  className="text-lg font-medium leading-6 text-card-foreground flex justify-between items-center"
                >
                  <span>Move {entryCount} {entryCount === 1 ? 'Entry' : 'Entries'}</span>
                  <button
                    type="button"
                    className="text-muted-foreground hover:text-foreground"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </Dialog.Title>

                <div className="mt-4">
                  <p className="text-sm text-muted-foreground">
                    Choose a destination folder for your {entryCount === 1 ? 'entry' : 'entries'}.
                  </p>
                </div>

                {error && (
                  <div className="mt-4 bg-destructive/10 border border-destructive/30 p-3 rounded-md">
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}

                <div className="mt-4 max-h-60 overflow-y-auto">
                  {loading ? (
                    <div className="flex justify-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    </div>
                  ) : folders.length === 0 ? (
                    <p className="text-sm text-muted-foreground py-4 text-center">
                      No other folders available.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {folders.map((folder) => (
                        <div
                          key={folder}
                          onClick={() => setSelectedFolder(folder)}
                          className={`flex items-center p-3 rounded-md cursor-pointer ${
                            selectedFolder === folder
                              ? 'bg-primary/10 border border-primary/20'
                              : 'hover:bg-accent/50'
                          }`}
                        >
                          <FolderIcon className="h-5 w-5 text-muted-foreground mr-2" />
                          <span className="text-card-foreground">{folder}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="mt-6 flex flex-col space-y-3 sm:flex-row sm:justify-between sm:space-y-0 sm:space-x-4">
                  <button
                    type="button"
                    className="inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-destructive-foreground bg-destructive/90 border border-transparent rounded-md hover:bg-destructive focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-destructive"
                    onClick={handleRemoveFromFolder}
                    disabled={processing || !currentFolder}
                  >
                    {processing ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-destructive-foreground mr-2"></div>
                    ) : null}
                    Remove from Folder
                  </button>

                  <button
                    type="button"
                    className="inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-primary-foreground bg-primary border border-transparent rounded-md hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary"
                    onClick={handleMove}
                    disabled={processing || !selectedFolder}
                  >
                    {processing ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground mr-2"></div>
                    ) : null}
                    Move
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
