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
	const [datetimeLocal, setDatetimeLocal] = useState('') // datetime-local input
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
		setQuestions(qs => ([...qs, { order: qs.length+1, text: '', examples:'', type: 'coding' }]))
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

		// convert datetime-local (no timezone) to ISO (UTC)
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
			const res = await api.post('/interviews', payload)
			setMessage(`Scheduled with id ${res.data.id}`)
			// show candidate link and token for immediate sharing (do not navigate away)
			if (res?.data?.token) {
				const origin = window.location.origin
				const link = `${origin}/candidate/interview/${res.data.token}`
				setCandidateLink({ link, token: res.data.token })
			}
			// reset form fields but keep message and show link
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
			const msg = err?.response?.data?.detail || err?.message || 'Error scheduling'
			setMessage(`Error scheduling: ${msg}`)
		}finally{ setSubmitting(false) }
	}

	return (
		<div>
			<h2>Schedule Interview</h2>
			<form onSubmit={onSubmit}>
				<div>
					<label>Title</label><br />
					<input value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="Interview Title" />
				</div>

				<div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
					<div style={{ flex: 1 }}>
						<label>Candidate Name</label><br />
						<input value={candidateName} onChange={e=>setCandidateName(e.target.value)} placeholder="Asha Kumar" />
					</div>
					<div style={{ flex: 1 }}>
						<label>Candidate Email</label><br />
						<input value={candidateEmail} onChange={e=>setCandidateEmail(e.target.value)} placeholder="asha@example.com" />
					</div>
				</div>

				<div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
					<div>
						<label>Scheduled At (local)</label><br />
						<input type="datetime-local" value={datetimeLocal} onChange={e=>setDatetimeLocal(e.target.value)} />
					</div>
					<div>
						<label>Duration (minutes)</label><br />
						<input type="number" value={duration} onChange={e=>setDuration(e.target.value)} min={5} max={480} />
					</div>
					<div>
						<label>Timezone (optional)</label><br />
						<input value={timezone} onChange={e=>setTimezone(e.target.value)} placeholder="Asia/Kolkata" />
					</div>
				</div>

				<div style={{ marginTop: 8 }}>
					<label>Instructions</label><br />
					<textarea value={instructions} onChange={e=>setInstructions(e.target.value)} rows={4} style={{ width: '100%' }} />
				</div>

				<div style={{ marginTop: 8 }}>
					<label>Token TTL (minutes)</label><br />
					<input type="number" value={tokenTTL} onChange={e=>setTokenTTL(e.target.value)} />
				</div>

				<div style={{ marginTop: 12 }}>
					<h3>Questions</h3>
					{questions.map((q, idx)=> (
						<div key={idx} style={{ border: '1px solid #ddd', padding: 8, marginBottom: 8 }}>
							<div style={{ display: 'flex', justifyContent: 'space-between' }}>
								<strong>Question {q.order}</strong>
								<div>
									<button type="button" onClick={()=>moveQuestion(idx, -1)}>↑</button>
									<button type="button" onClick={()=>moveQuestion(idx, 1)}>↓</button>
									<button type="button" onClick={()=>removeQuestion(idx)}>Remove</button>
								</div>
							</div>
							<div style={{ marginTop: 8 }}>
								<label>Text</label><br />
								<input value={q.text} onChange={e=>updateQuestion(idx, { text: e.target.value })} style={{ width: '100%' }} />
							</div>
							<div style={{ marginTop: 8 }}>
								<label>Examples</label><br />
								<input value={q.examples} onChange={e=>updateQuestion(idx, { examples: e.target.value })} style={{ width: '100%' }} />
							</div>
							<div style={{ marginTop: 8 }}>
								<label>Type</label><br />
								<select value={q.type} onChange={e=>updateQuestion(idx, { type: e.target.value })}>
									<option value="coding">coding</option>
									<option value="explain">explain</option>
									<option value="multiple">multiple</option>
								</select>
							</div>
						</div>
					))}
					<button type="button" onClick={addQuestion}>Add Question</button>
				</div>

				<div style={{ marginTop: 12 }}>
					<button type="submit" disabled={submitting}>{submitting ? 'Scheduling...' : 'Schedule Interview'}</button>
				</div>
			</form>
			{message && <p>{message}</p>}
			{candidateLink && (
				<div style={{ marginTop: 12, padding: 12, border: '1px solid #e6eef0', borderRadius: 8 }}>
					<strong>Candidate Link (share this):</strong>
					<div style={{ marginTop:8 }}>
						<input readOnly value={candidateLink.link} style={{ width: '100%' }} />
					</div>
					<div style={{ marginTop:8, display:'flex', gap:8 }}>
						<button onClick={() => { navigator.clipboard.writeText(candidateLink.link).catch(()=>{}); setMessage('Link copied to clipboard') }}>Copy Link</button>
						<a href={`mailto:${candidateEmail}?subject=Interview%20Link&body=Please%20join%20your%20interview:%20${encodeURIComponent(candidateLink.link)}`}><button>Open Mail</button></a>
					</div>
					<div style={{ marginTop:8, color:'#666', fontSize:13 }}>Token: {candidateLink.token}</div>
				</div>
			)}
		</div>
	)
}
