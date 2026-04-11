export default function LoadingSpinner() {
  return (
    <span className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-700">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-200 border-t-cyan-700" />
      Thinking with retrieved context
    </span>
  );
}
