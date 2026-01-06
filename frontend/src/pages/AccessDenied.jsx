import React from 'react'

export default function AccessDenied({ message = 'Access denied or token invalid/expired.' }){
  return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh', background:'#fff' }}>
      <div style={{ maxWidth:720, padding:28, textAlign:'center', borderRadius:10, boxShadow:'0 12px 40px rgba(0,0,0,0.06)' }}>
        <h2>Access Denied</h2>
        <p style={{ color:'#444' }}>{message}</p>
        <p style={{ color:'#888', fontSize:13 }}>If you believe this is an error, contact the test administrator for a fresh candidate link.</p>
      </div>
    </div>
  )
}
