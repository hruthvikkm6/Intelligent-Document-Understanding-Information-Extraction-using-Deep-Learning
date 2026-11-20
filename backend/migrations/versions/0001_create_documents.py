"""Create documents table."""

import sqlalchemy as sa
from alembic import op

revision = "0001_documents"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="uploaded"),
        sa.Column("ocr_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("extraction_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("extracted_fields", sa.JSON()),
        sa.Column("raw_extraction", sa.JSON()),
        sa.Column("validation", sa.JSON()),
        sa.Column("ocr_result", sa.JSON()),
        sa.Column("processing_time_ms", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_documents_status", "documents", ["status"])


def downgrade():
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_table("documents")
