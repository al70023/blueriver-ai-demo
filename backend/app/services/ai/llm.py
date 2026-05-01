from openai import OpenAI

from app.core.config import settings


def format_context(context_chunks: list[dict[str, str | int | float | None]]) -> str:
    formatted_chunks: list[str] = []

    for chunk in context_chunks:
        formatted_chunks.append(
            f"[chunk_id={chunk['chunk_id']}, chunk_index={chunk['chunk_index']}]\n"
            f"{chunk['text']}"
        )

    return "\n\n---\n\n".join(formatted_chunks)


def generate_answer_from_context(
    *,
    question: str,
    context_chunks: list[dict[str, str | int | float | None]],
) -> str:
    if not context_chunks:
        return "I could not find relevant context to answer the question."

    if not settings.openai_api_key:
        return (
            "Relevant chunks were retrieved, but no OpenAI API key is configured. "
            "Add OPENAI_API_KEY to .env to enable answer generation."
        )

    client = OpenAI(api_key=settings.openai_api_key)

    context = format_context(context_chunks)

    prompt = f"""
    You are an AI document review assistant.

    Answer the user's question using only the provided document context.

    Rules:
    - Do not use outside knowledge.
    - If the context does not contain the answer, say that the document context does not provide enough information.
    - Cite chunk IDs in your answer using this format: [chunk_id=123].
    - Be concise but useful.

    Document context:
    {context}

    User question:
    {question}
    """

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You answer questions using only provided document context.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""
