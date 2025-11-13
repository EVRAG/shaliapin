import { useState, useEffect } from 'react'
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/20/solid'

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '')

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function parseOpenAIResponse(response) {
  try {
    if (typeof response === 'string') {
      return JSON.parse(response)
    }
    return response
  } catch {
    return { response: response || '', status: 'unknown' }
  }
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(new Set())

  const fetchMessages = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/api/messages/all`)
      if (!response.ok) throw new Error('Failed to fetch messages')
      const data = await response.json()
      setMessages(data)
    } catch (error) {
      console.error('Error fetching messages:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (messageId, newStatus) => {
    try {
      setUpdating(prev => new Set(prev).add(messageId))
      const response = await fetch(`${API_URL}/api/messages/${messageId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      })
      
      if (!response.ok) throw new Error('Failed to update status')
      
      // Обновляем локальное состояние
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, status: newStatus } : msg
      ))
    } catch (error) {
      console.error('Error updating status:', error)
      alert('Ошибка при обновлении статуса')
    } finally {
      setUpdating(prev => {
        const next = new Set(prev)
        next.delete(messageId)
        return next
      })
    }
  }

  useEffect(() => {
    fetchMessages()
    // Обновляем каждые 5 секунд
    const interval = setInterval(fetchMessages, 5000)
    return () => clearInterval(interval)
  }, [])

  const okCount = messages.filter(m => m.status === 'ok').length
  const restrictedCount = messages.filter(m => m.status === 'restricted').length

  if (loading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="sm:flex sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Модерация сообщений</h1>
              <p className="mt-2 text-sm text-gray-600">
                Всего: <span className="font-medium text-gray-900">{messages.length}</span>
                {' · '}
                Принято: <span className="font-medium text-green-600">{okCount}</span>
                {' · '}
                Отклонено: <span className="font-medium text-red-600">{restrictedCount}</span>
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <button
                type="button"
                onClick={fetchMessages}
                className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                Обновить
              </button>
            </div>
          </div>
        </div>

        {/* Messages Grid */}
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Нет сообщений</p>
          </div>
        ) : (
          <ul role="list" className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {messages.map((message) => {
              const openAIResponse = parseOpenAIResponse(message.openai_response)
              const isOk = message.status === 'ok'
              const isUpdating = updating.has(message.id)

              return (
                <li key={message.id} className="col-span-1 flex flex-col divide-y divide-gray-200 rounded-lg bg-white shadow-sm border border-gray-200">
                  {/* Header */}
                  <div className="flex w-full items-center justify-between space-x-6 p-6">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-sm font-medium text-gray-900">#{message.id}</span>
                        <span
                          className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            isOk
                              ? 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20'
                              : 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20'
                          }`}
                        >
                          {isOk ? 'Принято' : 'Отклонено'}
                        </span>
                        {message.is_fetched && (
                          <span className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-600/20">
                            Забрано
                          </span>
                        )}
                      </div>
                      <p className="truncate text-sm text-gray-900 font-medium mb-1">
                        {message.message_text}
                      </p>
                      <p className="text-xs text-gray-500">
                        {message.name}
                        {message.gender && ` · ${message.gender}`}
                        {message.mood && ` · ${message.mood}`}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatDate(message.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div>
                    <div className="-mt-px flex divide-x divide-gray-200">
                      <div className="flex w-0 flex-1">
                        <button
                          type="button"
                          onClick={() => updateStatus(message.id, 'ok')}
                          disabled={isUpdating || isOk}
                          className={`relative -mr-px inline-flex w-0 flex-1 items-center justify-center gap-x-3 rounded-bl-lg border border-gray-200 py-4 text-sm font-semibold text-gray-900 ${
                            isOk
                              ? 'bg-green-50 text-green-700 cursor-default'
                              : 'bg-white hover:bg-gray-50'
                          } ${isUpdating ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          <CheckCircleIcon
                            aria-hidden="true"
                            className={`size-5 ${isOk ? 'text-green-600' : 'text-gray-400'}`}
                          />
                          Принять
                        </button>
                      </div>
                      <div className="-ml-px flex w-0 flex-1">
                        <button
                          type="button"
                          onClick={() => updateStatus(message.id, 'restricted')}
                          disabled={isUpdating || !isOk}
                          className={`relative inline-flex w-0 flex-1 items-center justify-center gap-x-3 rounded-br-lg border border-gray-200 py-4 text-sm font-semibold text-gray-900 ${
                            !isOk
                              ? 'bg-red-50 text-red-700 cursor-default'
                              : 'bg-white hover:bg-gray-50'
                          } ${isUpdating ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          <XCircleIcon
                            aria-hidden="true"
                            className={`size-5 ${!isOk ? 'text-red-600' : 'text-gray-400'}`}
                          />
                          Отклонить
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
