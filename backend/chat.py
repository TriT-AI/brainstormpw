from langchain_core.messages import SystemMessage, HumanMessage
from backend.llm_factory import get_user_llm  # <--- Import Factory


def build_project_context(sections):
    if not sections:
        return "[The document is currently empty.]"
    context_text = "CURRENT PROJECT DRAFT:\n\n"
    for sec in sections:
        title = sec["meta"]["title"]
        content = sec["user_data"].get("content", "").strip()
        if not content:
            content = "[No content written for this section yet]"
        context_text += f"## SECTION: {title}\n{content}\n\n"
    return context_text


def get_chat_response(history, current_sections):
    # 1. Check Credentials
    chat_llm = get_user_llm()
    if not chat_llm:
        return "⚠️ I can't help you yet! Please enter your **OpenAI Keys** in the sidebar settings."

    # 2. Build Context
    doc_context = build_project_context(current_sections)

    system_prompt = f"""You are a helpful Project Manager Assistant. 
    You have access to the current draft of the Project Charter below.
    
    INSTRUCTIONS:
    1. Answer the user's questions based PRIMARILY on the 'CURRENT PROJECT DRAFT' provided below.
    2. If the user asks about the purpose of the document, summarize the draft.
    3. If the answer is not in the draft, say "I don't see that information in your current draft" and suggest where they might add it.
    
    {doc_context}
    """

    messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))

    try:
        response = chat_llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"
