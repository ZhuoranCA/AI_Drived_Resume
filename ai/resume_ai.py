from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import re
from playwright.sync_api import sync_playwright


class ResumeState(TypedDict):
    user_message: Optional[str]
    resume_md: Optional[str]
    jd_md: Optional[str]
    goal: Optional[str]
    final_resume: Optional[str]
    response: Optional[str]
    next: Optional[str]


# === Sync JD Extractor using Playwright ===
def fetch_jd_from_url(url: str) -> str:
    """Fetch raw webpage text using Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)
            text = page.inner_text("body")
        except Exception:
            text = ""

        browser.close()
        return text


def define_graph(model_name: str = "gpt-4o-mini", temperature: float = 0.6) -> StateGraph:
    graph = StateGraph(state_schema=ResumeState)
    llm = ChatOpenAI(model=model_name, temperature=temperature)

    # === Helper: Conversational Reply ===
    def ai_speak(context: str, tone: str = "professional") -> str:
        prompt = f"""
You are a conversational AI resume assistant speaking in a {tone} tone.
Provide a short (1–3 sentence) natural reply.

Context:
{context}
"""
        return llm.invoke([HumanMessage(content=prompt)]).content.strip()

    # === Helper: Extract ONLY resume Markdown ===
    def extract_resume_md(raw_text: str) -> str:
        prompt = f"""
Extract ONLY the Markdown resume from the text strictly.

Rules:
- Do NOT modify content
- Do NOT fix formatting
- Return only the resume section

Input:
{raw_text}
"""
        return llm.invoke([HumanMessage(content=prompt)]).content.strip()

    # Validators
    def looks_like_resume(text: str) -> bool:
        keywords = ["experience", "education", "project", "skills", "engineer", "intern"]
        return any(k in text.lower() for k in keywords)

    def looks_like_jd(text: str) -> bool:
        jd_keywords = ["responsibilities", "requirements", "team", "position"]
        return any(k in text.lower() for k in jd_keywords)

    # === Main Input Handler ===
    def handle_input(state: ResumeState) -> ResumeState:
        user_input_raw = state.get("user_message") or ""
        resume = state.get("resume_md")
        jd = state.get("jd_md")
        final_resume = state.get("final_resume")

        # === 1) Extract URL from arbitrary input ===
        url_pattern = r"(https?://[^\s]+)"
        match = re.search(url_pattern, user_input_raw)
        if match:
            real_url = match.group(0)

            # Step 1: Crawl webpage
            raw_text = fetch_jd_from_url(real_url)

            # Step 2: AI clean the JD
            clean_prompt = f"""
Extract ONLY the job description (cleaned) from the following webpage text.

Include:
- Job Title
- Responsibilities
- Requirements
- Skills
- Qualifications

Remove:
- Ads, navigation bars, cookie notices,
- Footer text, sidebars, salary widgets, FAQs

Output in clean Markdown.

Webpage text:
{raw_text}
"""
            jd_clean = llm.invoke([HumanMessage(content=clean_prompt)]).content.strip()

            if not jd_clean or len(jd_clean.split()) < 30:
                return {"response": ai_speak("I visited the link but couldn't extract a valid job description.")}

            return {
                "jd_md": jd_clean,
                "response": ai_speak("Job description successfully extracted! Type 'optimize' when you're ready.")
            }

        # === End ===
        user_input_lc = user_input_raw.lower()
        if user_input_lc in ["done", "finish", "end"]:
            return {"response": ai_speak("The resume optimization process is complete."), "next": None}

        # === Refinement ===
        if final_resume and not any(k in user_input_lc for k in ["resume", "jd", "goal", "optimize"]):
            return {"response": ai_speak("Understood. Refining your resume..."), "next": "refine"}

        # === Optimization Start ===
        if "optimize" in user_input_lc:
            if not (resume and jd):
                return {"response": ai_speak("Please provide both a resume and a job description first.")}
            return {"response": ai_speak("Optimization starting..."), "next": "rewrite"}

        # === Classification ===
        class_prompt = f"""
Classify the input into: Resume, JD, Goal, Other.

Input:
{user_input_raw}
"""
        cls = llm.invoke([HumanMessage(content=class_prompt)]).content.strip().lower()

        # === Resume Input ===
        if "resume" in cls:
            if not looks_like_resume(user_input_raw):
                return {"response": ai_speak("This doesn't look like a resume. Please include Experience or Education.")}

            extracted = extract_resume_md(user_input_raw)
            if not extracted or len(extracted) < 20:
                return {"response": ai_speak("I couldn't detect a Markdown resume. Please paste it again.")}

            return {
                "resume_md": extracted,
                "response": ai_speak("Resume received! Now please provide the job description.")
            }

        # === JD Input ===
        if "jd" in cls:
            if not looks_like_jd(user_input_raw):
                return {"response": ai_speak("This job description seems incomplete. Please add Responsibilities or Requirements.")}

            return {
                "jd_md": user_input_raw,
                "response": ai_speak("Job description received! Type 'optimize' to proceed.")
            }

        # === Otherwise ===
        return {"response": ai_speak("I didn’t quite understand. You can provide a resume or a job description.")}

    # === Rewrite Resume ===
    def rewrite_resume(state: ResumeState) -> ResumeState:
        prompt = f"""
Optimize the following resume based on the job description.

### Resume
{state['resume_md']}

### Job Description
{state['jd_md']}

###
- Extract all technical skills, tools, frameworks, languages, cloud platforms, databases, and methodologies mentioned in the job description.
- If any of these skills are missing in the resume, add them to the Skills section in a natural and truthful way.
- Do NOT invent experience; only add skills that match the applicant’s existing background or can be reasonably inferred.
- If resume already contains a Skills section, expand it. Otherwise, create a concise Skills section.
- Ensure the resume remains consistent and believable while maximizing keyword alignment to pass ATS filters.

Output ONLY the improved resume in Markdown.
"""
        optimized = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        summary = ai_speak("Here is your optimized resume.")

        return {
            "final_resume": optimized,
            "resume_md": optimized,
            "response": summary + "\n\n" + optimized
        }

    # === Refinement ===
    def refine_resume(state: ResumeState) -> ResumeState:
        prompt = f"""
Refine the following resume based on the user’s new instructions.

### Resume
{state['final_resume']}

### Instruction
{state['user_message']}

Output ONLY the revised resume in Markdown.
"""
        refined = llm.invoke([HumanMessage(content=prompt)]).content.strip()
        summary = ai_speak("Your resume has been updated.")

        return {
            "final_resume": refined,
            "resume_md": refined,
            "response": summary + "\n\n" + refined
        }

    # === Graph Build ===
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
