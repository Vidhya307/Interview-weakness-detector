import os
from generator import generate_questions
from evaluator import evaluate_answer
from tracker import save_session, load_sessions, get_weakest_dimension
from voice import speak, listen

COLORS = {
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
    "cyan":   "\033[96m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}

def c(text, color):
    return f"{COLORS[color]}{text}{COLORS['reset']}"

def score_color(score):
    if score >= 4.0:
        return c(f"{score:.1f}", "green")
    elif score >= 2.5:
        return c(f"{score:.1f}", "yellow")
    else:
        return c(f"{score:.1f}", "red")

def get_user_profile():
    print(c("\n=== Interview Weakness Detector ===", "bold"))
    print(c("Let's personalise your session.\n", "cyan"))

    role  = input(c("What role are you preparing for? (e.g. Python Developer, Data Analyst): ", "cyan")).strip()
    level = input(c("Experience level? (Fresher / 1-2 years / 3-5 years): ", "cyan")).strip()
    focus = input(c("Any focus area? (e.g. Behavioral, System Design, General): ", "cyan")).strip()

    while True:
        try:
            count = int(input(c("How many questions this session? (1-10): ", "cyan")).strip())
            if 1 <= count <= 10:
                break
            print(c("Please enter a number between 1 and 10.", "yellow"))
        except ValueError:
            print(c("Please enter a valid number.", "yellow"))

    mode = input(c("Answer mode — type 't' for typing, 'v' for voice: ", "cyan")).strip().lower()
    voice_mode = mode == "v"
    return role, level, focus, count, voice_mode

def run_session():
    role, level, focus, count, voice_mode = get_user_profile()

    print(c("\nGenerating your personalised questions...", "cyan"))
    try:
        questions = generate_questions(role, level, focus, count)
    except Exception as e:
        print(c(f"Error generating questions: {e}", "red"))
        return

    print(c(f"\n{len(questions)} questions ready. Let's begin!\n", "green"))

    results = []

    for i, q in enumerate(questions, 1):
        print(c(f"\nQ{i} [{q['category']}]: {q['question']}", "bold"))

        if voice_mode:
            speak(f"Question {i}. {q['question']}")
            answer = listen()
            if not answer:
                print(c("Skipped — no voice detected.", "yellow"))
                continue
        else:
            print(c("Your answer (press Enter twice when done):", "cyan"))
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            answer = " ".join(lines).strip()

        if not answer:
            print(c("Skipped.", "yellow"))
            continue

        print(c("\nEvaluating...", "cyan"))

        try:
            evaluation = evaluate_answer(q["question"], q["category"], answer)
        except Exception as e:
            print(c(f"Error evaluating: {e}", "red"))
            break

        # Scores
        print(c("\n--- Your Scores ---", "bold"))
        for dim, score in evaluation["scores"].items():
            print(f"  {dim.capitalize():12} {score_color(score)}")
        print(f"\n  Overall: {score_color(evaluation['overall'])}")

        # Strengths & weaknesses
        if evaluation.get("strengths"):
            print(c(f"\n  ✅ Strength: ", "green") + evaluation["strengths"][0])
        if evaluation.get("weaknesses"):
            print(c(f"  ❌ Weakness: ", "red") + evaluation["weaknesses"][0])
        print(c(f"  💡 Tip: ", "yellow") + evaluation["tip"])

        # Ideal answer
        print(c("\n--- Ideal Answer ---", "bold"))
        print(c(evaluation.get("ideal_answer", "Not available."), "cyan"))

        # Spoken feedback (voice mode only)
        if voice_mode:
            speak(f"Your overall score is {evaluation['overall']}. {evaluation['tip']}")

        results.append({
            "question": q["question"],
            "answer": answer,
            "evaluation": evaluation
        })

    if results:
        save_session(results)
        sessions = load_sessions()
        weakest = get_weakest_dimension(sessions)

        print(c("\n=== Session Complete ===", "bold"))
        print(c(f"  Focus next on: {weakest.upper()}", "yellow"))
        print(c(f"  Sessions completed so far: {len(sessions)}\n", "cyan"))

def main():
    sessions = load_sessions()
    print(c(f"\nTotal sessions completed: {len(sessions)}", "cyan"))
    run_session()

if __name__ == "__main__":
    main()