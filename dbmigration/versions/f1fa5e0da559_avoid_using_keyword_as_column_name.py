# Copyright 2023 The chainmetareader Authors. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""avoid using keyword as column name

Revision ID: f1fa5e0da559
Revises: f1e13c4fa803
Create Date: 2024-03-26 17:20:03.744295

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1fa5e0da559"
down_revision = "f1e13c4fa803"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "chainmeta",
        "from",
        new_column_name="valid_from",
        type_=sa.DateTime,
        nullable=True,
    )
    op.alter_column(
        "chainmeta", "to", new_column_name="valid_to", type_=sa.DateTime, nullable=True
    )
    op.alter_column(
        "chainmeta",
        "metadata",
        new_column_name="additional_metadata",
        type_=sa.JSON,
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "chainmeta",
        "additional_metadata",
        new_column_name="metadata",
        type_=sa.JSON,
        nullable=True,
    )
    op.alter_column(
        "chainmeta", "valid_to", new_column_name="to", type_=sa.DateTime, nullable=True
    )
    op.alter_column(
        "chainmeta",
        "valid_from",
        new_column_name="from",
        type_=sa.DateTime,
        nullable=True,
    )
