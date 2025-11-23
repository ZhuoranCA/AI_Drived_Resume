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

    # === Helper: conversational AI reply ===
    def ai_speak(context: str, tone: str = "professional") -> str:
        guidance_prompt = f"""
You are a conversational AI resume assistant speaking in a {tone} and natural tone.
You help users refine resumes professionally and politely.
Generate a short, natural response (1–3 sentences) to guide the user.

Context:
{context}
"""
        return llm.invoke([HumanMessage(content=guidance_prompt)]).content.strip()

    # === Helper: AI extraction of Markdown resume ===
    def extract_resume_md(raw_text: str) -> str:
        """Extract ONLY the Markdown resume section from user input."""
        extract_prompt = f"""
You are an assistant that extracts ONLY the Markdown resume content from user input.

Rules:
- Output ONLY the Markdown resume content, exactly as written.
- Do NOT rewrite, modify, summarize, fix, or correct.
- Preserve original formatting, spacing, indentation, and capitalization.
- If multiple sections exist, return only the resume.
- If no valid resume is found, return an empty string.

User Input:
{raw_text}
"""
        result = llm.invoke([HumanMessage(content=extract_prompt)]).content.strip()
        return result

    # === Basic validators ===
    def is_markdown_like(text: str) -> bool:
        return bool(re.search(r"(\#|\*\*|[-*]\s|\n\d+\.)", text)) and len(text.split()) > 30

    def looks_like_resume(text: str) -> bool:
        keywords = ["experience", "education", "intern", "engineer", "project", "skills"]
        return any(k.lower() in text.lower() for k in keywords)

    def looks_like_jd(text: str) -> bool:
        jd_keywords = ["responsibilities", "requirements", "position", "we are looking for", "team"]
        return any(k.lower() in text.lower() for k in jd_keywords)

    # === Main input handler ===
    def handle_input(state: ResumeState) -> ResumeState:
        # Keep original raw text (don’t lowercase)
        user_input_raw = state.get("user_message") or ""
        # Only use lowercase for classification
        user_input_lc = user_input_raw.lower()

        resume = state.get("resume_md")
        jd = state.get("jd_md")
        final_resume = state.get("final_resume")

        # === End process ===
        if user_input_lc in ["done", "finish", "end"]:
            msg = ai_speak("Great! The resume optimization process is complete. Wishing you success!")
            return {"response": msg, "next": None}

        # === Refinement path ===
        if final_resume and not any(k in user_input_lc for k in ["resume", "jd", "goal", "optimize"]):
            msg = ai_speak("Got it. Refining your current resume according to your new instructions...")
            return {"response": msg, "next": "refine"}

        # === Optimization trigger ===
        if "optimize" in user_input_lc:
            if not (resume and jd):
                msg = ai_speak("You need to provide both a resume and a job description before optimizing.")
                return {"response": msg}
            msg = ai_speak("Optimization starting now.")
            return {"response": msg, "next": "rewrite"}

        # === Classification ===
        classification_prompt = f"""
You are an input classifier for a resume optimization assistant.
Classify this input into one of: Resume, JD, Goal, Other.

Input:
{user_input_raw}
"""
        classification = llm.invoke([HumanMessage(content=classification_prompt)]).content.strip().lower()

        # === Resume input ===
        if "resume" in classification:
            if not looks_like_resume(user_input_raw):
                msg = ai_speak("The text doesn’t look like a resume. Please include sections such as Experience and Education.")
                return {"response": msg}

            # Extract only the resume part via GPT
            extracted = extract_resume_md(user_input_raw)

            if not extracted or len(extracted) < 20:
                msg = ai_speak("I couldn't detect a valid Markdown resume in your input. Please paste it again.")
                return {"response": msg}

            # Save resume exactly, no modifications
            msg = ai_speak("Resume received. Please provide the job description next.")
            return {"resume_md": extracted, "response": msg}

        # === Job description input ===
        elif "jd" in classification:
            if not looks_like_jd(user_input_raw):
                msg = ai_speak("The job description seems incomplete. Please paste the full Responsibilities and Requirements section.")
                return {"response": msg}
            msg = ai_speak("Job description received. You can now type 'optimize' to begin alignment.")
            return {"jd_md": user_input_raw, "response": msg}

        # === Other ===
        else:
            msg = ai_speak("I didn't quite understand that. You can provide a resume, job description, or ask for optimization.")
            return {"response": msg}

    # === Optimizer ===
    def rewrite_resume(state: ResumeState) -> ResumeState:
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
        summary = ai_speak("Here’s your optimized resume. You can ask me to adjust it further.")
        return {
            "final_resume": optimized,
            "resume_md": optimized,
            "response": summary + "\n\n" + optimized
        }

    # === Refinement ===
    def refine_resume(state: ResumeState) -> ResumeState:
        prompt = f"""
You are a resume refinement assistant.

The current optimized resume is:
{state['final_resume']}

User's latest instruction:
{state['user_message']}

Revise the resume accordingly. Maintain Markdown format.
Output only the full updated resume in Markdown.
"""
        refined = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        summary = ai_speak("I've refined your resume based on your feedback.")
        return {
            "final_resume": refined,
            "resume_md": refined,
            "response": summary + "\n\n" + refined
        }

    # === Graph wiring ===
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
