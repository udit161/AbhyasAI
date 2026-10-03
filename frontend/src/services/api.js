import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const askQuestion = async (videoId, currentTimestamp, question, allowedResourceIds = []) => {
  const response = await axios.post(`${API_BASE_URL}/chat`, {
    user_id: "test_user_123",
    video_id: videoId,
    current_timestamp: currentTimestamp,
    query: question,
    permitted_doc_ids: allowedResourceIds
  });
  return response.data;
};

export const generateQuiz = async (videoId, currentTimestamp, numQuestions = 3) => {
  const response = await axios.post(`${API_BASE_URL}/quiz`, {
    video_id: videoId,
    current_timestamp: currentTimestamp,
    num_questions: numQuestions
  });
  return response.data;
};

export const startInterview = async (interviewParams) => {
  const response = await axios.post(`${API_BASE_URL}/interview/start`, interviewParams);
  return response.data;
};

export const submitInterviewAnswer = async (sessionId, answer) => {
  const response = await axios.post(`${API_BASE_URL}/interview/answer`, {
    session_id: sessionId,
    answer: answer
  });
  return response.data;
};

export const getInterviewScorecard = async (sessionId) => {
  const response = await axios.get(`${API_BASE_URL}/interview/scorecard/${sessionId}`);
  return response.data;
};
