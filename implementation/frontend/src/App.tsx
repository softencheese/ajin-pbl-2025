import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div style={{ padding: '50px', textAlign: 'center' }}>
      <h1>🏭 AJIN RFID 물류 추적 시스템</h1>
      <p>FastAPI + React + MySQL</p>
      <div>
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
      </div>
      <p style={{ marginTop: '20px', color: '#666' }}>
        구현 준비 완료 - 개발을 시작하세요!
      </p>
    </div>
  )
}

export default App
