type Props = { message: string | null; onDismiss?: () => void };

export function ErrorBanner({ message, onDismiss }: Props) {
  if (!message) return null;
  return (
    <div role="alert" className="error-banner">
      <span>{message}</span>
      {onDismiss ? (
        <button onClick={onDismiss} aria-label="Dismiss error">
          Dismiss
        </button>
      ) : null}
    </div>
  );
}
