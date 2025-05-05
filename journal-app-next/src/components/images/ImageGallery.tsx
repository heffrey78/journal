import React, { useEffect, useState, useImperativeHandle, forwardRef } from 'react';
import Image from 'next/image';
import { imagesApi, ImageMetadata } from '@/lib/api';

interface ImageGalleryProps {
  entryId?: string;
  onImageSelect?: (image: ImageMetadata) => void;
  onImageDelete?: (imageId: string) => void;
}

export interface ImageGalleryHandle {
  refreshImages: () => Promise<void>;
}

const ImageGallery = forwardRef<ImageGalleryHandle, ImageGalleryProps>(({
  entryId,
  onImageSelect,
  onImageDelete
}, ref) => {
  const [images, setImages] = useState<ImageMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingErrors, setLoadingErrors] = useState<Record<string, boolean>>({});

  const loadImages = async () => {
    if (!entryId) return;

    setIsLoading(true);
    setError(null);

    try {
      const entryImages = await imagesApi.getEntryImages(entryId);
      setImages(entryImages);
    } catch (err) {
      console.error('Error loading images:', err);
      setError('Failed to load images. The server may not be running.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadOrphanedImages = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const orphanedImages = await imagesApi.getOrphanedImages();
      setImages(orphanedImages);
    } catch (err) {
      console.error('Error loading orphaned images:', err);
      setError('Failed to load images. The server may not be running.');
    } finally {
      setIsLoading(false);
    }
  };

  // Expose the refresh method via ref
  useImperativeHandle(ref, () => ({
    refreshImages: async () => {
      if (entryId) {
        await loadImages();
      } else {
        await loadOrphanedImages();
      }
    }
  }));

  useEffect(() => {
    if (entryId) {
      loadImages();
    } else {
      // Load orphaned images if no entry ID is provided
      loadOrphanedImages();
    }
  }, [entryId]);

  const handleDeleteImage = async (imageId: string) => {
    if (!confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      await imagesApi.deleteImage(imageId);
      setImages(images.filter(img => img.id !== imageId));

      if (onImageDelete) {
        onImageDelete(imageId);
      }
    } catch (err) {
      console.error('Error deleting image:', err);
      setError('Failed to delete image.');
    }
  };

  const handleImageError = (imageId: string) => {
    setLoadingErrors(prev => ({ ...prev, [imageId]: true }));
  };

  if (isLoading) {
    return (
      <div className="p-4 text-center">
        <p className="text-gray-500 dark:text-gray-400">Loading images...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-500 dark:text-red-400">{error}</p>
        <button
          onClick={() => entryId ? loadImages() : loadOrphanedImages()}
          className="mt-2 px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="p-4 text-center border border-gray-200 dark:border-gray-700 rounded-lg">
        <p className="text-gray-500 dark:text-gray-400">No images available</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      {images.map(image => (
        <div
          key={image.id}
          className="relative group border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
        >
          <div className="aspect-square relative bg-gray-100 dark:bg-gray-800">
            {loadingErrors[image.id] ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center px-2">
                  Image could not be loaded
                </p>
              </div>
            ) : (
              <img
                src={image.url || `/images/${image.id}`}
                alt={image.description || image.filename}
                className="object-cover w-full h-full"
                onError={() => handleImageError(image.id)}
              />
            )}
          </div>

          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-all duration-200 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100">
            <button
              onClick={() => onImageSelect && onImageSelect(image)}
              className="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded-md text-sm mb-2"
            >
              Insert
            </button>
            <button
              onClick={() => handleDeleteImage(image.id)}
              className="bg-red-500 hover:bg-red-600 text-white py-1 px-3 rounded-md text-sm"
            >
              Delete
            </button>
          </div>

          <div className="p-2 text-xs truncate">
            {image.filename}
          </div>
        </div>
      ))}
    </div>
  );
});

export default ImageGallery;
