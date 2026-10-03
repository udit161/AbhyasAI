import json
import time
from typing import List, Dict, Any
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service

# Mock Test Dataset
TEST_QUERIES = [
    {
        "id": "scenario_1_past_content",
        "description": "Question about content discussed BEFORE the current timestamp",
        "query": "Why do we use timestamp boundary enforcement in interactive learning?",
        "video_id": "vid_sample_1",
        "current_timestamp": 900.0,  # 15:00
        "permitted_doc_ids": [],
        "expected_found": True,
        "expected_refusal": False
    },
    {
        "id": "scenario_2_future_content",
        "description": "Question about content covered LATER in the lecture",
        "query": "Tell me about AWS Neptune integration and graph retrieval.",
        "video_id": "vid_sample_1",
        "current_timestamp": 300.0,  # 05:00 (Neptune is at 18:42)
        "permitted_doc_ids": [],
        "expected_found": False,
        "expected_refusal": True
    },
    {
        "id": "scenario_3_pdf_content",
        "description": "Question answered by a permitted PDF/PPT",
        "query": "What are the core prerequisites listed in the syllabus?",
        "video_id": "vid_sample_1",
        "current_timestamp": 0.0,
        "permitted_doc_ids": ["cs101_syllabus"],
        "expected_found": True,
        "expected_refusal": False
    },
    {
        "id": "scenario_4_out_of_bounds",
        "description": "Out-of-bounds question not present in any resource",
        "query": "Who won the World Series in 2024?",
        "video_id": "vid_sample_1",
        "current_timestamp": 3600.0,
        "permitted_doc_ids": ["cs101_syllabus"],
        "expected_found": False,
        "expected_refusal": True
    }
]

def run_evaluation():
    print("=========================================")
    print("Starting Automated RAG Evaluation Script")
    print("=========================================\n")

    metrics = {
        "total_queries": len(TEST_QUERIES),
        "correct_retrievals": 0,
        "correct_refusals": 0,
        "citation_formats_valid": 0,
        "hallucinations_detected": 0
    }

    for test in TEST_QUERIES:
        print(f"Running Test: [{test['id']}] - {test['description']}")
        print(f"Query: '{test['query']}'")
        print(f"Current Timestamp: {test['current_timestamp']}s")
        
        # 1. Test Retrieval
        retrieved_contexts = retrieval_service.retrieve_grounded_context(
            query=test["query"],
            video_id=test["video_id"],
            current_timestamp=test["current_timestamp"],
            permitted_doc_ids=test["permitted_doc_ids"],
            top_k=3
        )
        
        found_relevant_context = len(retrieved_contexts) > 0
        if found_relevant_context == test["expected_found"]:
            metrics["correct_retrievals"] += 1
            print(" ✓ Retrieval filter behaved as expected.")
        else:
            print(" ✗ Retrieval filter failed expectation.")

        # 2. Test LLM Generation
        answer, citations, is_refusal, latency = llm_service.generate_grounded_answer(
            question=test["query"],
            retrieved_contexts=retrieved_contexts,
            current_timestamp=test["current_timestamp"]
        )
        
        print(f" LLM Answer: {answer[:100]}...")
        
        # 3. Analyze Refusal & Hallucination
        if is_refusal == test["expected_refusal"]:
            metrics["correct_refusals"] += 1
            print(" ✓ Refusal logic behaved as expected.")
        else:
            if test["expected_refusal"] and not is_refusal:
                metrics["hallucinations_detected"] += 1
                print(" ✗ Hallucination detected! Model answered a restricted/out-of-bounds query.")
                
        # 4. Analyze Citation formatting
        if not is_refusal and citations:
            metrics["citation_formats_valid"] += 1
            print(f" ✓ Generated {len(citations)} strict citations.")
            
        print("-" * 50)

    # Calculate final metrics
    total = metrics["total_queries"]
    retrieval_precision = (metrics["correct_retrievals"] / total) * 100
    refusal_accuracy = (metrics["correct_refusals"] / total) * 100
    hallucination_rate = (metrics["hallucinations_detected"] / total) * 100
    
    # Citation accuracy only calculated over queries that were supposed to generate citations
    queries_with_answers = sum(1 for t in TEST_QUERIES if not t["expected_refusal"])
    citation_accuracy = (metrics["citation_formats_valid"] / queries_with_answers * 100) if queries_with_answers > 0 else 100.0

    print("\n=========================================")
    print("EVALUATION METRICS SUMMARY")
    print("=========================================")
    print(f"Retrieval Precision (Boundary Enforcement): {retrieval_precision:.1f}%")
    print(f"Citation Accuracy (Format & Presence):      {citation_accuracy:.1f}%")
    print(f"Refusal Accuracy (Anti-Spoofing):           {refusal_accuracy:.1f}%")
    print(f"Hallucination Rate:                         {hallucination_rate:.1f}%")
    print("=========================================")

if __name__ == "__main__":
    run_evaluation()
