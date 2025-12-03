import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

export default function InterviewDetails(){
  const { id } = useParams()
  const [interview, setInterview] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/interviews/${id}`)
      .then(res => setInterview(res.data))
      .catch(err => setInterview(null))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <div>
      <h2>Interview Details — {id}</h2>
      {loading && <p>Loading...</p>}
      {!loading && interview && (
        <div>
          <p>Title: {interview.title}</p>
          <p>Scheduled At: {interview.scheduled_at}</p>
        </div>
      )}
      {!loading && !interview && (
        <p>Interview not found</p>
      )}
    </div>
  )
}
