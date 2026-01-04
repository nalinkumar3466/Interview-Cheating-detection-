import api from './api'

export async function uploadInterviewRecording(interviewId, fileBlob, answer){
  const fd = new FormData()
  fd.append('file', fileBlob, fileBlob.name || `interview_${interviewId}_${Date.now()}.webm`)
  fd.append('answer', answer || '')
  return api.post(`/interviews/${interviewId}/complete`, fd, { headers: {'Content-Type':'multipart/form-data'} })
}
