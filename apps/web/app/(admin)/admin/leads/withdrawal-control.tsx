"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, ConfirmationDialog } from "@keeper/ui";

export function WithdrawalControl({
  leadId,
  action,
}: {
  leadId: string;
  action: (formData: FormData) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(false);
  const [pending, setPending] = useState(false);
  const router = useRouter();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const submittingRef = useRef(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!open || !dialog) return;
    if (typeof dialog.showModal === "function") {
      if (!dialog.open) dialog.showModal();
    } else {
      dialog.setAttribute("open", "");
    }
    return () => {
      if (dialog.open && typeof dialog.close === "function") dialog.close();
    };
  }, [open]);

  useEffect(() => {
    if (!open && returnFocusRef.current) {
      returnFocusRef.current.focus();
      returnFocusRef.current = null;
    }
  }, [open]);

  function openDialog() {
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    setError(false);
    setOpen(true);
  }

  function cancel() {
    if (!submittingRef.current) setOpen(false);
  }

  async function confirm() {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setPending(true);
    const formData = new FormData();
    formData.set("lead_id", leadId);
    try {
      await action(formData);
      setOpen(false);
      setError(false);
      router.refresh();
    } catch {
      setError(true);
    } finally {
      submittingRef.current = false;
      setPending(false);
    }
  }

  return (
    <>
      <Button
        type="button"
        className="button-danger"
        onClick={openDialog}
        disabled={pending}
      >
        {pending ? "Withdrawing…" : "Withdraw marketing consent"}
      </Button>
      <ConfirmationDialog
        title="Withdraw marketing consent?"
        open={open}
        onCancel={cancel}
        onConfirm={confirm}
        dialogRef={dialogRef}
        busy={pending}
      >
        <p>
          This stops optional marketing consent for this lead. It does not
          affect the required service acknowledgement.
        </p>
        {error ? (
          <p role="alert">The withdrawal could not be completed. Try again.</p>
        ) : null}
      </ConfirmationDialog>
    </>
  );
}
