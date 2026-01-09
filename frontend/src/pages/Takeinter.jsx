import React from "react";
import { useParams, Link } from 'react-router-dom'

export default function TakeInterview(){
	const { id } = useParams()
	return (
		<div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-[#05070a] min-h-screen">
			<div className="text-center">
				<div className="w-16 h-16 rounded-full bg-amber-100 dark:bg-amber-900/50 flex items-center justify-center mx-auto mb-4">
					<svg className="w-8 h-8 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4v2m0 0v2m0-6v-2m0 0V7" /></svg>
				</div>
				<h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Route Deprecated</h2>
				<p className="text-slate-600 dark:text-slate-300 mb-6">This interview route has been consolidated. Please proceed to the interview run page.</p>
				<Link to={`/run/${id}`} className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-semibold rounded-lg hover:from-emerald-600 hover:to-emerald-700 transition-all shadow-lg">
					Continue to Interview
				</Link>
			</div>
		</div>
	)
}
