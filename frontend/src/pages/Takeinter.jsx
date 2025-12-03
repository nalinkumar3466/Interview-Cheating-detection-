import React from "react";
import { useParams } from 'react-router-dom'

export default function TakeInterview(){
	const { id } = useParams()
	return <div><h2>Take Interview — {id}</h2><p>Placeholder for interviewer/candidate UI</p></div>
}
