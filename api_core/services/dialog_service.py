"""Business logic functions operating on dialogs."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    Dialog,
    DialogMode,
    DialogStatus,
    Message,
    MessageSender,
    Operator,
    User,
)
from .confidence import ConfidenceEvaluator
from .notifications import NotificationManager


class DialogService:
    """Encapsulates complex dialog workflows."""

    def __init__(
        self,
        db: Session,
        notifier: NotificationManager,
        confidence: ConfidenceEvaluator,
    ) -> None:
        self.db = db
        self.notifier = notifier
        self.confidence = confidence

    # region fetching
    def list_dialogs(self, status: DialogStatus | None = None) -> Sequence[Dialog]:
        statement = select(Dialog).order_by(Dialog.last_message_at.desc())
        if status:
            statement = statement.filter(Dialog.status == status)
        return self.db.scalars(statement).all()

    def get_dialog(self, dialog_id: int) -> Dialog:
        dialog = self.db.get(Dialog, dialog_id)
        if not dialog:
            raise ValueError("Dialog not found")
        return dialog

    # endregion fetching

    def ensure_user(self, tg_user_id: int, defaults: dict[str, str | None]) -> User:
        user = self.db.query(User).filter(User.tg_user_id == tg_user_id).first()
        if user:
            user.last_seen = datetime.utcnow()
            return user
        user = User(tg_user_id=tg_user_id, **defaults)
        self.db.add(user)
        self.db.flush()
        return user

    def create_or_get_active_dialog(self, user: User) -> Dialog:
        dialog = (
            self.db.query(Dialog)
            .filter(Dialog.user_id == user.id)
            .order_by(Dialog.created_at.desc())
            .first()
        )
        if dialog and dialog.status in {DialogStatus.WAITING_OPERATOR, DialogStatus.WAITING_USER}:
            return dialog
        dialog = Dialog(user_id=user.id)
        self.db.add(dialog)
        self.db.flush()
        return dialog

    def add_message(
        self,
        dialog: Dialog,
        sender: MessageSender,
        text: str,
        llm_provider: str | None = None,
        confidence: float | None = None,
        payload: dict | None = None,
    ) -> Message:
        message = Message(
            dialog_id=dialog.id,
            sender=sender,
            text=text,
            llm_provider=llm_provider,
            confidence=confidence,
            payload=payload or {},
        )
        dialog.last_message_at = message.created_at
        self.db.add(message)
        self.db.flush()
        self.notifier.broadcast(
            event="message_created",
            payload={"dialog_id": dialog.id, "message_id": message.id, "sender": sender.value},
        )
        return message

    def transition_status(self, dialog: Dialog, new_status: DialogStatus) -> None:
        old_status = dialog.status
        dialog.status = new_status
        if old_status != new_status:
            self.notifier.broadcast(
                event="dialog_status",
                payload={"dialog_id": dialog.id, "from": old_status.value, "to": new_status.value},
            )

    def assign_operator(self, dialog: Dialog, operator: Operator) -> None:
        dialog.assigned_operator_id = operator.id
        self.notifier.broadcast(
            event="dialog_assigned",
            payload={"dialog_id": dialog.id, "operator_id": operator.id},
        )

    def handle_user_message(self, dialog: Dialog, text: str) -> Message:
        message = self.add_message(dialog, MessageSender.USER, text)
        if dialog.mode == DialogMode.HUMAN and dialog.status == DialogStatus.WAITING_OPERATOR:
            return message
        return message

    def handle_bot_reply(self, dialog: Dialog, text: str, confidence: float, provider: str) -> Message:
        message = self.add_message(
            dialog,
            sender=MessageSender.BOT,
            text=text,
            confidence=confidence,
            llm_provider=provider,
        )
        if confidence < self.confidence.threshold:
            self.transition_status(dialog, DialogStatus.WAITING_OPERATOR)
        else:
            self.transition_status(dialog, DialogStatus.WAITING_USER)
        return message

    def handle_operator_reply(self, dialog: Dialog, operator: Operator, text: str) -> Message:
        dialog.mode = DialogMode.HUMAN
        dialog.assigned_operator_id = operator.id
        message = self.add_message(dialog, MessageSender.OPERATOR, text)
        self.transition_status(dialog, DialogStatus.WAITING_USER)
        return message

    def takeover(self, dialog: Dialog, operator: Operator) -> None:
        dialog.mode = DialogMode.HUMAN
        dialog.assigned_operator_id = operator.id
        self.transition_status(dialog, DialogStatus.WAITING_OPERATOR)

    def handoff_to_auto(self, dialog: Dialog) -> None:
        dialog.mode = DialogMode.AUTO
        if dialog.status == DialogStatus.WAITING_OPERATOR:
            self.transition_status(dialog, DialogStatus.AUTO)

    def paginate_messages(
        self, dialog: Dialog, limit: int = 50, before_id: int | None = None
    ) -> Iterable[Message]:
        query = self.db.query(Message).filter(Message.dialog_id == dialog.id)
        if before_id:
            query = query.filter(Message.id < before_id)
        return query.order_by(Message.created_at.desc()).limit(limit).all()
