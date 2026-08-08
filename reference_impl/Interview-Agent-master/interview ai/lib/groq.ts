import Groq from "groq-sdk";

// Initialize once — reuse across all requests
const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY!,
});

export const GROQ_MODEL = process.env.GROQ_MODEL || "llama-3.3-70b-versatile";

/**
 * Send a chat completion request to Groq.
 * @param messages  Full message history to send
 * @param temperature  0.0–1.0, use 0.7 for interviews, 0.1 for feedback
 * @param maxTokens  Token limit for the response
 */
export async function groqChat(
  messages: { role: "system" | "user" | "assistant"; content: string }[],
  temperature = 0.7,
  maxTokens = 1024
): Promise<string> {
  const completion = await groq.chat.completions.create({
    model: GROQ_MODEL,
    messages,
    temperature,
    max_tokens: maxTokens,
  });
  return completion.choices[0]?.message?.content ?? "";
}

/**
 * Stream a chat completion token-by-token. `onToken` receives each text delta
 * as it arrives; the promise resolves with the fully accumulated reply.
 */
export async function groqChatStream(
  messages: { role: "system" | "user" | "assistant"; content: string }[],
  temperature = 0.7,
  maxTokens = 1024,
  onToken?: (delta: string) => void
): Promise<string> {
  const stream = await groq.chat.completions.create({
    model: GROQ_MODEL,
    messages,
    temperature,
    max_tokens: maxTokens,
    stream: true,
  });

  let full = "";
  for await (const chunk of stream) {
    const delta = chunk.choices?.[0]?.delta?.content ?? "";
    if (delta) {
      full += delta;
      onToken?.(delta);
    }
  }
  return full;
}

export default groq;
