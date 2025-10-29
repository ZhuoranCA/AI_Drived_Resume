from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import re


class ResumeState(TypedDict):
    user_message: Optional[str]
    resume_md: Optional[str]
    jd_md: Optional[str]
    goal: Optional[str]
    final_resume: Optional[str]
    response: Optional[str]
    next: Optional[str]


def define_graph() -> StateGraph:
    graph = StateGraph(state_schema=ResumeState)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.6)

    def ai_speak(context: str, tone: str = "professional") -> str:
        """Generate human-like, contextual messages."""
        guidance_prompt = f"""
You are a conversational AI resume assistant speaking in a {tone} and natural tone.
You help users refine resumes professionally and politely.
Generate a short, natural response (1–3 sentences) to guide the user.

Context:
{context}
"""
        return llm.invoke([HumanMessage(content=guidance_prompt)]).content.strip()

    def is_markdown_like(text: str) -> bool:
        """Check if the text is formatted like Markdown."""
        return bool(re.search(r"(\#|\*\*|[-*]\s|\n\d+\.)", text)) and len(text.split()) > 30

    def looks_like_resume(text: str) -> bool:
        keywords = ["experience", "education", "intern", "engineer", "project", "skills"]
        return any(k.lower() in text.lower() for k in keywords)

    def looks_like_jd(text: str) -> bool:
        jd_keywords = ["responsibilities", "requirements", "position", "we are looking for", "team"]
        return any(k.lower() in text.lower() for k in jd_keywords)

    def handle_input(state: ResumeState) -> ResumeState:
        """Classify and process the user input."""
        user_input = (state.get("user_message") or "").strip().lower()
        resume = state.get("resume_md")
        jd = state.get("jd_md")
        final_resume = state.get("final_resume")

        # === Handle end condition ===
        if user_input in ["done", "finish", "end"]:
            msg = ai_speak("Great! The resume optimization process is complete. Wishing you success in your job search!")
            return {"response": msg, "next": None}

        # === Continue refining ===
        if final_resume and not any(keyword in user_input for keyword in ["resume", "jd", "goal", "optimize"]):
            msg = ai_speak("Got it. Refining your current resume according to your new instructions...")
            return {"response": msg, "next": "refine"}

        # === Optimization trigger ===
        if user_input == "optimize" or "optimize" in user_input:
            if not (resume and jd):
                msg = ai_speak("You need to provide both a resume and a job description before optimizing.")
                return {"response": msg}
            msg = ai_speak("Optimization starting now.")
            return {"response": msg, "next": "rewrite"}

        # === Classification for new data ===
        classification_prompt = f"""
You are an input classifier for a resume optimization assistant.
Classify this input into one of: Resume, JD, Goal, Other.

Input:
{user_input}
"""
        classification = llm.invoke([HumanMessage(content=classification_prompt)]).content.strip().lower()

        if "resume" in classification:
            if not is_markdown_like(user_input):
                msg = ai_speak("The resume doesn’t appear to be in Markdown format. Please reformat it properly.")
                return {"response": msg}
            if not looks_like_resume(user_input):
                msg = ai_speak("The text doesn’t look like a resume. Please include sections such as Experience and Education.")
                return {"response": msg}
            msg = ai_speak("Resume received. Please provide the job description next.")
            return {"resume_md": user_input, "response": msg}

        elif "jd" in classification:
            if not looks_like_jd(user_input):
                msg = ai_speak("The job description seems incomplete. Please paste the full version including Responsibilities and Requirements.")
                return {"response": msg}
            msg = ai_speak("Job description received. You can now type 'optimize' to begin alignment.")
            return {"jd_md": user_input, "response": msg}

        else:
            msg = ai_speak("I didn’t quite understand that. You can provide a resume, job description, or ask for optimization.")
            return {"response": msg}

    def rewrite_resume(state: ResumeState) -> ResumeState:
        """Generate the first optimized resume."""
        prompt = f"""
You are a professional resume optimization assistant.

Revise the following resume to align with the job description.

### Resume
{state['resume_md']}

### Job Description
{state['jd_md']}

### Goal
{state.get('goal', 'Align the resume with the job description for maximum relevance.')}

Rules:
- Output only the optimized resume in Markdown.
- Preserve key experience.
- Highlight relevant skills and results.
"""
        optimized = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        summary = ai_speak("Here’s your optimized resume. You can ask me to adjust it further (e.g., emphasize Azure, shorten Experience, etc.).")

        return {
            "final_resume": optimized,
            "resume_md": optimized,
            "response": summary + "\n\n" + optimized
        }

    def refine_resume(state: ResumeState) -> ResumeState:
        """Refine existing optimized resume based on user feedback."""
        prompt = f"""
You are a resume refinement assistant.

The current optimized resume is:
{state['final_resume']}

User's latest instruction:
{state['user_message']}

Revise the resume accordingly. Maintain Markdown format and professionalism.
Output only the full updated resume in Markdown.
"""
        refined = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        summary = ai_speak("I've refined your resume based on your feedback. You can continue adjusting until you're "
                           "satisfied.")

        return {
            "final_resume": refined,
            "resume_md": refined,
            "response": summary + "\n\n" + refined
        }

    # === Graph definition ===
    graph.add_node("handle_input", handle_input)
    graph.add_node("rewrite_resume", rewrite_resume)
    graph.add_node("refine_resume", refine_resume)

    graph.add_conditional_edges(
        "handle_input",
        lambda s: "rewrite_resume" if s.get("next") == "rewrite"
        else "refine_resume" if s.get("next") == "refine"
        else END,
        {"rewrite_resume": "rewrite_resume", "refine_resume": "refine_resume", END: END},
    )

    graph.add_edge("rewrite_resume", END)
    graph.add_edge("refine_resume", END)
    graph.set_entry_point("handle_input")

    return graph
