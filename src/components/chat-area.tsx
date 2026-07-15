"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Mic, Paperclip, StopCircle, Copy, Check, ThumbsUp, ThumbsDown, FileText, Image as ImageIcon, PanelLeft, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { ChatContainer } from "@/components/ui/chat-container"
import { Message } from "@/components/ui/message"
import { PromptInput, PromptInputTextarea, PromptInputActions, PromptInputAction } from "@/components/ui/prompt-input"
import { ThinkingBar } from "@/components/ui/thinking-bar"

export type MessageType = {
  id: string
  role: "user" | "assistant"
  content: string
  files?: Array<{ name: string; type: "image" | "file" }>
  thinking?: boolean
  thinkingDuration?: string
  isStreaming?: boolean
  evidences?: Array<{
    paper_id: string
    title: string
    abstract: string
    categories: string[]
    similarity: number
  }>
  insufficientEvidence?: boolean
}

type ChatAreaProps = {
  messages: MessageType[]
  onSendMessage: (content: string, files?: Array<{ name: string; type: "image" | "file" }>) => void
  onStopGeneration?: () => void
  isGenerating: boolean
  isSidebarCollapsed: boolean
  setIsSidebarCollapsed: (collapsed: boolean) => void
}

export function ChatArea({
  messages,
  onSendMessage,
  onStopGeneration,
  isGenerating,
  isSidebarCollapsed,
  setIsSidebarCollapsed,
}: ChatAreaProps) {
  const [inputValue, setInputValue] = useState("")
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [feedbackId, setFeedbackId] = useState<{ [id: string]: "like" | "dislike" | undefined }>({})
  const [attachedFiles, setAttachedFiles] = useState<Array<{ name: string; type: "image" | "file" }>>([])
  
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    if (!inputValue.trim() && attachedFiles.length === 0) return
    onSendMessage(inputValue, attachedFiles)
    setInputValue("")
    setAttachedFiles([])
  }

  const handleAttachFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      const type: "image" | "file" = file.type.startsWith("image/") ? "image" : "file"
      setAttachedFiles((prev) => [...prev, { name: file.name, type }])
    }
  }

  const removeAttachedFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const copyToClipboard = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(msgId)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleFeedback = (msgId: string, type: "like" | "dislike") => {
    // Local-only UI feedback: the exam guide does not require persisting
    // relevance feedback, so this just toggles the button state.
    const isUndoing = feedbackId[msgId] === type
    const newFeedback = isUndoing ? undefined : type

    setFeedbackId((prev) => ({
      ...prev,
      [msgId]: newFeedback,
    }))
  }

  // Scroll to bottom when messages or loading changes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  const renderPromptInput = () => {
    return (
      <div className="w-full flex flex-col gap-2">
        {/* Attached Files Preview */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 p-2 rounded-2xl glass-card border border-border animate-in slide-in-from-bottom-2 duration-300">
            {attachedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-secondary border border-border text-xs text-foreground"
              >
                {file.type === "image" ? (
                  <ImageIcon className="size-3 text-primary" />
                ) : (
                  <FileText className="size-3 text-primary" />
                )}
                <span className="max-w-[120px] truncate">{file.name}</span>
                <button
                  onClick={() => removeAttachedFile(idx)}
                  className="ml-1 text-muted-foreground hover:text-foreground text-[10px] font-bold cursor-pointer"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* PromptInput wrapper with absolute black, centered layout */}
        <PromptInput
          isLoading={isGenerating}
          value={inputValue}
          onValueChange={setInputValue}
          onSubmit={handleSend}
          className="bg-black! border border-border! focus-within:border-white/30! p-2 rounded-3xl relative group transition-all duration-300 flex items-center w-full"
        >
          {/* Hidden native input for attaching files */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleAttachFile}
            className="hidden"
          />

          <PromptInputActions className="pl-1 shrink-0">
            <PromptInputAction tooltip="Adjuntar archivo">
              <span
                onClick={() => fileInputRef.current?.click()}
                className="p-2 rounded-full hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors cursor-pointer inline-block"
              >
                <Paperclip className="size-4.5" />
              </span>
            </PromptInputAction>
            <PromptInputAction tooltip="Grabación de voz (Demo)">
              <span
                className="p-2 rounded-full hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors cursor-pointer inline-block"
              >
                <Mic className="size-4.5" />
              </span>
            </PromptInputAction>
          </PromptInputActions>

          <div className="flex-1 min-w-0 pr-2">
            <PromptInputTextarea
              placeholder="Pregúntale a tu asistente..."
              className="w-full text-foreground bg-transparent! dark:bg-transparent! border-none! shadow-none! outline-none! focus-visible:ring-0! focus-visible:ring-offset-0! min-h-0! py-1.5! px-3! resize-none"
            />
          </div>

          <PromptInputActions className="pr-1 shrink-0">
            {isGenerating ? (
              <PromptInputAction tooltip="Detener generación">
                <span
                  onClick={onStopGeneration}
                  className="p-2 rounded-full bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors cursor-pointer inline-block"
                >
                  <StopCircle className="size-4.5" />
                </span>
              </PromptInputAction>
            ) : (
              <PromptInputAction tooltip="Enviar mensaje">
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!inputValue.trim() && attachedFiles.length === 0}
                  className={cn(
                    "p-2 rounded-full transition-all duration-300 cursor-pointer",
                    inputValue.trim() || attachedFiles.length > 0
                      ? "bg-primary text-primary-foreground scale-105 shadow-md"
                      : "text-muted-foreground/45 opacity-40 pointer-events-none cursor-not-allowed"
                  )}
                >
                  <Send className="size-4.5" />
                </button>
              </PromptInputAction>
            )}
          </PromptInputActions>
        </PromptInput>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-transparent relative">
      {/* Header bar - No text, menu toggle using PanelLeft when collapsed */}
      <header className="h-16 flex items-center px-6 z-20 shrink-0">
        {isSidebarCollapsed && (
          <button
            onClick={() => setIsSidebarCollapsed(false)}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            title="Abrir menú"
          >
            <PanelLeft className="size-4" />
          </button>
        )}
      </header>

      {/* Main chat window */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 relative" ref={chatContainerRef}>
        {messages.length === 0 ? (
          /* Initial Screen - Centered Title + Centered Input box */
          <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto py-12 w-full space-y-6">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground select-none">
              ¿En qué puedo ayudarte hoy?
            </h1>
            <div className="w-full">
              {renderPromptInput()}
            </div>
          </div>
        ) : (
          /* Messages list */
          <div className="max-w-3xl mx-auto space-y-6 pb-24">
            <ChatContainer>
              {messages.map((message) => {
                const isUser = message.role === "user"
                return (
                  <div
                    key={message.id}
                    className={cn(
                      "group flex flex-col space-y-1.5 w-full animate-in fade-in-50 duration-300",
                      isUser ? "items-end" : "items-start"
                    )}
                  >
                    {/* Render visual files attachments */}
                    {message.files && message.files.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-1 justify-end max-w-full">
                        {message.files.map((file, fIdx) => (
                          <div
                            key={fIdx}
                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-secondary border border-border text-xs text-foreground"
                          >
                            {file.type === "image" ? (
                              <ImageIcon className="size-3 text-primary" />
                            ) : (
                              <FileText className="size-3 text-primary" />
                            )}
                            <span className="max-w-[150px] truncate">{file.name}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Chat Bubble */}
                    <Message
                      role={message.role}
                      variant={isUser ? "bubble" : "default"}
                      className={cn(
                        "max-w-[85%] rounded-3xl text-sm leading-relaxed p-4",
                        isUser
                          ? "bg-primary text-primary-foreground font-normal rounded-tr-sm shadow-xs"
                          : "bg-transparent text-foreground border-none pl-0 pr-4 py-1"
                      )}
                    >
                      {message.thinking && (
                        <div className="w-full pb-3 animate-in fade-in-50 duration-200">
                          <ThinkingBar
                            text="Analizando solicitud..."
                            onStop={onStopGeneration}
                            stopLabel="Detener"
                            className="bg-secondary px-3 py-2 rounded-xl"
                          />
                        </div>
                      )}

                      {/* Display reasoning duration if present */}
                      {!message.thinking && message.thinkingDuration && (
                        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-2 font-mono">
                          <span>{message.thinkingDuration}</span>
                        </div>
                      )}

                      {/* Message Content */}
                      <div className={cn(
                        "prose dark:prose-invert max-w-none text-foreground",
                        !isUser && "glass-card p-4 rounded-3xl border border-border shadow-xs"
                      )}>
                        {message.content}
                      </div>

                      {/* Explicit notice when the corpus lacks enough evidence for this query */}
                      {!isUser && !message.thinking && message.insufficientEvidence && (
                        <div className="mt-2 text-[11px] text-amber-500/90 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5">
                          El corpus no contiene evidencia suficiente para responder esta consulta con certeza.
                        </div>
                      )}

                      {/* Evidences (Top-K retrieved papers) Accordion - Only shown for Assistant messages with evidence */}
                      {!isUser && !message.thinking && message.evidences && message.evidences.length > 0 && (
                        <details className="mt-3 border-t border-border/20 pt-3 group/details w-full">
                          <summary className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground select-none outline-none flex items-center gap-1 cursor-pointer list-none">
                            <ChevronDown className="size-3 transition-transform group-open/details:rotate-180" />
                            <span>Evidencias recuperadas ({message.evidences.length})</span>
                          </summary>
                          <div className="grid grid-cols-1 gap-3 mt-3.5 animate-in fade-in-30 slide-in-from-top-1 duration-300">
                            {message.evidences.map((item, idx) => (
                              <div
                                key={idx}
                                className="bg-secondary/20 border border-border/60 p-3 rounded-xl hover:bg-secondary/40 transition-all duration-200"
                              >
                                <p className="text-xs font-medium text-foreground leading-snug" title={item.title}>
                                  {item.title}
                                </p>
                                <p className="text-[11px] text-muted-foreground/80 leading-snug line-clamp-3 mt-1">
                                  {item.abstract}
                                </p>
                                <div className="flex flex-wrap items-center gap-2 mt-1.5">
                                  {item.categories?.map((cat) => (
                                    <span
                                      key={cat}
                                      className="text-[9px] uppercase font-semibold text-muted-foreground/60 tracking-wider bg-secondary/60 px-1.5 py-0.5 rounded"
                                    >
                                      {cat}
                                    </span>
                                  ))}
                                  <span className="text-[9px] text-muted-foreground font-mono ml-auto">
                                    Similitud: {(item.similarity * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}

                      {/* Floating actions for assistant messages */}
                      {!isUser && !message.thinking && (
                        <div className="flex items-center gap-2 mt-2 ml-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                          <button
                            onClick={() => copyToClipboard(message.content, message.id)}
                            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-all duration-200 cursor-pointer"
                            title="Copiar mensaje"
                          >
                            {copiedId === message.id ? (
                              <Check className="size-3.5 text-emerald-500" />
                            ) : (
                              <Copy className="size-3.5" />
                            )}
                          </button>
                          <button
                            onClick={() => handleFeedback(message.id, "like")}
                            className={cn(
                              "p-1 rounded-md transition-all duration-200 cursor-pointer",
                              feedbackId[message.id] === "like"
                                ? "text-emerald-500 bg-emerald-500/10"
                                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                            )}
                          >
                            <ThumbsUp className="size-3.5" />
                          </button>
                          <button
                            onClick={() => handleFeedback(message.id, "dislike")}
                            className={cn(
                              "p-1 rounded-md transition-all duration-200 cursor-pointer",
                              feedbackId[message.id] === "dislike"
                                ? "text-red-500 bg-red-500/10"
                                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                            )}
                          >
                            <ThumbsDown className="size-3.5" />
                          </button>
                        </div>
                      )}
                    </Message>
                  </div>
                )
              })}
            </ChatContainer>
          </div>
        )}
      </div>

      {/* Floating Prompt Input Panel at the bottom - only shown when there are messages */}
      {messages.length > 0 && (
        <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-background via-background/90 to-transparent z-20 pointer-events-none">
          <div className="max-w-3xl mx-auto w-full pointer-events-auto">
            {renderPromptInput()}
          </div>
        </div>
      )}
    </div>
  )
}
