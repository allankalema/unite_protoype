import json
import os
from urllib import error, request


def _build_prompt(user_message, course=None, lesson=None, history=None, teacher_name="Teacher"):
    history = history or []
    course_title = course.title if course else "General teacher development"
    learning_objectives = course.learning_objectives if course else ""
    module_title = lesson.module.title if lesson and lesson.module else "N/A"
    lesson_title = lesson.title if lesson else "N/A"
    lesson_summary = ""
    lesson_ai_summary = ""
    lesson_content = ""

    if lesson:
        lesson_summary = lesson.summary or ""
        lesson_ai_summary = lesson.ai_summary or ""
        lesson_content = lesson.content[:3500] if lesson.content else ""

    recent_history = "\n".join(
        [f"{item.get('role', 'user')}: {item.get('message', '')}" for item in history[-8:]]
    )

    return f"""
You are an AI tutor for Uganda National Institute for Teacher Education (UNITE).
Your role: patient, practical, and clear teacher-trainer assistant.

Rules:
- Keep explanations simple, structured, and classroom-relevant.
- Prefer bullet points and concrete examples for Uganda teacher contexts.
- If a direct answer is not in provided lesson/course context, explicitly say so.
- When context is missing, still give a helpful general explanation and suggest what to review.
- Avoid fabricating specific policy details.
- Focus on teacher training and instructional improvement.

Context:
Course: {course_title}
Course learning objectives: {learning_objectives}
Module: {module_title}
Lesson: {lesson_title}
Lesson summary: {lesson_summary}
Lesson AI summary: {lesson_ai_summary}
Lesson content excerpt:
{lesson_content}

Conversation history:
{recent_history}

Teacher question:
{user_message}

Important style:
- Address the teacher naturally by name when appropriate: {teacher_name}.
- Use normal apostrophes in contractions (e.g., I'm, don't). Do not use escaped forms like \\u0027.
""".strip()


def _call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "missing_api_key"

    primary_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    candidate_models = [
        primary_model,
        "gemini-flash-latest",
        "gemini-2.0-flash",
    ]
    unique_models = []
    for model in candidate_models:
        if model and model not in unique_models:
            unique_models.append(model)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 700,
        },
    }

    for model_name in unique_models:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent?key={api_key}"
        )
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=40) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                candidates = response_data.get("candidates", [])
                if not candidates:
                    return None, "empty_candidates"

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return None, "empty_parts"

                text_chunks = [part.get("text", "") for part in parts if part.get("text")]
                text = "\n".join(text_chunks).strip()
                if not text:
                    return None, "empty_text"
                return text, None
        except error.HTTPError as exc:
            status_code = getattr(exc, "code", None)
            if status_code == 404:
                continue
            body = ""
            try:
                body = exc.read().decode("utf-8", "ignore")
            except Exception:
                body = ""
            return None, f"http_error_{status_code}:{body[:220]}"
        except Exception:
            return None, "connection_error"

    return None, "model_not_found"


def generate_ai_response(user_message, course=None, lesson=None, history=None, teacher_name="Teacher"):
    prompt = _build_prompt(
        user_message,
        course=course,
        lesson=lesson,
        history=history,
        teacher_name=teacher_name,
    )
    result, code = _call_gemini(prompt)
    if result:
        return result

    if code == "missing_api_key":
        return (
            "AI tutor is not configured yet. Add GEMINI_API_KEY to your environment to enable live responses. "
            "For now, review the lesson summary and key objectives."
        )
    if code and code.startswith("http_error_"):
        return (
            "The AI tutor request failed. Please verify GEMINI_API_KEY, Gemini API enablement, and quota. "
            f"Details: {code}"
        )
    if code == "model_not_found":
        return (
            "Configured Gemini model is not available for generateContent. "
            "Set GEMINI_MODEL in .env to a supported model such as gemini-2.5-flash."
        )
    if code in {"empty_candidates", "empty_parts", "empty_text"}:
        return "I could not generate a response right now. Please try again shortly."
    return "AI tutor encountered a connection issue. Please try again in a moment."


def generate_lesson_summary(lesson):
    prompt = f"""
You are supporting teacher professional development at UNITE.
Summarize this lesson for teachers in Uganda in simple, practical language.
Return:
1) A concise summary (4-6 bullet points)
2) Keywords line starting with 'Keywords:'

Lesson title: {lesson.title}
Lesson type: {lesson.lesson_type}
Course: {lesson.module.course.title}
Course objectives: {lesson.module.course.learning_objectives}
Current lesson summary: {lesson.summary}
Lesson content:
{lesson.content[:5000]}
""".strip()
    result, _ = _call_gemini(prompt)
    if not result:
        return "AI tutor encountered a connection issue. Please try again in a moment."
    return result
