import React from 'react'

export default function AccessDenied({ message = 'Access denied or token invalid/expired.' }){
  return (
    <div className="flex items-center justify-center min-h-screen bg-white dark:bg-[#05070a]">
      <div className="max-w-md p-8 text-center bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700">
        <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4v2m0 0v2m0-6v-2m0 0V7" /></svg>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Access Denied</h2>
        <p className="text-slate-600 dark:text-slate-300 mb-4">{message}</p>
        <p className="text-sm text-slate-500 dark:text-slate-400">If you believe this is an error, contact the test administrator for a fresh candidate link.</p>
      </div>
    </div>
  )
}
