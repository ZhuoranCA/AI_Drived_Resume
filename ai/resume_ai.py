from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage


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
        """Generate natural assistant messages."""
        guidance_prompt = f"""
You are a conversational AI resume assistant speaking in a {tone} and natural tone.
You help users refine resumes professionally and politely.
Generate a short, human-like response (1–3 sentences) to guide the user.

Context:
{context}
"""
        return llm.invoke([HumanMessage(content=guidance_prompt)]).content.strip()

    def handle_input(state: ResumeState) -> ResumeState:
        """Classify user input and determine what to do next."""
        user_input = (state.get("user_message") or "").strip()
        resume = state.get("resume_md")
        jd = state.get("jd_md")
        goal = state.get("goal")

        # === 1️⃣ 自动识别 resume+JD 齐全 ===
        if resume and jd and not user_input:
            msg = ai_speak("Both resume and job description are present. Proceeding directly to optimization.")
            return {"response": msg, "next": "rewrite"}

        # === 2️⃣ 分类输入 ===
        classification_prompt = f"""
You are an input classifier for a resume optimization assistant.
Classify this input into one of: Resume, JD, Goal, Optimize, Other.

Input:
{user_input}

Output exactly one label.
"""
        if not user_input:
            msg = ai_speak("Waiting for user input, please provide either your resume or job description.",
                           tone="welcoming")
            return {"response": msg}

        classification = llm.invoke([HumanMessage(content=classification_prompt)]).content.strip().lower()

        # === 3️⃣ 根据分类处理 ===
        if "resume" in classification:
            msg = ai_speak("Resume received. Please provide the job description next.")
            return {"resume_md": user_input, "response": msg}

        elif "jd" in classification:
            msg = ai_speak("Job description received. You can now type 'optimize' to begin alignment.")
            return {"jd_md": user_input, "response": msg}

        elif "goal" in classification:
            msg = ai_speak("Goal noted. It will be used to guide optimization.")
            return {"goal": user_input, "response": msg}

        elif "optimize" in classification:
            if not resume and not jd:
                msg = ai_speak("You haven't provided a resume or JD yet. Please upload both to start.")
                return {"response": msg}
            elif not resume:
                msg = ai_speak("Please upload your resume before optimization.")
                return {"response": msg}
            elif not jd:
                msg = ai_speak("Please provide a job description before optimization.")
                return {"response": msg}
            msg = ai_speak("Optimization starting now.")
            return {"response": msg, "next": "rewrite"}

        else:
            msg = ai_speak("I'm not sure what that means — please share your resume or JD.")
            return {"response": msg}

    def rewrite_resume(state: ResumeState) -> ResumeState:
        """Optimize resume based on JD and goal."""
        if not (state.get("resume_md") and state.get("jd_md")):
            msg = ai_speak("Optimization requested but missing information.")
            return {"response": msg}

        prompt = f"""
You are a professional resume optimization assistant.

Revise the following resume to align with the given job description.

### Resume
{state['resume_md']}

### Job Description
{state['jd_md']}

### Optimization Goal
{state.get('goal', 'Align with job description requirements for best match.')}

Rules:
- Output only the optimized resume in Markdown.
- Keep the tone professional.
- Emphasize relevant skills and achievements matching the JD.
"""
        optimized = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        summary = ai_speak("Optimization completed. Here is the refined version of the resume:")

        return {
            "final_resume": optimized,
            "resume_md": optimized,
            "response": summary + "\n\n" + optimized
        }

    graph.add_node("handle_input", handle_input)
    graph.add_node("rewrite_resume", rewrite_resume)

    graph.add_conditional_edges(
        "handle_input",
        lambda s: "rewrite_resume" if s.get("next") == "rewrite" else END,
        {"rewrite_resume": "rewrite_resume", END: END},
    )

    graph.add_edge("rewrite_resume", END)
    graph.set_entry_point("handle_input")

    # ✅ 7️⃣ 最关键：返回 graph
    return graph
