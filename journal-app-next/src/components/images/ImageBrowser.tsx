import React, { useState, useRef } from 'react';
import ImageUploader from './ImageUploader';
import ImageGallery, { ImageGalleryHandle } from './ImageGallery';
import { ImageMetadata } from '@/lib/api';

interface ImageBrowserProps {
  entryId?: string;
  onInsertImage: (imageUrl: string) => void;
}

const ImageBrowser: React.FC<ImageBrowserProps> = ({
  entryId,
  onInsertImage
}) => {
  const [showUploader, setShowUploader] = useState(false);
  const [uploadedImage, setUploadedImage] = useState<ImageMetadata | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const galleryRef = useRef<ImageGalleryHandle>(null);

  const handleImageUploaded = (image: ImageMetadata) => {
    setUploadedImage(image);
    setErrorMessage(null);

    // Refresh the gallery to show the newly uploaded image
    if (galleryRef.current) {
      galleryRef.current.refreshImages();
    }

    // Hide uploader after successful upload
    setShowUploader(false);
  };

  const handleError = (error: Error) => {
    setErrorMessage(error.message || 'Failed to upload image.');
  };

  const handleImageSelect = (image: ImageMetadata) => {
    // Insert image into editor using markdown syntax
    // The URL will be the absolute path to the image
    if (image.url) {
      onInsertImage(image.url);
    } else {
      // Fallback to constructing URL from image ID
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      onInsertImage(`${baseUrl}/images/${image.id}`);
    }
  };

  return (
    <div className="my-4 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Images</h3>

        <button
          onClick={() => setShowUploader(!showUploader)}
          className="text-sm bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded-md flex items-center"
          type="button"
        >
          {showUploader ? 'Hide Uploader' : 'Upload Image'}
        </button>
      </div>

      {errorMessage && (
        <div className="bg-red-100 border-l-4 border-red-500 p-4 dark:bg-red-900/30">
          <p className="text-red-700 dark:text-red-300">{errorMessage}</p>
        </div>
      )}

      {showUploader && (
        <div className="mb-4">
          <ImageUploader
            entryId={entryId}
            onImageUploaded={handleImageUploaded}
            onError={handleError}
          />
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <ImageGallery
          ref={galleryRef}
          entryId={entryId}
          onImageSelect={handleImageSelect}
        />
      </div>

      <div className="text-xs text-gray-500 dark:text-gray-400">
        <p>Supported formats: JPG, PNG, GIF, WEBP</p>
        <p>Click "Insert" on an image to add it to your journal entry.</p>
      </div>
    </div>
  );
};

export default ImageBrowser;
