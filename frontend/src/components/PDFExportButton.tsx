import { useState } from 'react';
import { Download } from 'lucide-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

interface Props {
  targetRef: React.RefObject<HTMLDivElement | null>;
  fileName?: string;
}

export default function PDFExportButton({ targetRef, fileName = 'health-report.pdf' }: Props) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!targetRef.current) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(targetRef.current, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(fileName);
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('导出失败，请重试');
    } finally {
      setExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className="flex items-center gap-1 bg-gray-800 text-white px-3 py-1.5 rounded-lg hover:bg-gray-700 disabled:opacity-50"
    >
      <Download size={16} />
      {exporting ? '导出中...' : '导出 PDF'}
    </button>
  );
}
