export default function SuggestedPrompts({ prompts, onSelect }) {
  if (!prompts?.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {prompts.map((prompt) => (
        <button key={prompt} className="prompt-chip" type="button" onClick={() => onSelect(prompt)}>
          {prompt}
        </button>
      ))}
    </div>
  );
}
