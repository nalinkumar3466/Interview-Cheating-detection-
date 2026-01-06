import { useEffect, useRef } from 'react'
import api from '../services/api'

// useAntiCheat: best-effort anti-cheat utilities. Attaches listeners to
// block common devtools shortcuts, disable right click, detect tab switch,
// log events to backend, and attempt to prevent navigation/refresh.
// Parameters: { token, interviewId, enabled }
export default function useAntiCheat({ token, interviewId, enabled = false }){
  const orig = useRef({})

  useEffect(() => {
    if (!enabled) return

    function sendLog(event, detail = {}){
      const payload = { token, interview_id: interviewId, event, ts: new Date().toISOString(), detail }
      // fire-and-forget; keep console copy
      try { api.post('/candidate/log', payload).catch(()=>{}) } catch(e) {}
      try { console.info('anti-cheat-log', payload) } catch(e) {}
    }

    // context menu
    function onContext(e){ e.preventDefault(); sendLog('contextmenu_blocked') }
    window.addEventListener('contextmenu', onContext)

    // keydown: block common devtools / page-source keys
    function onKey(e){
      // Ctrl+Shift+I / Ctrl+Shift+C / Ctrl+Shift+J / F12 / Ctrl+U / Ctrl+R / F5
      if ((e.ctrlKey && e.shiftKey && ['I','C','J'].includes(e.key.toUpperCase())) ||
          e.key === 'F12' ||
          (e.ctrlKey && e.key.toUpperCase() === 'U') ||
          (e.ctrlKey && e.key.toUpperCase() === 'R') ||
          e.key === 'F5'){
        e.preventDefault(); e.stopPropagation(); sendLog('blocked_shortcut', { key: e.key })
      }
    }
    window.addEventListener('keydown', onKey, true)

    // visibility change / blur
    function onVisibility(){
      if (document.hidden) sendLog('visibility_hidden')
      else sendLog('visibility_visible')
    }
    document.addEventListener('visibilitychange', onVisibility)

    function onBlur(){ sendLog('window_blur') }
    window.addEventListener('blur', onBlur)

    // beforeunload: warn + log refresh attempts
    function onBeforeUnload(e){
      sendLog('before_unload')
      // show generic prompt (modern browsers ignore custom text)
      e.preventDefault()
      e.returnValue = ''
      return ''
    }
    window.addEventListener('beforeunload', onBeforeUnload)

    // history push/replace protection: no-op during candidate mode
    orig.current.pushState = history.pushState
    orig.current.replaceState = history.replaceState
    history.pushState = function(){ sendLog('attempt_pushstate'); }
    history.replaceState = function(){ sendLog('attempt_replacestate'); }

    // popstate: prevent leaving candidate route by forcing back to same URL
    function onPop(e){ sendLog('popstate_detected'); /* best-effort: nothing else */ }
    window.addEventListener('popstate', onPop)

    // keep trying to request fullscreen (best-effort; user must accept)
    async function tryFullscreen(){
      try {
        const el = document.documentElement
        if (el.requestFullscreen) await el.requestFullscreen()
      } catch(e){ /* ignore */ }
    }
    // do not spam attempts; run once
    tryFullscreen().catch(()=>{})

    sendLog('candidate_enter')

    return () => {
      sendLog('candidate_exit')
      window.removeEventListener('contextmenu', onContext)
      window.removeEventListener('keydown', onKey, true)
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('blur', onBlur)
      window.removeEventListener('beforeunload', onBeforeUnload)
      window.removeEventListener('popstate', onPop)
      // restore history functions
      try { history.pushState = orig.current.pushState } catch(e){}
      try { history.replaceState = orig.current.replaceState } catch(e){}
    }
  }, [token, interviewId, enabled])
}
