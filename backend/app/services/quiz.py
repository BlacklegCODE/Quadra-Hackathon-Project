import random

from ..quiz_bank import QUESTION_BANK


def build_attempt(role_title):
    bank = QUESTION_BANK[role_title]
    order = list(range(len(bank)))
    random.shuffle(order)

    items = []
    for qi in order:
        skill, question, options, correct, explanation = bank[qi]
        perm = list(range(len(options)))
        random.shuffle(perm)
        items.append(
            {
                "skill": skill,
                "question": question,
                "options": [options[p] for p in perm],
                "correct": perm.index(correct),
                "explanation": explanation,
            }
        )
    return items


def grade_attempt(items, answers):
    per_skill = {}
    review = []

    for item, chosen in zip(items, answers):
        is_correct = chosen == item["correct"]
        stats = per_skill.setdefault(item["skill"], {"correct": 0, "total": 0})
        stats["total"] += 1
        stats["correct"] += int(is_correct)
        review.append(
            {
                "skill": item["skill"],
                "question": item["question"],
                "your_answer": item["options"][chosen],
                "correct_answer": item["options"][item["correct"]],
                "explanation": item["explanation"],
                "is_correct": is_correct,
            }
        )

    for stats in per_skill.values():
        stats["level"] = int(stats["correct"] / stats["total"] * 5 + 0.5)

    return {
        "score": sum(s["correct"] for s in per_skill.values()),
        "total": len(items),
        "skills": per_skill,
        "review": review,
    }