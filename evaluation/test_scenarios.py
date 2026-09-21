import unittest
import requests

BASE_URL = "http://localhost:8000/api/v1"

class TestTimestampAwareRetrieval(unittest.TestCase):
    def test_past_content_question(self):
        """Question about content discussed BEFORE current timestamp (18:42 / 1122s)"""
        payload = {
            "video_id": "video_sample_1",
            "current_timestamp": 1122.0,
            "question": "What is timestamp-aware vector retrieval?"
        }
        res = requests.post(f"{BASE_URL}/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["is_refusal"])
        self.assertGreater(len(data["citations"]), 0)

    def test_future_content_question(self):
        """Question about content discussed LATER in the lecture (after 18:42)"""
        payload = {
            "video_id": "video_sample_1",
            "current_timestamp": 300.0, # at 5:00 min mark
            "question": "What is AWS Neptune and graph retrieval?"
        }
        res = requests.post(f"{BASE_URL}/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        # Should refuse or state content hasn't been reached yet
        print("Future content response:", data["answer"])

if __name__ == "__main__":
    unittest.main()
