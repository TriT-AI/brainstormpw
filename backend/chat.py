import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize a separate LLM instance for Chat (maybe faster/cheaper model like gpt-4o-mini)
chat_llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model="gpt-4.1-nano",
)


def build_project_context(sections):
    """
    Combines the current state of the document into a single readable string.
    """
    if not sections:
        return "[The document is currently empty.]"

    context_text = "CURRENT PROJECT DRAFT:\n\n"

    for sec in sections:
        title = sec["meta"]["title"]
        # CRITICAL: Access the 'user_data' -> 'content' path safely
        content = sec["user_data"].get("content", "").strip()

        if not content:
            content = "[No content written for this section yet]"

        context_text += f"## SECTION: {title}\n{content}\n\n"

    return context_text


def get_chat_response(history, current_sections):
    """
    history: List of {"role": "user/assistant", "content": "..."}
    current_sections: The raw section data from session_state
    """
    # 1. Build the dynamic context from the user's actual draft
    doc_context = build_project_context(current_sections)

    # 2. System Prompt with "Grounding"
    # We tell the AI to prioritize the context provided.
    system_prompt = f"""You are a helpful Project Manager Assistant. 
    You have access to the current draft of the Project Charter below.
    
    INSTRUCTIONS:
    1. Answer the user's questions based PRIMARILY on the 'CURRENT PROJECT DRAFT' provided below.
    2. If the user asks about the purpose of the document, summarize the draft.
    3. If the answer is not in the draft, say "I don't see that information in your current draft" and suggest where they might add it.
    
    {doc_context}
    """

    # 3. Convert messages for LangChain
    messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(SystemMessage(content=msg["content"]))

    # 4. Run LLM
    try:
        response = chat_llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"I'm having trouble reading the document right now. Error: {str(e)}"
