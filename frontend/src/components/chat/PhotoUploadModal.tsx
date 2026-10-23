import React, { useState } from 'react';
import { Camera, UploadCloud, X, CheckCircle2, AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';
import { api } from '../../services/api';
import { PhotoAnalysisResult } from '../../types';
import { useToast } from '../../context/ToastContext';

interface PhotoUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalysisComplete: (result: PhotoAnalysisResult) => void;
}

export const PhotoUploadModal: React.FC<PhotoUploadModalProps> = ({
  isOpen,
  onClose,
  onAnalysisComplete,
}) => {
  const { showToast } = useToast();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [analysis, setAnalysis] = useState<PhotoAnalysisResult | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      showToast('Please select a valid image (JPEG, PNG, WebP)', 'error');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      showToast('Image size exceeds 5MB limit', 'error');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setAnalysis(null);
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    try {
      const result = await api.uploadDefectPhoto(selectedFile, notes.trim());
      setAnalysis(result);
      showToast('Visual defect analysis complete!', 'success');
      onAnalysisComplete(result);
    } catch (err: any) {
      showToast(err.message || 'Failed to analyze uploaded photo', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setNotes('');
    setAnalysis(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-brand-50 text-brand-600">
              <Camera className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Product Photo Defect Analysis</h3>
              <p className="text-xs text-slate-500">
                Upload image evidence of physical transit damage or wrong item
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1 text-xs">
          {!previewUrl ? (
            <label className="border-2 border-dashed border-slate-200 hover:border-brand-500 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-brand-50/20">
              <UploadCloud className="h-10 w-10 text-slate-400 mb-2" />
              <span className="font-semibold text-slate-800 text-sm">Click or Drag to Upload Photo</span>
              <span className="text-slate-400 text-xs mt-1">JPEG, PNG, or WebP (Max 5MB)</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          ) : (
            <div className="space-y-3">
              <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-100 aspect-video flex items-center justify-center">
                <img
                  src={previewUrl}
                  alt="Product preview"
                  className="max-h-full max-w-full object-contain"
                />
                <button
                  type="button"
                  onClick={handleReset}
                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-slate-900/70 text-white hover:bg-slate-900 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div>
                <label className="block font-medium text-slate-700 text-xs mb-1">
                  Describe the observed defect (optional):
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Broken screen, crack on left hinge, wrong color"
                  className="w-full text-xs rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              {!analysis && (
                <button
                  type="button"
                  onClick={handleUploadAndAnalyze}
                  disabled={isUploading}
                  className="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isUploading ? (
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Inspect Photo with Vision Engine</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              )}
            </div>
          )}

          {/* Analysis Result Card */}
          {analysis && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-brand-600" />
                  <span className="font-bold text-slate-900">Visual Inspection Summary</span>
                </div>
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                  {Math.round(analysis.confidence_score * 100)}% Confidence
                </span>
              </div>

              <p className="text-slate-700 leading-relaxed">{analysis.summary}</p>

              {analysis.visible_evidence && analysis.visible_evidence.length > 0 && (
                <div className="space-y-1">
                  {analysis.visible_evidence.map((ev, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-slate-600">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
                      <span>{ev}</span>
                    </div>
                  ))}
                </div>
              )}

              {analysis.requires_human_review && (
                <div className="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 p-2.5 text-amber-800 text-[11px]">
                  <AlertTriangle className="h-4 w-4 flex-shrink-0 text-amber-600" />
                  <span>Ambiguous defect routed to human specialist for final approval.</span>
                </div>
              )}

              <p className="text-[10px] text-slate-400 italic leading-snug">
                {analysis.disclaimer}
              </p>

              <button
                type="button"
                onClick={onClose}
                className="w-full py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs transition-colors"
              >
                Apply Evidence to Chat
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
