import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, Loader2 } from 'lucide-react';
import { api } from '../lib/api';

interface UploadZoneProps {
  catId: string;
  onUploadComplete: (reportId: string) => void;
}

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'analyzing' | 'complete' | 'error';
  error?: string;
  reportId?: string;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ catId, onUploadComplete }) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const newFiles: UploadingFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      progress: 0,
      status: 'uploading'
    }));
    
    setUploadingFiles(prev => [...prev, ...newFiles]);

    for (const uploadingFile of newFiles) {
      try {
        // Step 1: Upload file
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id ? { ...f, progress: 30 } : f
        ));

        const formData = new FormData();
        formData.append('file', uploadingFile.file);
        
        const uploadRes = await api.post('/uploads/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id ? { ...f, progress: 60, status: 'analyzing' } : f
        ));

        // Step 2: Analyze and create report
        const { file_path, file_name, mime_type, file_size } = uploadRes.data;
        
        const analyzeRes = await api.post('/reports/analyze', null, {
          params: {
            cat_id: catId,
            file_path,
            file_name,
            mime_type,
            file_size
          }
        });

        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id ? { 
            ...f, 
            progress: 100, 
            status: 'complete',
            reportId: analyzeRes.data.id
          } : f
        ));

        onUploadComplete(analyzeRes.data.id);

      } catch (error: any) {
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id ? { 
            ...f, 
            status: 'error',
            error: error.response?.data?.detail || '上传失败'
          } : f
        ));
      }
    }
  }, [catId, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'application/pdf': ['.pdf']
    },
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  const removeFile = (id: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== id));
  };

  const getStatusIcon = (status: UploadingFile['status']) => {
    switch (status) {
      case 'uploading':
      case 'analyzing':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
      case 'complete':
        return <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
          <span className="text-white text-xs">✓</span>
        </div>;
      case 'error':
        return <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
          <span className="text-white text-xs">!</span>
        </div>;
    }
  };

  const getStatusText = (file: UploadingFile) => {
    switch (file.status) {
      case 'uploading':
        return '上传中...';
      case 'analyzing':
        return 'AI 分析中...';
      case 'complete':
        return '完成';
      case 'error':
        return file.error || '失败';
    }
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-blue-300 hover:border-blue-400 hover:bg-blue-50/50'
          }
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-blue-500" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          {isDragActive ? '松开以上传文件' : '拖拽文件到这里，或点击选择'}
        </p>
        <p className="text-sm text-gray-500">
          支持 PDF、JPG、PNG 格式，单个文件不超过 10MB
        </p>
        <div className="flex justify-center gap-2 mt-4">
          {['血常规', '生化全项', '尿检报告'].map(tag => (
            <span key={tag} className="px-3 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map(file => (
            <div key={file.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <File className="w-5 h-5 text-gray-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {file.file.name}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusIcon(file.status)}
                  <span className="text-xs text-gray-500">{getStatusText(file)}</span>
                </div>
                {(file.status === 'uploading' || file.status === 'analyzing') && (
                  <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
              </div>
              <button
                onClick={() => removeFile(file.id)}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};