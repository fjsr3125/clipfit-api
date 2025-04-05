// ✅ 合成スタート時に動画＆静止画を FastAPI に送信するフロントエンドコード

'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

export default function Home() {
  const [videos, setVideos] = useState<File[]>([])
  const [images, setImages] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setVideos(Array.from(e.target.files))
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setImages(Array.from(e.target.files))
    }
  }

  const handleStart = async () => {
    if (videos.length === 0 || images.length === 0) {
      alert('動画と静止画の両方を選択してください！')
      return
    }

    const formData = new FormData()
    videos.forEach((file) => formData.append('videos', file))
    images.forEach((file) => formData.append('images', file))

    try {
      setUploading(true)
      setMessage('アップロード中...')

      const res = await fetch('https://clipfit-api.onrender.com/merge', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) throw new Error('送信エラー')

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)

      const a = document.createElement('a')
      a.href = url
      a.download = 'clipfit_result.mp4'
      a.click()
      a.remove()
      setMessage('✅ 合成完了！ダウンロードを開始しました')
    } catch (err) {
      console.error(err)
      setMessage('❌ 合成に失敗しました')
    } finally {
      setUploading(false)
    }
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-6">🎬 ClipFit 動画合成ツール</h1>

      <div className="grid grid-cols-2 gap-8 mb-4">
        <div>
          <label className="font-semibold">🎥 動画ファイル (複数可)</label>
          <input type="file" multiple accept="video/*" onChange={handleVideoChange} className="block mt-2" />
        </div>
        <div>
          <label className="font-semibold">🖼️ 静止画PNG (複数可)</label>
          <input type="file" multiple accept="image/png" onChange={handleImageChange} className="block mt-2" />
        </div>
      </div>

      <Button onClick={handleStart} disabled={uploading}>
        {uploading ? '合成中...' : '🚀 合成スタート'}
      </Button>

      <p className="mt-4 text-sm text-muted-foreground">{message}</p>
    </main>
  )
}
