import requests

def generate_mcq_with_ollama(question, answer, difficulty):
    """
    Calls the local Ollama gemma3n model to generate MCQ options for a question.
    Returns a dict: { "options": [...], "answer_index": int }
    """
    if difficulty.lower() == "easy":
        distractor_instruction = "Make the 3 incorrect options totally different from the correct answer."
    elif difficulty.lower() == "medium":
        distractor_instruction = "Make the 3 incorrect options somewhat close to the correct answer, but still wrong."
    else:
        distractor_instruction = "Make the 3 incorrect options very close to the correct answer, but still wrong."
    prompt = (
        f"Given the following question and answer, generate 4 MCQ options where one is correct and the other three are distractors. "
        f"{distractor_instruction}\n"
        f"Question: {question}\n"
        f"Correct Answer: {answer}\n"
        f"Return ONLY the result as a JSON object with keys: 'options' (a list of 4 strings), and 'answer_index' (the index of the correct answer in the list, 0-based). "
        f"Each option should be ONLY the content, WITHOUT any 'A.', 'B.', 'C.', or 'D.' or any similar prefix. Do not include any explanation or text outside the JSON."
    )
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3n:e4b-it-fp16",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        import json as pyjson
        text = response.json().get("response", "")
        # DEBUG: log the raw response for troubleshooting
        with open("ollama_mcq_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\nPROMPT:\n{prompt}\nRESPONSE:\n{text}\n{'='*40}\n")
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            mcq_json = pyjson.loads(match.group(0))
            # Post-process to remove any leading "A. ", "B. ", "C. ", "D. " or similar from options
            import re
            cleaned_options = []
            for opt in mcq_json.get("options", []):
                cleaned_opt = re.sub(r"^[A-Da-d][\.\)]\s*", "", opt).strip()
                cleaned_options.append(cleaned_opt)
            mcq_json["options"] = cleaned_options
            return mcq_json
        else:
            return None
    except Exception as e:
        with open("ollama_mcq_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\nERROR: {str(e)}\n")
        return None

def generate_mcqs_for_exam(exam):
    """
    Given an exam dict (with a 'questions' list), returns a list of MCQ dicts for each question.
    """
    mcq_results = []
    for q in exam["questions"]:
        question_text = q.get("Question")
        answer_text = q.get("Answer")
        difficulty = q.get("Difficulty", "medium")
        mcq = generate_mcq_with_ollama(question_text, answer_text, difficulty)
        if mcq:
            mcq_results.append({
                "question": question_text,
                "options": mcq.get("options"),
                "answer_index": mcq.get("answer_index"),
                "difficulty": difficulty
            })
        else:
            import random
            options = [answer_text, "", "", ""]
            random.shuffle(options)
            answer_index = options.index(answer_text)
            mcq_results.append({
                "question": question_text,
                "options": options,
                "answer_index": answer_index,
                "difficulty": difficulty
            })
    return mcq_results
