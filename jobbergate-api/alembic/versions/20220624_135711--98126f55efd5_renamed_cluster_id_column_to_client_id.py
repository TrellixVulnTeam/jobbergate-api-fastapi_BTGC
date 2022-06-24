"""Renamed cluster_id column to client_id

Revision ID: 98126f55efd5
Revises: edfdea225579
Create Date: 2022-06-24 13:57:11.720760

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "98126f55efd5"
down_revision = "edfdea225579"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("job_submissions", sa.Column("client_id", sa.String(), nullable=False))
    op.drop_index("ix_job_submissions_cluster_id", table_name="job_submissions")
    op.create_index(op.f("ix_job_submissions_client_id"), "job_submissions", ["client_id"], unique=False)
    op.drop_column("job_submissions", "cluster_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "job_submissions", sa.Column("cluster_id", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.drop_index(op.f("ix_job_submissions_client_id"), table_name="job_submissions")
    op.create_index("ix_job_submissions_cluster_id", "job_submissions", ["cluster_id"], unique=False)
    op.drop_column("job_submissions", "client_id")
    # ### end Alembic commands ###
