from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import os


class ResumeState(TypedDict):
    user_message: Optional[str]
    resume_md: Optional[str]
    jd_md: Optional[str]
    goal: Optional[str]
    final_resume: Optional[str]
    response: Optional[str]


def define_graph() -> StateGraph:
    graph = StateGraph(state_schema=ResumeState)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.6)

    def ai_speak(context: str, tone: str = "professional") -> str:
        """让模型根据语境生成自然的系统回复"""
        guidance_prompt = f"""
You are a conversational AI resume assistant speaking in a {tone} and natural tone.
You help users refine resumes professionally and politely.
Generate a single short message (1–3 sentences) to guide or respond based on this situation:

Context:
{context}

Rules:
- Sound natural, friendly, and confident.
- Do not use emojis or exclamation marks.
- Keep sentences concise and human-like.
- Avoid repeating the same phrases across replies.
"""
        return llm.invoke([HumanMessage(content=guidance_prompt)]).content.strip()

    def handle_input(state: ResumeState) -> ResumeState:
        user_input = state.get("user_message", "").strip()
        resume = state.get("resume_md")
        jd = state.get("jd_md")
        goal = state.get("goal")

        if not user_input and not resume and not jd:
            msg = ai_speak(
                "The user has just started the conversation.",
                tone="welcoming"
            )
            return {"response": msg}

        classification_prompt = f"""
You are an intelligent input classifier for a resume optimization assistant.
Your task is to determine what kind of text the user provided.

User input:
{user_input}

Decide which category best fits this text:
1. Resume
2. Job description
3. Optimization goal
4. Command to start optimization (e.g. 'optimize', 'start', 'run')
5. General or unrelated message

Respond with only one word from this list: Resume, JD, Goal, Optimize, Other.
"""
        classification = llm.invoke([HumanMessage(content=classification_prompt)]).content.strip().lower()

        if "resume" in classification:
            msg = ai_speak(
                "The user just provided a resume. Acknowledge receipt and ask for the job description next."
            )
            return {"resume_md": user_input, "response": msg}

        elif "jd" in classification:
            msg = ai_speak(
                "The user has provided a job description. Confirm receipt and guide them to type 'optimize' when ready."
            )
            return {"jd_md": user_input, "response": msg}

        elif "goal" in classification:
            msg = ai_speak(
                "The user mentioned a goal or focus area for optimization. Confirm it and suggest proceeding when ready."
            )
            return {"goal": user_input, "response": msg}

        elif "optimize" in classification:
            if not resume:
                msg = ai_speak("The user tried to start optimization but hasn't uploaded a resume yet.")
                return {"response": msg}
            if not jd:
                msg = ai_speak("The user tried to start optimization but hasn't provided a job description yet.")
                return {"response": msg}
            msg = ai_speak("The user is ready to optimize. Acknowledge and indicate that optimization is starting.")
            return {"response": msg, "goal": goal or "align with JD"}

        msg = ai_speak(
            "The user's input was unclear. Politely ask for clarification and suggest sharing resume or job description."
        )
        return {"response": msg}

    def rewrite_resume(state: ResumeState) -> ResumeState:
        if not state.get("resume_md") or not state.get("jd_md"):
            msg = ai_speak("Optimization was requested but required information is missing.")
            return {"response": msg}

        prompt = f"""
You are a professional career coach and resume optimization expert.

Revise the candidate’s resume to better align with the given job description.

### Resume (Original)
{state['resume_md']}

### Job Description
{state['jd_md']}

### Optimization Goal
{state.get('goal', 'align with API and microservices requirements')}

### Requirements:
- Output only the optimized resume in Markdown.
- Keep the tone professional and natural.
- Preserve factual accuracy and structure.
- Align with relevant job description keywords.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        optimized_resume = response.content

        msg = ai_speak("The optimization is complete. Explain briefly what was done and then present the new resume.")
        return {"final_resume": optimized_resume, "response": msg + "\n\n" + optimized_resume}

    graph.add_node("handle_input", handle_input)
    graph.add_node("rewrite_resume", rewrite_resume)

    graph.add_conditional_edges(
        "handle_input",
        lambda s: "rewrite_resume" if "starting" in s.get("response", "").lower() else END,
        {"rewrite_resume": "rewrite_resume", END: END},
    )
    graph.add_edge("rewrite_resume", END)
    graph.set_entry_point("handle_input")
    return graph
