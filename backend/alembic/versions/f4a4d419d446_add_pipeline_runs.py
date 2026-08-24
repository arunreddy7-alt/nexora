"""add pipeline runs

Revision ID: f4a4d419d446
Revises: 39360bca31c2
Create Date: 2026-08-20 23:35:21.186287

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4a4d419d446"
down_revision: Union[str, Sequence[str], None] = "39360bca31c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "pipeline_runs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "current_agent",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_pipeline_runs_id",
        "pipeline_runs",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_pipeline_runs_project_id",
        "pipeline_runs",
        ["project_id"],
        unique=False,
    )

    op.create_index(
        "ix_pipeline_runs_status",
        "pipeline_runs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_pipeline_runs_status",
        table_name="pipeline_runs",
    )

    op.drop_index(
        "ix_pipeline_runs_project_id",
        table_name="pipeline_runs",
    )

    op.drop_index(
        "ix_pipeline_runs_id",
        table_name="pipeline_runs",
    )

    op.drop_table("pipeline_runs")