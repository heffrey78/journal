import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { imagesApi, ImageMetadata } from '@/lib/api';

interface ImageUploaderProps {
  entryId?: string;
  onImageUploaded?: (image: ImageMetadata) => void;
  onError?: (error: Error) => void;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({
  entryId,
  onImageUploaded,
  onError
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    // Process each file
    for (const file of acceptedFiles) {
      try {
        setIsUploading(true);
        setUploadProgress(0);

        // Create a fake progress simulation (since we don't have real progress events from the API)
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            const newProgress = prev + Math.random() * 15;
            return newProgress >= 90 ? 90 : newProgress; // Cap at 90% until complete
          });
        }, 300);

        // Upload the image
        const uploadedImage = await imagesApi.uploadImage(file, entryId);

        // Clear the interval and set progress to 100%
        clearInterval(progressInterval);
        setUploadProgress(100);

        // Notify parent component about the uploaded image
        if (onImageUploaded) {
          onImageUploaded(uploadedImage);
        }

        // Reset progress after a short delay
        setTimeout(() => {
          setIsUploading(false);
          setUploadProgress(0);
        }, 1000);
      } catch (error) {
        console.error('Error uploading image:', error);
        setIsUploading(false);
        setUploadProgress(0);

        if (onError && error instanceof Error) {
          onError(error);
        }
      }
    }
  }, [entryId, onImageUploaded, onError]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp']
    },
    multiple: true
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}
          ${isDragReject ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : ''}
          hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/10
        `}
      >
        <input {...getInputProps()} />

        {isDragActive ? (
          <p className="text-blue-500 dark:text-blue-300">Drop the images here...</p>
        ) : (
          <div className="space-y-2">
            <p className="text-gray-600 dark:text-gray-300">
              Drag & drop images here, or click to select files
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Supported formats: JPG, PNG, GIF, WEBP
            </p>
          </div>
        )}

        {isDragReject && (
          <p className="text-red-500 dark:text-red-300 mt-2">
            Some files are not supported. Please upload only images.
          </p>
        )}
      </div>

      {isUploading && (
        <div className="mt-4">
          <div className="flex items-center">
            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {Math.round(uploadProgress)}%
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Uploading image...
          </p>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
