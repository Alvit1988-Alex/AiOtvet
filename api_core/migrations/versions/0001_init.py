"""Initial database schema."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("username", sa.String(length=255)),
        sa.Column("first_name", sa.String(length=255)),
        sa.Column("last_name", sa.String(length=255)),
        sa.Column("lang", sa.String(length=8), default="ru"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "operator",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tg_id", sa.Integer(), unique=True),
        sa.Column("email", sa.String(length=255), unique=True, nullable=False),
        sa.Column("role", sa.Enum("operator", "lead", "admin", name="operatorrole"), nullable=False),
        sa.Column("password_hash", sa.String(length=255)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.sql.expression.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "dialog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id")),
        sa.Column("assigned_operator_id", sa.Integer(), sa.ForeignKey("operator.id")),
        sa.Column("status", sa.Enum("auto", "waiting_operator", "waiting_user", name="dialogstatus"), nullable=False),
        sa.Column("mode", sa.Enum("auto", "human", name="dialogmode"), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index("ix_dialog_status_last_message", "dialog", ["status", "last_message_at"])

    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dialog_id", sa.Integer(), sa.ForeignKey("dialog.id")),
        sa.Column("sender", sa.Enum("user", "bot", "operator", name="messagesender"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON()),
        sa.Column("llm_provider", sa.String(length=50)),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index("ix_message_dialog_created", "message", ["dialog_id", "created_at"])

    op.create_table(
        "knowledge_document",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("tags", sa.String(length=255)),
        sa.Column("source_type", sa.String(length=32)),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("operator.id")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "knowledge_chunk",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("knowledge_document.id"), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON()),
        sa.Column("meta", sa.JSON()),
    )

    op.create_table(
        "setting",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_type", sa.String(length=32)),
        sa.Column("actor_id", sa.Integer()),
        sa.Column("event_type", sa.String(length=64)),
        sa.Column("payload", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_event")
    op.drop_table("setting")
    op.drop_table("knowledge_chunk")
    op.drop_table("knowledge_document")
    op.drop_index("ix_message_dialog_created", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_dialog_status_last_message", table_name="dialog")
    op.drop_table("dialog")
    op.drop_table("operator")
    op.drop_table("user")
