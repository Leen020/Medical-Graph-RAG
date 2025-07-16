from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import os
import sys
import argparse
import time
import logging
from print_logger import Logger
from evaluation import (
    extract_answer_letter,
    load_mcq_questions,
    save_inference_results,
    evaluate_mcq_performance,
)
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

# ─── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument(
    "-mcq_eval",
    action="store_true",
    help="Run MCQ evaluation using mcq_evaluation_medgemma.py",
)
parser.add_argument(
    "--delay",
    type=float,
    default=float(os.getenv("REQUEST_DELAY", 0.0)),
    help="Seconds to sleep after *each successful* request (default: 0)",
)
parser.add_argument(
    "-english",
    action="store_true",
    help="Use English prompts and questions (default: False, uses Turkish)",
)
args = parser.parse_args()

# ─── Logging ──────────────────────────────────────────────────────────────────
if args.english:
    sys.stdout = Logger("medgemma27B_outputs/processing_medgemma_english.log")
else:
    sys.stdout = Logger("medgemma27B_outputs/processing_medgemma_turkish.log")
sys.stderr = sys.stdout
logging.basicConfig(level=logging.INFO)

# ─── Constants ───────────────────────────────────────────────────────────────
MODEL_ID = "google/medgemma-27b-text-it"

if args.mcq_eval:
    # Use different files for MCQ evaluation
    if args.english:
        QUESTIONS_FILE = "./prompt160.json"
        RESULTS_FILE = "medgemma27B_outputs/inference_results_medgemma__eng.json"
    else:
        QUESTIONS_FILE = "./translated_cardiology_mcq.json"
        RESULTS_FILE = "medgemma27B_outputs/inference_results_medgemma__turkish.json"
else:
    if args.english:
        # Use default files for English inference
        QUESTIONS_FILE = "./prompt_english.txt"
        RESULTS_FILE = "medgemma27B_outputs/inference_results_medgemma__QA_english.txt"
    
    else:
        # Use default files for Turkish inference
        QUESTIONS_FILE = "./prompt_turkish.txt"
        RESULTS_FILE = "medgemma27B_outputs/inference_results_medgemma__QA_turkish.txt"

# ─── LLM Call with Retry ─────────────────────────────────────────────────────
client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY"))


@retry(
    stop=stop_after_attempt(5),              # try up to 5 times
    wait=wait_exponential_jitter(initial=1), # 1s, 2‑4s, 4‑8s, ...
    reraise=True,
)
def call_llm(system_message: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        # vLLM‑only extras go in extra_body
        extra_body={"top_k": 50},
    )
    return response.choices[0].message.content.strip()


def prompt(question_text: str) -> tuple[str, str]:
    if args.mcq_eval:
        if args.english:
            system_message = "You are a cardiologist expert specialized in question answering."
            user_message = f"""
                Answer the following question. Reply only with the correct option in this exact format:

                Answer: A

                Do not provide any explanation or use any other format.

                Question:
                {question_text}
            """.strip()

        else:
            system_message = "Sen kardiyoloji alanında uzman bir doktor ve çoktan seçmeli sorulara yanıt veren bir asistansın."
            
            user_message = f"""
                Aşağıdaki soruyu yanıtla. Cevabını yalnızca şu formatta ver:

                Cevap: A

                Açıklama yapma. Yukarıdaki format dışında başka bir biçim kullanma.

                Soru:
                {question_text}
            """.strip()
    else:
        if args.english:
            system_message = "You are a cardiologist expert specialized in question answering."
            user_message = f"""
                If given a patient's case, provide all possible diagnoses to the patient's case, otherwise answer the question. Add references to your answer.

                Question:
                {question_text}
            """.strip()
        else:
            system_message = "Sen kardiyoloji alanında uzman bir doktor ve soru cevaplama konusunda uzman bir asistansın."
            user_message = f"""
                Eğer bir hastanın durumu verildiyse, hastanın durumuna ilişkin tüm olası tanıları sağla, aksi takdirde soruyu yanıtla. Cevabına referanslar ekle.

                Soru:
                {question_text}
            """.strip()
    return call_llm(system_message, user_message)


def inference(prompt_content: str) -> str:
    answer = prompt(prompt_content)
    # Optional fixed pause between successful requests
    if args.delay > 0:
        time.sleep(args.delay)
    return answer


# ─── Main Logic ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if args.mcq_eval:
        mcq_questions = load_mcq_questions(QUESTIONS_FILE)
        inference_results = []

        for idx, question_data in enumerate(mcq_questions):
            question_text = question_data["question"] + "\nAnswer the following question and explain."
            question_id = question_data["question_id"]
            correct_answer = question_data["answer_letter"]

            logging.info(f"Processing Question {idx+1} (ID: {question_id})")
            response = inference(question_text)
            predicted_letter = extract_answer_letter(response)

            inference_results.append(
                {
                    "question_id": question_id,
                    "question": question_text,
                    "full_answer": response,
                    "predicted_letter": predicted_letter,
                    "answer_letter": correct_answer,
                }
            )
            print(f"Question: {question_text}")
            print(f"Model Answer: {response}")
            logging.info(
                f"✔ Extracted: {predicted_letter} – Correct: {correct_answer} "
                f"({'✅' if predicted_letter == correct_answer else '❌'})"
            )

        save_inference_results(inference_results, RESULTS_FILE)
        evaluate_mcq_performance(inference_results)

    else:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            prompt_content = f.read().strip()

        response = inference(
            "If given a patient's case, provide all possible diagnoses to the patient's "
            "case, otherwise answer the question. Add references to your answer\n" + prompt_content
        )

        with open(RESULTS_FILE, "w", encoding="utf-8") as out:
            out.write(response)

        logging.info("Response saved to %s", RESULTS_FILE)
