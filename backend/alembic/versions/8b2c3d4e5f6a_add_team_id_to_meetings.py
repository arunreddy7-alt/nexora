"""add team id to meetings

Revision ID: 8b2c3d4e5f6a
Revises: 7a1b2c3d4e5f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b2c3d4e5f6a"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "7a1b2c3d4e5f"

branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column(
        "meetings",
        sa.Column(
            "team_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_meetings_team_id",
        "meetings",
        ["team_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_meetings_team_id_teams",
        "meetings",
        "teams",
        ["team_id"],
        ["id"],
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_meetings_team_id_teams",
        "meetings",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_meetings_team_id",
        table_name="meetings",
    )

    op.drop_column(
        "meetings",
        "team_id",
    )