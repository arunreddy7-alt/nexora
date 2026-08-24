"""add team id to projects

Revision ID: 7a1b2c3d4e5f
Revises: f4a4d419d446
Create Date: 2026-08-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "f4a4d419d446"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "projects",
        sa.Column(
            "team_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_projects_team_id",
        "projects",
        ["team_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_projects_team_id_teams",
        "projects",
        "teams",
        ["team_id"],
        ["id"],
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_projects_team_id_teams",
        "projects",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_projects_team_id",
        table_name="projects",
    )

    op.drop_column(
        "projects",
        "team_id",
    )