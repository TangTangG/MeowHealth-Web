import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image } from 'lucide-react';

interface UploadZoneProps {
  onUpload: (files: File[]) => void;
  uploading?: boolean;
}

export default function UploadZone({ onUpload, uploading }: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onUpload(acceptedFiles);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      
      <div className="flex justify-center gap-4 mb-4">
        <FileText size={32} className="text-red-500" />
        <Image size={32} className="text-blue-500" />
      </div>
      
      {uploading ? (
        <p className="text-gray-500">上传中...</p>
      ) : isDragActive ? (
        <p className="text-blue-600">拖放文件到这里</p>
      ) : (
        <>
          <p className="text-gray-600 mb-2">
            拖拽文件到这里，或 <span className="text-blue-600">点击选择</span>
          </p>
          <p className="text-sm text-gray-400">
            支持 PDF、JPG、PNG，最大 10MB
          </p>
        </>
      )}
    </div>
  );
}
