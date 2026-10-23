import React, { useEffect, useRef, useState } from 'react';
import {
  Sparkles,
  Send,
  Camera,
  Languages,
  Bot,
  User,
} from 'lucide-react';

import { api } from '../../services/api';
import { ChatMessage, PhotoAnalysisResult } from '../../types';
import { useToast } from '../../context/ToastContext';
import { EligibilityCard } from './EligibilityCard';
import { ResolutionCard } from './ResolutionCard';
import { OrderCard } from './OrderCard';
import { PolicyCitationCard } from './PolicyCitationCard';
import { ConfirmationCard } from './ConfirmationCard';
import { PhotoUploadModal } from './PhotoUploadModal';

interface ChatContainerProps {
  initialMessage?: string;
  onNavigateTab?: (tab: string) => void;
  isWidget?: boolean;
}

const QUICK_PROMPTS = [
  { label: '👟 Size Exchange (Hinglish)', query: 'Yaar shoes ka size chhota hai, exchange karne hain' },
  { label: '📦 Track Return Status', query: 'Can you check my return status?' },
  { label: '⚠️ Damaged Product', query: 'I received a damaged, cracked product' },
  { label: '📜 Explain Return Policy (Hindi)', query: 'मुझे रिटर्न और रिफंड पॉलिसी समझाइए' },
];

export const ChatContainer: React.FC<ChatContainerProps> = ({
  initialMessage = '',
  onNavigateTab,
  isWidget = false,
}) => {
  const { showToast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState(initialMessage);
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState<'auto' | 'en' | 'hi' | 'hinglish'>('auto');
  const [isPhotoModalOpen, setIsPhotoModalOpen] = useState(false);
  const [sessionId] = useState(() => `session-${Math.random().toString(36).substring(2, 9)}`);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Initial greeting
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome-msg',
          role: 'assistant',
          content:
            "Hello! I am your ReturnPilot AI assistant. I can help you check return or exchange eligibility, " +
            "explain store policies, resolve size issues, or track existing returns in English, Hindi, or Hinglish. " +
            "How can I help you today?",
          timestamp: new Date().toISOString(),
          language: 'en',
        },
      ]);
    }
  }, []);

  const handleSend = async (messageText?: string, orderNumberOverride?: string, skuOverride?: string) => {
    const textToSend = (messageText || inputMessage).trim();
    if (!textToSend && !orderNumberOverride) return;

    setInputMessage('');

    // Append user message to UI
    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: textToSend || `Checking item ${skuOverride} in order ${orderNumberOverride}`,
      timestamp: new Date().toISOString(),
      language: language === 'auto' ? 'en' : language,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage({
        message: textToSend,
        session_id: sessionId,
        preferred_language: language,
        order_number: orderNumberOverride,
        sku: skuOverride,
      });

      setMessages((prev) => [...prev, response]);
    } catch (err: any) {
      showToast(err.message || 'Error processing your message', 'error');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `I encountered an issue processing your request: ${err.message || 'Network error'}. Please try again.`,
          timestamp: new Date().toISOString(),
          language: 'en',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectOrderItem = (orderNumber: string, sku: string, productName: string) => {
    handleSend(`Checking return eligibility for ${productName}`, orderNumber, sku);
  };

  const handleSelectResolution = (resId: string) => {
    handleSend(`I would like to proceed with resolution: ${resId}`);
  };

  const handleReturnSuccess = (returnNumber: string, status: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `succ-${Date.now()}`,
        role: 'assistant',
        content: `Your return request **${returnNumber}** has been recorded with status **${status}**! You can track live updates on the tracking dashboard.`,
        timestamp: new Date().toISOString(),
        language: language === 'auto' ? 'en' : language,
      },
    ]);
    if (onNavigateTab && !isWidget) {
      setTimeout(() => {
        onNavigateTab('tracking');
      }, 2500);
    }
  };

  const handlePhotoAnalysisAttached = (result: PhotoAnalysisResult) => {
    handleSend(
      `I uploaded a photo of the product defect. Automated analysis: ${result.detected_issue} (${Math.round(
        result.confidence_score * 100
      )}% confidence). ${result.summary}`
    );
  };

  return (
    <div className={`flex flex-col bg-white border border-slate-200/90 rounded-2xl shadow-xs overflow-hidden ${
      isWidget ? 'h-[540px]' : 'h-[calc(100vh-140px)] min-h-[550px]'
    }`}>
      {/* Chat Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 bg-slate-50/70">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-violet-600 flex items-center justify-center text-white shadow-xs">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 tracking-tight leading-tight">
              ReturnPilot AI Advisor
            </h3>
            <span className="text-[10px] text-slate-400 font-medium block">
              Multilingual Policy & Resolution Engine
            </span>
          </div>
        </div>

        {/* Language Override Controls */}
        <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl p-1 shadow-2xs text-[11px]">
          <Languages className="w-3.5 h-3.5 text-slate-400 ml-1" />
          {(['auto', 'en', 'hi', 'hinglish'] as const).map((langKey) => (
            <button
              key={langKey}
              type="button"
              onClick={() => setLanguage(langKey)}
              className={`px-2 py-0.5 rounded-lg font-medium transition-colors ${
                language === langKey
                  ? 'bg-brand-600 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {langKey === 'auto'
                ? 'Auto'
                : langKey === 'en'
                ? 'EN'
                : langKey === 'hi'
                ? 'हिंदी'
                : 'Hinglish'}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 text-xs">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-white text-[11px] font-bold ${
                  isUser ? 'bg-slate-800' : 'bg-brand-600'
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              {/* Message Bubble Content */}
              <div className={`max-w-[85%] sm:max-w-[78%] ${isUser ? 'items-end' : 'items-start'}`}>
                <div
                  className={`p-3.5 rounded-2xl shadow-2xs leading-relaxed ${
                    isUser
                      ? 'bg-slate-900 text-white rounded-tr-xs'
                      : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-xs'
                  }`}
                >
                  <p className="whitespace-pre-line text-xs">{msg.content}</p>

                  {/* Policy citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <PolicyCitationCard citations={msg.citations} />
                  )}

                  {/* Embedded orders */}
                  {msg.orders && msg.orders.length > 0 && (
                    <OrderCard
                      orders={msg.orders}
                      onSelectItem={handleSelectOrderItem}
                    />
                  )}

                  {/* Deterministic eligibility result */}
                  {msg.eligibility && (
                    <EligibilityCard eligibility={msg.eligibility} />
                  )}

                  {/* Resolution options */}
                  {msg.suggested_resolutions && msg.suggested_resolutions.length > 0 && (
                    <ResolutionCard
                      resolutions={msg.suggested_resolutions}
                      onSelectResolution={handleSelectResolution}
                    />
                  )}

                  {/* Explicit confirmation prompt */}
                  {msg.confirmation_required && msg.confirmation_payload && (
                    <ConfirmationCard
                      payload={msg.confirmation_payload}
                      sessionId={sessionId}
                      onSuccess={handleReturnSuccess}
                    />
                  )}
                </div>

                <span className="text-[10px] text-slate-400 mt-1 block px-1">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          );
        })}

        {/* Loading typing dots */}
        {isLoading && (
          <div className="flex items-center gap-2.5 text-slate-400">
            <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center text-white">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 rounded-tl-xs flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-brand-600 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-brand-600 animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 rounded-full bg-brand-600 animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/40 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        {QUICK_PROMPTS.map((p, idx) => (
          <button
            key={idx}
            type="button"
            disabled={isLoading}
            onClick={() => handleSend(p.query)}
            className="whitespace-nowrap px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-brand-500 hover:text-brand-600 text-slate-600 text-[11px] font-medium transition-colors shadow-2xs flex-shrink-0 disabled:opacity-50"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="p-3 sm:p-4 border-t border-slate-100 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          {/* Camera photo upload trigger */}
          <button
            type="button"
            onClick={() => setIsPhotoModalOpen(true)}
            title="Upload photo evidence of damaged or wrong item"
            className="p-2 rounded-xl text-slate-400 hover:text-brand-600 hover:bg-brand-50 transition-colors border border-slate-200 shadow-2xs"
          >
            <Camera className="w-4 h-4" />
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={isLoading}
            placeholder="Type your return issue in English, Hindi or Hinglish..."
            className="flex-1 text-xs rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Photo Upload Modal */}
      <PhotoUploadModal
        isOpen={isPhotoModalOpen}
        onClose={() => setIsPhotoModalOpen(false)}
        onAnalysisComplete={handlePhotoAnalysisAttached}
      />
    </div>
  );
};
