import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import InsightCard from "../components/InsightCard";
import ChatBubble from "../components/ChatBubble";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import Button from "../components/Button";
import { fetchInsights, askAssistant } from "../services/aiService";
import { getErrorMessage } from "../utils/errors";
import usePageTitle from "../hooks/usePageTitle";

// Must match AskQuestionRequest.history's max_length in the backend schema
// (app/schemas/ai.py) — kept in sync manually since there's no shared contract.
const MAX_HISTORY_ENTRIES = 20;

const SUGGESTED_QUESTIONS = [
  "Where did I spend the most this month?",
  "What was my highest expense?",
  "Compare my spending with last month.",
  "How can I reduce unnecessary spending?",
];

export default function AIInsights() {
  usePageTitle("AI Insights");
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(true);
  const [insightsError, setInsightsError] = useState(null);

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [chatError, setChatError] = useState(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
    loadInsights();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadInsights() {
    setInsightsLoading(true);
    setInsightsError(null);
    try {
      const data = await fetchInsights();
      setInsights(data);
    } catch (err) {
      setInsightsError(getErrorMessage(err, "Failed to load insights."));
    } finally {
      setInsightsLoading(false);
    }
  }

  async function handleAsk(questionText) {
    const q = (questionText ?? question).trim();
    if (!q || isAsking) return;

    // Cap history to what the backend will accept (see MAX_HISTORY_ENTRIES above);
    // send the most recent entries so a long-running chat degrades gracefully
    // instead of the request failing with a 422 once the transcript grows past it.
    const history = messages.slice(-MAX_HISTORY_ENTRIES).map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    setChatError(null);
    setIsAsking(true);

    try {
      const data = await askAssistant(q, history);
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch (err) {
      setChatError(getErrorMessage(err, "The assistant is unavailable right now."));
    } finally {
      setIsAsking(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    handleAsk();
  }

  return (
    <>
      <div className="mx-auto flex max-w-4xl flex-col gap-6">
        {/* Insights */}
        <div>
          <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Your Spending Insights
          </h2>

          {insightsLoading ? (
            <div className="flex justify-center py-10">
              <LoadingSpinner />
            </div>
          ) : insightsError ? (
            <ErrorState message={insightsError} onRetry={loadInsights} />
          ) : (
            <>
              <div className="flex flex-col gap-2">
                {insights.insights.map((item, idx) => (
                  <InsightCard key={idx} message={item.message} type={item.type} />
                ))}
              </div>
              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">{insights.disclaimer}</p>
            </>
          )}
        </div>

        {/* Assistant */}
        <div className="rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
          <div className="border-b border-gray-100 px-5 py-3 dark:border-gray-800">
            <h2 className="flex items-center gap-1.5 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <Sparkles size={15} aria-hidden="true" /> Ask about your expenses
            </h2>
          </div>

          <div className="flex h-96 flex-col overflow-y-auto px-5 py-4">
            {messages.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Ask a question about your spending — answers are based only on your logged expenses.
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleAsk(q)}
                      className="rounded-full border border-gray-300 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4" role="log" aria-label="Conversation with the expense assistant" aria-live="polite">
                {messages.map((m, idx) => (
                  <ChatBubble key={idx} role={m.role} content={m.content} />
                ))}
                {isAsking && (
                  <div className="flex items-center gap-2 pl-9 text-sm text-gray-500 dark:text-gray-400">
                    <LoadingSpinner size="sm" /> <span>Thinking...</span>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>

          {chatError && (
            <p role="alert" className="border-t border-gray-100 px-5 py-2 text-sm text-red-600 dark:border-gray-800 dark:text-red-400">
              {chatError}
            </p>
          )}

          <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-gray-100 p-3 dark:border-gray-800">
            <label htmlFor="assistant-question" className="sr-only">Ask a question about your expenses</label>
            <input
              id="assistant-question"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about your expenses..."
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
              disabled={isAsking}
            />
            <Button type="submit" disabled={isAsking || !question.trim()} aria-label="Send question">
              <Send size={15} aria-hidden="true" />
            </Button>
          </form>
          {messages.length > 0 && (
            <p className="px-5 pb-3 text-xs text-gray-500 dark:text-gray-400">
              This is based on your logged expense data and is for informational purposes only — not financial advice.
            </p>
          )}
        </div>
      </div>
    </>
  );
}
