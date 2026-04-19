from ai_scoring_pipeline.db_service import save_results

segments = [
    {
        "question": "What is Python?",
        "answer": "Python is a programming language because it is easy. For example, beginners use it.",
        "final_score": 9
    }
]

save_results("test_video.mp4", segments,interview_id=16)