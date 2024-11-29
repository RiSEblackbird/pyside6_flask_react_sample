// src/App.tsx
import { useState, useEffect } from 'react'
import { Todo, ApiResponse } from './types/todo'

function App() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [newTodo, setNewTodo] = useState('')

  // Todo一覧の取得
  const fetchTodos = async () => {
    const response = await fetch('http://localhost:5000/api/todos')
    const data = await response.json()
    setTodos(data)
  }

  // 新規Todo追加
  const addTodo = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTodo.trim()) return

    const response = await fetch('http://localhost:5000/api/todos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTodo })
    })
    const data: ApiResponse = await response.json()
    if (data.success) {
      setNewTodo('')
      fetchTodos()
    }
  }

  // Todo完了状態の更新
  const toggleTodo = async (todo: Todo) => {
    const response = await fetch(`http://localhost:5000/api/todos/${todo.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: !todo.completed })
    })
    const data: ApiResponse = await response.json()
    if (data.success) {
      fetchTodos()
    }
  }

  // Todo削除
  const deleteTodo = async (id: number) => {
    const response = await fetch(`http://localhost:5000/api/todos/${id}`, {
      method: 'DELETE'
    })
    const data: ApiResponse = await response.json()
    if (data.success) {
      fetchTodos()
    }
  }

  // 初期データ取得
  useEffect(() => {
    fetchTodos()
  }, [])

  return (
    <div className="container mx-auto p-4 max-w-md">
      <h1 className="text-2xl font-bold mb-4">Todoリスト</h1>
      
      <form onSubmit={addTodo} className="mb-4">
        <input
          type="text"
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          placeholder="新しいタスクを入力"
          className="w-full p-2 border rounded"
        />
      </form>

      <ul className="space-y-2">
        {todos.map((todo) => (
          <li 
            key={todo.id} 
            className="flex items-center justify-between p-2 border rounded"
          >
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={() => toggleTodo(todo)}
                className="mr-2"
              />
              <span className={todo.completed ? 'line-through' : ''}>
                {todo.title}
              </span>
            </div>
            <button
              onClick={() => deleteTodo(todo.id)}
              className="text-red-500 hover:text-red-700"
            >
              削除
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App