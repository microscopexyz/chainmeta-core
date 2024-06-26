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

from collections import defaultdict
from datetime import date, datetime
from functools import reduce as functional_reduce
from typing import Callable, Generator, Iterable, List, Optional

from dateutil import parser
from sqlalchemy import JSON, Date, DateTime, Integer, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    scoped_session,
    sessionmaker,
)
from unsync import unsync  # type: ignore

from chainmeta.config import default_config
from chainmeta.constants import Namespace
from chainmeta.logger import logger
from chainmeta.metadata import ChainmetaItem

"""This module defines the database schema and provides the functions to interact with the database.
"""

# Define the database connection
_session_maker: Optional[Callable] = None

err_msg = "Database is not initialized.Set CHAINMETA_DB_CONN environment variable or call set_connection_string() first."  # noqa: E501


class Base(DeclarativeBase):
    pass


class ChainmetaRecord(Base):
    """Define the table schema for Chainmeta.

    Chainmeta is stored in the database as a flattened list of records, where
    entity, name, and each categories are all stored as separate records.
    """

    __tablename__ = "chainmeta"

    id: Mapped[Optional[int]] = mapped_column(Integer, primary_key=True)
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    namespace: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(64), nullable=False)
    submitted_on: Mapped[date] = mapped_column(Date, nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    additional_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=False)


def init_db(connection_string: str) -> None:
    global _session_maker

    # Initialize the database connection
    engine = create_engine(connection_string, echo=False)

    # Create a sessionmaker object to interact with the database
    session_factory = sessionmaker(bind=engine)
    _session_maker = scoped_session(session_factory)


def flatten(metadata_list: List[ChainmetaItem]) -> List[ChainmetaRecord]:
    """Flatten the list of ChainmetaItem into a list of ChainmetaRecord.

    Function flatten() translates chain metadata in common schema to database records.
    """

    flattened_records: List[Optional[ChainmetaRecord]] = []
    for metadata in metadata_list:
        address, network, source, submitted_by = (
            metadata.address,
            metadata.chain,
            metadata.source,
            metadata.submitted_by,
        )

        try:
            submitted_on = parser.parse(metadata.submitted_on)
        except Exception:
            logger.warning("Invalid submitted_on date: %s", metadata.submitted_on)
            continue

        valid_from_: Optional[datetime] = None
        if "valid_from" in metadata.additional_metadata:
            valid_from_str = metadata.additional_metadata["valid_from"]
            try:
                valid_from_ = parser.parse(valid_from_str)
            except Exception:
                logger.warning("Invalid valid_from date: %s", valid_from_str)

        valid_to_: Optional[datetime] = None
        if "valid_to" in metadata.additional_metadata:
            valid_to_str = metadata.additional_metadata["valid_to"]
            try:
                valid_to_ = parser.parse(valid_to_str)
            except Exception:
                logger.warning("Invalid valid_to date: %s", valid_to_str)

        def _should_include_valid_from(tag_type: str, tag_value: str) -> bool:
            if (
                tag_type in ["category"]
                and "valid_from"
                in default_config.Categories[tag_value].additional_metadata_fields
            ):
                return True
            return False

        def _should_include_valid_to(tag_type: str, tag_value: str) -> bool:
            if (
                tag_type in ["category"]
                and "valid_to"
                in default_config.Categories[tag_value].additional_metadata_fields
            ):
                return True
            return False

        def _additional_metadata_fields(tag_type: str, tag_value: str) -> list[str]:
            if tag_type in ["category"]:
                return [
                    f
                    for f in default_config.Categories[
                        tag_value
                    ].additional_metadata_fields
                    if f not in ["valid_from", "valid_to"]
                ]
            return []

        def _build_record(tag_type: str, tag_value: Optional[str]):
            if not tag_value:
                return None

            valid_from = None
            if _should_include_valid_from(tag_type, tag_value):
                valid_from = valid_from_
            valid_to = None
            if _should_include_valid_to(tag_type, tag_value):
                valid_to = valid_to_

            valid_to = (
                valid_to_ if _should_include_valid_to(tag_type, tag_value) else None
            )
            field_names = _additional_metadata_fields(tag_type, tag_value)
            all_additional_metadata = metadata.additional_metadata
            additional_metadata = {
                k: all_additional_metadata[k]
                for k in field_names
                if k in all_additional_metadata
            }

            return ChainmetaRecord(
                address=address,
                chain=network,
                namespace=Namespace.GLOBAL.value,
                scope=tag_type,
                tag=tag_value,
                source=source,
                submitted_by=submitted_by,
                submitted_on=submitted_on,
                valid_from=valid_from,
                valid_to=valid_to,
                additional_metadata=additional_metadata,
            )

        flattened_records.append(
            _build_record(tag_type="entity", tag_value=metadata.entity)
        )
        flattened_records.append(
            _build_record(tag_type="name", tag_value=metadata.name)
        )
        flattened_records += [
            _build_record(tag_type="category", tag_value=category)
            for category in metadata.categories
        ]
    return [r for r in flattened_records if r]


def reduce(record_list: List[ChainmetaRecord]) -> List[ChainmetaItem]:
    """Reduce the list of ChainmetaRecord into a list of ChainmetaItem.

    Function reduce() translates database records to chain metadata in common schema.
    """

    def _group_by(metadata_groups: dict, record: ChainmetaRecord):
        k = (record.address, record.chain, record.source, record.submitted_by)
        metadata_groups[k].append(record)
        return metadata_groups

    def _build_meta(group: List[ChainmetaRecord]) -> List[ChainmetaItem]:
        result: List[ChainmetaItem] = []
        if len(group) == 0:
            return result
        metadata = ChainmetaItem(
            chain=group[0].chain,
            address=group[0].address,
            entity="",
            name=None,
            categories=[],
            source=group[0].source,
            submitted_by=group[0].submitted_by,
            submitted_on=str(group[0].submitted_on),
            additional_metadata={},
        )

        records_no_additional_meta = [
            i
            for i in group
            if i.namespace != Namespace.GLOBAL.value
            and not (i.valid_from or i.valid_to or i.additional_metadata)
        ]
        for record in records_no_additional_meta:
            metadata.submitted_on = max(metadata.submitted_on, str(record.submitted_on))
            if record.scope == "entity":
                metadata.entity = record.tag
            elif record.scope == "name":
                metadata.name = record.tag
            elif record.scope == "category":
                metadata.categories.append(record.tag)
        if records_no_additional_meta:
            result.append(metadata)

        records_with_additional_meta = [
            i
            for i in group
            if i.namespace != Namespace.GLOBAL.value
            and (i.valid_from or i.valid_to or i.additional_metadata)
        ]
        for record in records_with_additional_meta:
            metadata = ChainmetaItem(
                chain=group[0].chain,
                address=group[0].address,
                entity="",
                name=None,
                categories=[],
                source=group[0].source,
                submitted_by=group[0].submitted_by,
                submitted_on=str(group[0].submitted_on),
                additional_metadata={},
            )

            metadata.submitted_on = max(metadata.submitted_on, str(record.submitted_on))
            if record.scope == "entity":
                metadata.entity = record.tag
            elif record.scope == "name":
                metadata.name = record.tag
            elif record.scope == "category":
                metadata.categories.append(record.tag)
            result.append(metadata)

        return result

    metadata_groups: defaultdict = defaultdict(list)
    functional_reduce(_group_by, record_list, metadata_groups)

    reduced_list: List[ChainmetaItem] = []
    for v in metadata_groups.values():
        reduced_list += _build_meta(v)
    return reduced_list


@unsync
def _upload_chainmeta_single_batch(
    session_maker: Callable,
    items: Iterable[ChainmetaItem] | Iterable[ChainmetaRecord],
    *,
    skip_check: bool,
) -> int:
    """Upload a single batch of chain metadata to database."""

    with session_maker() as session:

        def _find_exist_item(record):
            """Check if the record already exists in the database."""
            if skip_check:
                return None
            with session.no_autoflush:
                found = (
                    session.query(ChainmetaRecord)
                    .filter_by(
                        chain=record.chain,
                        address=record.address,
                        namespace=record.namespace,
                        scope=record.scope,
                        tag=record.tag,
                        source=record.source,
                        submitted_by=record.submitted_by,
                    )
                    .first()
                )
                return found

        skipped = 0
        total = 0
        for item in items:
            if isinstance(item, ChainmetaItem):
                recods = flatten([item])
            else:
                recods = [item]
            for record in recods:
                total += 1
                exist_item = _find_exist_item(record)
                if exist_item:
                    for key, value in item.__dict__.items():
                        setattr(exist_item, key, value)
                else:
                    session.add(record)
        logger.debug(f"Skipped {skipped} and uploaded {total} records to database")
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(e)
            return 0
        return total


def upload_chainmeta(
    items: Iterable[ChainmetaItem] | Iterable[ChainmetaRecord],
    *,
    batch_size: int = 200,
    max_concurrency: int = 10,
    skip_check: bool = False,
) -> int:
    """Upload chain metadata to database.

    The upload is done in batches to avoid overloading the database.
    """

    if _session_maker is None:
        raise RuntimeError(err_msg)

    total, batch, tasks = 0, [], []
    for item in items:
        batch += [item]
        if len(batch) >= batch_size:
            tasks += [
                _upload_chainmeta_single_batch(
                    _session_maker, batch, skip_check=skip_check
                )
            ]
            batch = []
            if len(tasks) >= max_concurrency:
                total += sum(task.result() for task in tasks)
                tasks = []

    if batch:
        tasks += [
            _upload_chainmeta_single_batch(_session_maker, batch, skip_check=skip_check)
        ]
    if tasks:
        total += sum(task.result() for task in tasks)

    return total


def search_chainmeta(*, filter: dict = {}) -> Generator[ChainmetaItem, None, None]:
    """Search chain metadata from database.

    The query is done with pagination to avoid overloading the database.
    """

    if _session_maker is None:
        raise RuntimeError(err_msg)

    def _apply_filter(query, filter: dict):
        """Apply filter to query."""

        if not filter:
            return query

        for k, v in filter.items():
            if k in ["chain", "address", "submitted_by"]:
                query = query.filter(getattr(ChainmetaRecord, k) == v)
            else:
                logger.warning(f"Unsupported filter: {k}={v}")
        return query

    def _key(r: ChainmetaRecord):
        return r.chain, r.address, r.source, r.submitted_by

    with _session_maker() as session:
        page_size = 100
        is_empty = True
        remaining_results = []
        cursor = None
        while True:
            query = _apply_filter(session.query(ChainmetaRecord), filter)
            if cursor:
                query = query.filter(ChainmetaRecord.id > cursor)
            batch_results = (
                query.order_by(
                    ChainmetaRecord.chain,
                    ChainmetaRecord.address,
                    ChainmetaRecord.source,
                    ChainmetaRecord.submitted_by,
                    ChainmetaRecord.id,
                )
                .limit(page_size)
                .all()
            )
            if not batch_results:
                break

            if len(batch_results) < page_size:
                remaining_results += batch_results
                break
            last_record = batch_results[-1]
            cursor = last_record.id
            last_key = (
                last_record.chain,
                last_record.address,
                last_record.source,
                last_record.submitted_by,
            )

            batch_results = remaining_results + batch_results
            for r in reduce([r for r in batch_results if _key(r) != last_key]):
                is_empty = False
                yield r
            remaining_results = [r for r in batch_results if _key(r) == last_key]

        if remaining_results:
            for r in reduce(remaining_results):
                is_empty = False
                yield r

        if is_empty:
            return
