import Modal from "./Modal";
import Button from "./Button";

/**
 * Pass `isConfirming` while the confirm action is in flight to disable both
 * buttons (prevents a double-click firing two deletes) and show pending text.
 * The dialog does NOT close itself — the caller closes it on success and
 * leaves it open (with an error toast) on failure, so the user can retry.
 */
export default function ConfirmDialog({
  isOpen, onClose, onConfirm, title, message, isDangerous = true, isConfirming = false,
}) {
  return (
    <Modal isOpen={isOpen} onClose={isConfirming ? () => {} : onClose} title={title}>
      <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose} disabled={isConfirming}>
          Cancel
        </Button>
        <Button variant={isDangerous ? "danger" : "primary"} onClick={onConfirm} disabled={isConfirming}>
          {isConfirming ? "Deleting..." : "Confirm"}
        </Button>
      </div>
    </Modal>
  );
}
