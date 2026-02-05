"""
Make file_path nullable in recordings table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'make_file_path_nullable'
down_revision = 'ef36bd1f1752'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('recordings', 'file_path', existing_type=sa.String(), nullable=True)

def downgrade():
    op.alter_column('recordings', 'file_path', existing_type=sa.String(), nullable=False)
