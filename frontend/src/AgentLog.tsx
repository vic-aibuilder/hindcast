import { useEffect, useRef } from 'react'

interface AgentLogProps {
  messages: string[]
  active?: boolean
  label?: string
}

export default function AgentLog({ messages, active = false, label }: AgentLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) return null

  return (
    <div className="agent-log" aria-live="polite" aria-label="Agent reasoning log">
      {label && <div className="agent-log__hdr">{label}</div>}
      {messages.map((msg, i) => (
        <div key={i} className="agent-log__line">
          <span>{msg}</span>
          {active && i === messages.length - 1 && (
            <span className="agent-log__cursor" aria-hidden="true" />
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
