import React, { useState } from "react";
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

function isFutureDate(dt){
	try{
		const d = new Date(dt)
		return d.toString() !== 'Invalid Date' && d.getTime() > Date.now()
	}catch(e){return false}
}

function validateEmail(email){
	return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)
}

export default function ScheduleInterview(){
	const [title, setTitle] = useState('')
	const [candidateName, setCandidateName] = useState('')
	const [candidateEmail, setCandidateEmail] = useState('')
	const [datetimeLocal, setDatetimeLocal] = useState('')
	const [duration, setDuration] = useState(45)
	const [timezone, setTimezone] = useState('')
	const [instructions, setInstructions] = useState('')
	const [tokenTTL, setTokenTTL] = useState(180)
	const [questions, setQuestions] = useState([])
	const [message, setMessage] = useState(null)
	const [candidateLink, setCandidateLink] = useState(null)
	const [submitting, setSubmitting] = useState(false)
	const navigate = useNavigate()

	function addQuestion(){
		setQuestions(qs => ([...qs, { order: qs.length+1, text: '', examples:'', type: 'explain' }]))
	}

	function updateQuestion(idx, patch){
		setQuestions(qs => qs.map((q,i)=> i===idx ? {...q, ...patch} : q))
	}

	function removeQuestion(idx){
		setQuestions(qs=> qs.filter((_,i)=> i!==idx).map((q,i)=> ({...q, order: i+1})))
	}

	function moveQuestion(idx, dir){
		setQuestions(qs=>{
			const arr = [...qs]
			const to = idx + dir
			if(to < 0 || to >= arr.length) return arr
			const tmp = arr[to]
			arr[to] = arr[idx]
			arr[idx] = tmp
			return arr.map((q,i)=> ({...q, order: i+1}))
		})
	}

	async function onSubmit(e){
		e.preventDefault()
		setMessage(null)
		if(!title) return setMessage('Title is required')
		if(!candidateName) return setMessage('Candidate name is required')
		if(!validateEmail(candidateEmail)) return setMessage('Candidate email looks invalid')
		if(!datetimeLocal || !isFutureDate(datetimeLocal)) return setMessage('Scheduled datetime must be in the future')
		if(!(Number.isInteger(Number(duration)) && Number(duration) > 0)) return setMessage('Duration must be a positive integer')
		if(questions.length === 0) return setMessage('Add at least one question')
		for(const q of questions){ if(!q.text || q.text.trim() === '') return setMessage('All questions must have text') }

		const schedIso = new Date(datetimeLocal).toISOString()

		const payload = {
			title,
			candidate_name: candidateName,
			candidate_email: candidateEmail,
			scheduled_at: schedIso,
			duration_minutes: Number(duration),
			timezone: timezone || undefined,
			instructions: instructions || undefined,
			token_ttl_minutes: tokenTTL || undefined,
			questions: questions.map(q=> ({ order: q.order, text: q.text, examples: q.examples, type: q.type }))
		}

		setSubmitting(true)
		try{
			const res = await api.post('/interviews/', payload)
			setMessage(`Scheduled with id ${res.data.id}`)
			if (res?.data?.token) {
				const origin = window.location.origin
				const link = `${origin}/candidate/interview/${res.data.token}`
				setCandidateLink({ link, token: res.data.token })
			}
			setTitle('')
			setCandidateName('')
			setCandidateEmail('')
			setDatetimeLocal('')
			setDuration(45)
			setTimezone('')
			setInstructions('')
			setTokenTTL(180)
			setQuestions([])
		}catch(err){
			console.error('Schedule submit error:', err)
			let msg = 'Error scheduling'
			if (err?.response?.data?.detail) {
				if (Array.isArray(err.response.data.detail)) {
					msg = err.response.data.detail.map(e => typeof e === 'object' ? (e.msg || e.message || JSON.stringify(e)) : e).join(', ')
				} else if (typeof err.response.data.detail === 'object') {
					msg = err.response.data.detail.msg || err.response.data.detail.message || JSON.stringify(err.response.data.detail)
				} else {
					msg = err.response.data.detail
				}
			} else if (err?.message) {
				msg = err.message
			}
			setMessage(`Error scheduling: ${msg}`)
		}finally{ setSubmitting(false) }
	}

	return (
		<div className="max-w-4xl mx-auto bg-white dark:bg-[#05070a] text-black dark:text-white min-h-screen">
			<div className="mb-8">
				<h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">Schedule Interview</h1>
				<p className="text-slate-600 dark:text-slate-300">Create a new interview assessment with custom questions and candidate details</p>
			</div>

			<form onSubmit={onSubmit} className="space-y-8">
				{/* Basic Info */}
				<div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
					<h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">Interview Details</h3>
					<div className="space-y-6">
						<div>
					<label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Interview Title *</label>
					<input value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="e.g., Senior Software Engineer - Round 1" className="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-slate-700 text-slate-900 dark:text-white" />
						</div>

						<div className="grid grid-cols-2 gap-6">
							<div>
								<label className="block text-sm font-semibold text-slate-700 mb-2">Candidate Name *</label>
								<input value={candidateName} onChange={e=>setCandidateName(e.target.value)} placeholder="Asha Kumar" className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900" />
							</div>
							<div>
								<label className="block text-sm font-semibold text-slate-700 mb-2">Candidate Email *</label>
								<input value={candidateEmail} onChange={e=>setCandidateEmail(e.target.value)} placeholder="asha@example.com" className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900" />
							</div>
						</div>
					</div>
				</div>

				{/* Schedule & Duration */}
				<div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
					<h3 className="text-lg font-semibold text-slate-900 mb-6 pb-4 border-b border-slate-200">Schedule & Settings</h3>
					<div className="grid grid-cols-3 gap-6">
						<div>
							<label className="block text-sm font-semibold text-slate-700 mb-2">Scheduled At *</label>
							<input type="datetime-local" value={datetimeLocal} onChange={e=>setDatetimeLocal(e.target.value)} className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900" />
						</div>
						<div>
							<label className="block text-sm font-semibold text-slate-700 mb-2">Duration (min) *</label>
							<input type="number" value={duration} onChange={e=>setDuration(e.target.value)} min={5} max={480} className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900" />
						</div>
						<div>
							<label className="block text-sm font-semibold text-slate-700 mb-2">Timezone</label>
							<input value={timezone} onChange={e=>setTimezone(e.target.value)} placeholder="Asia/Kolkata" className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900" />
						</div>
					</div>
					<div className="mt-6">
						<label className="block text-sm font-semibold text-slate-700 mb-2">Token TTL (minutes)</label>
						<input type="number" value={tokenTTL} onChange={e=>setTokenTTL(e.target.value)} className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900" />
					</div>
				</div>

				{/* Instructions */}
		<div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
			<h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 pb-4 border-b border-slate-200 dark:border-slate-700">Instructions (Optional)</h3>
			<textarea value={instructions} onChange={e=>setInstructions(e.target.value)} rows={4} placeholder="Add any special instructions for the candidate..." className="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-slate-700 text-slate-900 dark:text-white resize-none" />
				</div>

				{/* Questions */}
		<div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
			<div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
				<h3 className="text-lg font-semibold text-slate-900 dark:text-white">Questions *</h3>
						<span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{questions.length} added</span>
					</div>
					<div className="space-y-4">
						{questions.map((q, idx)=> (
							<div key={idx} className="border border-slate-200 dark:border-slate-600 rounded-lg p-5 bg-slate-50 dark:bg-slate-700 hover:bg-white dark:hover:bg-slate-600 transition-colors">
								<div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-200">
									<div className="flex items-center gap-3">
										<span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 font-semibold text-sm">{q.order}</span>
										<span className="text-sm font-medium text-slate-600 bg-blue-100 text-blue-700 px-3 py-1 rounded-full capitalize">{q.type}</span>
									</div>
									<div className="flex gap-2">
										<button type="button" onClick={()=>moveQuestion(idx, -1)} className="p-2 hover:bg-slate-200 rounded-lg transition-colors" title="Move up">↑</button>
										<button type="button" onClick={()=>moveQuestion(idx, 1)} className="p-2 hover:bg-slate-200 rounded-lg transition-colors" title="Move down">↓</button>
										<button type="button" onClick={()=>removeQuestion(idx)} className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium text-sm">Remove</button>
									</div>
								</div>
								<div className="space-y-4">
									<div>
										<label className="block text-xs font-semibold text-slate-700 mb-2">Question Text</label>
										<input value={q.text} onChange={e=>updateQuestion(idx, { text: e.target.value })} placeholder="Enter the question..." className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900 text-sm" />
									</div>
									<div>
										<label className="block text-xs font-semibold text-slate-700 mb-2">Examples (comma-separated)</label>
										<input value={q.examples} onChange={e=>updateQuestion(idx, { examples: e.target.value })} placeholder="e.g., Python, JavaScript, etc." className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900 text-sm" />
									</div>
									<div>
										<label className="block text-xs font-semibold text-slate-700 mb-2">Question Type</label>
										<select value={q.type} onChange={e=>updateQuestion(idx, { type: e.target.value })} className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white text-slate-900 text-sm">

											<option value="explain">Explanation</option>
											<option value="multiple">Multiple Choice</option>
											<option value="sketch">Sketch / System Design</option>
										</select>
									</div>
								</div>
							</div>
						))}
					</div>
					<button type="button" onClick={addQuestion} className="mt-6 w-full py-3 border-2 border-dashed border-slate-300 text-slate-700 font-semibold rounded-lg hover:border-emerald-500 hover:text-emerald-600 hover:bg-emerald-50 transition-all">
						+ Add Question
					</button>
				</div>

				{/* Submit */}
				<div className="flex gap-4">
					<button type="submit" disabled={submitting} className="flex-1 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-semibold py-3 rounded-lg hover:from-emerald-600 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-60 disabled:cursor-not-allowed">
						{submitting ? 'Scheduling...' : 'Schedule Interview'}
					</button>
				</div>
			</form>

			{/* Messages */}
			{message && (
				<div className={`mt-6 p-4 rounded-lg font-medium ${
					message.startsWith('Error') 
						? 'bg-red-50 border border-red-200 text-red-700' 
						: message.includes('copied')
						? 'bg-blue-50 border border-blue-200 text-blue-700'
						: 'bg-emerald-50 border border-emerald-200 text-emerald-700'
				}`}>
					{message}
				</div>
			)}

			{/* Candidate Link */}
			{candidateLink && (
				<div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 shadow-lg">
					<h3 className="font-semibold text-slate-900 mb-4 text-lg">🔗 Candidate Link</h3>
					<p className="text-slate-600 text-sm mb-4">Share this link with your candidate to start the interview:</p>
					<div className="flex gap-3 mb-4">
						<input readOnly value={candidateLink.link} className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-lg font-mono text-sm text-slate-700" />
						<button onClick={() => { navigator.clipboard.writeText(candidateLink.link).catch(()=>{}); setMessage('Link copied to clipboard') }} className="px-6 py-3 bg-emerald-500 text-white font-semibold rounded-lg hover:bg-emerald-600 transition-colors shadow-md hover:shadow-lg">
							Copy
						</button>
					</div>
					<a href={`mailto:${candidateEmail}?subject=Interview%20Link&body=Please%20join%20your%20interview:%20${encodeURIComponent(candidateLink.link)}`}>
						<button type="button" className="w-full px-4 py-2 bg-white border border-blue-300 text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition-colors">
							✉ Send via Email
						</button>
					</a>
				</div>
			)}
		</div>
	)
}
