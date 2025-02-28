"""Moved job scripts to S3, removing string column

Revision ID: 2ab7ccf2f8c8
Revises: 98126f55efd5
Create Date: 2022-06-27 10:31:25.585016

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2ab7ccf2f8c8"
down_revision = "98126f55efd5"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("job_scripts", "job_script_data_as_string")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "job_scripts",
        sa.Column("job_script_data_as_string", sa.String(), nullable=False),
    )
    # ### end Alembic commands ###
