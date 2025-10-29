from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

load_dotenv()


class ResumeState(TypedDict):
    resume_md: Optional[str]
    jd_md: Optional[str]
    goal: Optional[str]
    final_resume: Optional[str]


def define_graph():
    graphState = StateGraph(state_schema=ResumeState)

    # ---------- 节点函数 ----------
    def input_resume_and_jd(state: ResumeState) -> ResumeState:
        print("📄 请输入你的简历 (Markdown)：(END 结束)")
        resume_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            resume_lines.append(line)
        resume_md = "\n".join(resume_lines)

        print("\n💼 请输入职位描述 (Job Description)：(END 结束)")
        jd_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            jd_lines.append(line)
        jd_md = "\n".join(jd_lines)

        return {"resume_md": resume_md, "jd_md": jd_md}

    def choose_focus(state: ResumeState) -> ResumeState:
        print("\n🎯 你希望本次优化的重点是什么？")
        goal = input("👉 请输入你的目标（例如 '更技术'、'更简洁'、'更贴合JD中的API要求'）：\n")
        return {"goal": goal or "general improvement"}

    def rewrite_resume(state: ResumeState) -> ResumeState:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
        prompt = f"""
You are a professional career coach and resume optimization expert.

Your task is to revise and tailor the candidate’s resume to better align with the given job description.

### Resume (Original Markdown)
{state["resume_md"]}

### Job Description
{state["jd_md"]}

### Optimization Goal
Make the resume more {state["goal"]} while ensuring it matches the tone and style of a professional tech resume.

### Requirements:
- Output **only** the revised Markdown resume.
- Keep it realistic; do not invent experience.
- You may adjust ordering, add keywords, or rephrase sentences to match the JD.
- Highlight technical alignment and measurable achievements where possible.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        print("\n✅ 优化后的简历：\n")
        print(response.content)
        return {"final_resume": response.content}

    # ---------- 注册节点 ----------
    graphState.add_node("input_resume_and_jd", input_resume_and_jd)
    graphState.add_node("choose_focus", choose_focus)
    graphState.add_node("rewrite_resume", rewrite_resume)

    # ---------- 定义连接 ----------
    graphState.add_edge("input_resume_and_jd", "choose_focus")
    graphState.add_edge("choose_focus", "rewrite_resume")
    graphState.add_edge("rewrite_resume", END)
    graphState.set_entry_point("input_resume_and_jd")

    return graphState


if __name__ == "__main__":
    graph = define_graph()
    compiled_graph = graph.compile()
    compiled_graph.invoke({})
