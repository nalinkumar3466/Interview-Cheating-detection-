import React, { useEffect, useState } from 'react'
import botAnim from '../assets/bot-speaking.json'

export default function BotSpeaker({ speaking = false }) {
  const [LottieComp, setLottieComp] = useState(null)

  useEffect(() => {
    let mounted = true
    import('lottie-react').then((m) => {
      if (mounted) setLottieComp(() => m.default)
    }).catch(() => {
      // lottie-react not installed — fallback will be used
    })
    return () => { mounted = false }
  }, [])

  if (LottieComp) {
    const Lottie = LottieComp
    return (
      <div style={{ width: 140, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Lottie animationData={botAnim} loop={speaking} autoplay={speaking} style={{ width: 120 }} />
        <div className="bot-label" style={{ marginTop: 6, fontWeight: 700, color: '#2b3a67' }}>Berribot</div>
      </div>
    )
  }

  // fallback static SVG face
  return (
    <div style={{ width: 140, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg width="120" height="120" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <circle cx="32" cy="32" r="30" fill="#fff" />
        <circle cx="32" cy="32" r="22" fill="#5b6cff" />
        <circle cx="24" cy="28" r="3" fill="#fff" />
        <circle cx="40" cy="28" r="3" fill="#fff" />
        <path d="M24 38c3 3 9 5 16 0" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      </svg>
      <div className="bot-label" style={{ marginTop: 6, fontWeight: 700, color: '#2b3a67' }}>Berribot</div>
    </div>
  )
}
