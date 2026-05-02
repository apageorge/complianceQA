from src.eval_dataset import EVAL_DATASET
from src.chain import ask_question


def evaluate(chain, vectorstore, k=4, selected_docs=None):
    results = []

    for item in EVAL_DATASET:
        question = item["question"]
        expected_keywords = item["expected_keywords"]
        should_answer = item["should_answer"]

        try:
            answer, sources = ask_question(
                chain,
                question,
                [],
                k=k,
                selected_docs=selected_docs,
                vectorstore=vectorstore
            )
        except Exception as e:
            answer = f"Error: {e}"
            sources = []

        # --- Checks ---
        keyword_match = any(
            kw.lower() in answer.lower() for kw in expected_keywords
        ) if expected_keywords else False

        said_not_addressed = "not addressed" in answer.lower()

        results.append({
            "question": question,
            "answer": answer,
            "sources": sources,
            "keyword_match": keyword_match,
            "correct_fallback": (not should_answer and said_not_addressed),
            "should_answer": should_answer
        })

    return results