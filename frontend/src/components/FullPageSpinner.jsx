import LoadingSpinner from "./LoadingSpinner";

export default function FullPageSpinner() {
  return (
    <div className="flex h-dvh items-center justify-center">
      <LoadingSpinner size="lg" />
    </div>
  );
}
