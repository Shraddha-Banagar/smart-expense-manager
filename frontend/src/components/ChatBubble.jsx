import { Bot, User } from "lucide-react";

export default function ChatBubble({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-accent text-white" : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
        }`}
      >
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>
      <div
        className={`max-w-[80%] rounded-lg px-3.5 py-2.5 text-sm ${
          isUser
            ? "bg-accent text-white"
            : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
