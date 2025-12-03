import React, { useState } from "react";
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

export default function ScheduleInterview(){
	const [title, setTitle] = useState('')
	const [datetime, setDatetime] = useState('')
	const [message, setMessage] = useState(null)
	const navigate = useNavigate()

	const onSubmit = async (e) => {
		e.preventDefault()
		setMessage(null)
		try {
			const res = await api.post('/interviews', { title, scheduled_at: datetime })
			setMessage(`Scheduled with id ${res.data.id}`)
			setTitle('')
			setDatetime('')
			// redirect to dashboard
			navigate('/')
		} catch (err) {
			// better error reporting for debugging
			console.error('Schedule submit error:', err)
			const msg = err?.response?.data?.detail || err?.message || 'Error scheduling'
			setMessage(`Error scheduling: ${msg}`)
		}
	}

	return (
		<div>
			<h2>Schedule Interview</h2>
			<form onSubmit={onSubmit}>
				<div>
					<label>Title</label><br />
					<input value={title} onChange={(e)=>setTitle(e.target.value)} placeholder="Interview Title" />
				</div>
				<div style={{ marginTop: 8 }}>
					<label>Scheduled At</label><br />
					<input value={datetime} onChange={(e)=>setDatetime(e.target.value)} placeholder="2025-12-02T15:00:00" />
				</div>
				<button style={{ marginTop: 8 }} type="submit">Schedule</button>
			</form>
			{message && <p>{message}</p>}
		</div>
	)
}
