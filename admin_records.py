"""Read execution manifests without filesystem access beyond the TSV itself.

Field order belongs here; plan/v1 records are a different format and must not
use these definitions. Callers retain responsibility for PDF hash verification
and deciding whether a draft or final manifest is appropriate.
"""

from collections import namedtuple
import csv
import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
import re


RECORDS = {
    'schema': namedtuple('Schema', 'version'),
    'bundle': namedtuple('Bundle', 'date week start end state approval pdf_name pdf_sha256'),
    'created-at': namedtuple('CreatedAt', 'epoch'),
    'entry': namedtuple('Entry', 'order member_id display_name requirement state source mtime sha256 page_count page_start page_end reason'),
    'history': namedtuple('History', 'week member_id state evidence'),
    'candidate': namedtuple('Candidate', 'member_id decision source mtime sha256 reason'),
    'issue': namedtuple('Issue', 'severity code member_id message'),
}
Manifest = namedtuple('Manifest', 'bundle entries records')
STATES = {'included', 'exception', 'missing', 'optional-missing'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, field, minimum=0):
    _require(re.fullmatch(r'[0-9]+', value), field + ': expected an unsigned integer')
    number = int(value)
    _require(number >= minimum, field + ': value is too small')
    return number


def _hash(value, field):
    _require(re.fullmatch(r'[0-9a-f]{64}', value), field + ': expected a SHA-256 hex digest')


def _relative(value, field, filename=False):
    # Check both syntaxes regardless of the host reading a shared manifest.
    for path in (PurePosixPath(value), PureWindowsPath(value)):
        _require(value != '-' and not path.anchor and '..' not in path.parts
                 and bool(path.parts) and (not filename or len(path.parts) == 1),
                 field + ': expected a relative ' + ('filename' if filename else 'path'))


def _week(value):
    _require(re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])-W[1-5]', value), 'week: invalid reporting week')


def _validate(kind, record):
    if kind == 'schema':
        _require(record.version == 'admin-wr-bundle/v1', 'unsupported execution manifest schema')
    elif kind == 'bundle':
        for field in ('date', 'start', 'end'):
            value = getattr(record, field)
            _require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), field + ': expected YYYY-MM-DD')
            datetime.date(*map(int, value.split('-')))
        _week(record.week)
        _require((record.state, record.approval) in {
            ('draft', 'required'), ('complete', 'not-required'),
            ('approved-with-issues', 'user-confirmed')}, 'invalid state/approval pair')
        _relative(record.pdf_name, 'pdf_name', filename=True)
        _hash(record.pdf_sha256, 'pdf_sha256')
    elif kind == 'created-at':
        record = record._replace(epoch=_integer(record.epoch, 'epoch'))
    elif kind == 'entry':
        _require(record.requirement in {'required', 'optional'} and record.state in STATES,
                 'invalid requirement or entry state')
        record = record._replace(order=_integer(record.order, 'order', 1),
                                 page_count=_integer(record.page_count, 'page_count'))
        if record.state in {'included', 'exception'}:
            # Source names are opaque evidence here, not paths to open. Keep
            # POSIX names containing colons/backslashes valid on other hosts.
            _require(record.source != '-', 'source: expected a selected source')
            _hash(record.sha256, 'sha256')
            record = record._replace(mtime=_integer(record.mtime, 'mtime'),
                                     page_start=_integer(record.page_start, 'page_start', 2),
                                     page_end=_integer(record.page_end, 'page_end', 2))
            _require(record.page_count > 0 and record.page_end - record.page_start + 1 == record.page_count,
                     'page_count: does not match the page range')
        else:
            _require((record.state == 'missing') == (record.requirement == 'required'),
                     'missing state does not match requirement')
            _require(record.page_count == 0 and all(getattr(record, f) == '-' for f in
                     ('source', 'mtime', 'sha256', 'page_start', 'page_end')),
                     'missing entry must have page_count 0 and absent source metadata/range')
    elif kind == 'history':
        _week(record.week)
        _require(record.state in STATES | {'unknown'}, 'invalid history state')
    elif kind == 'candidate':
        _require(record.decision in {'selected', 'rejected'}, 'invalid candidate decision')
        _require(record.source != '-', 'source: expected a candidate source')
        _hash(record.sha256, 'sha256')
        record = record._replace(mtime=_integer(record.mtime, 'mtime'))
    elif kind == 'issue':
        _require(record.severity in {'warning', 'error'}, 'invalid issue severity')
    return record


def read_manifest(path):
    """Return named, validated v1 records; errors identify the file and line.

    Quotes are literal TSV data. BOM, CRLF, comments and blank lines are
    accepted. Optional history records are not required for legacy manifests.
    No referenced PDF is opened here, even when later rows are malformed.
    """
    records, entries, bundles, schemas = [], [], [], []
    member_ids, orders = set(), set()
    with Path(path).open(encoding='utf-8-sig', newline='') as source:
        for line, row in enumerate(csv.reader(source, delimiter='\t', quoting=csv.QUOTE_NONE), 1):
            if not row or not row[0] or row[0].startswith('#'):
                continue
            kind = row[0]
            try:
                _require(kind in RECORDS, 'unknown record type')
                cls = RECORDS[kind]
                _require(len(row) == len(cls._fields) + 1,
                         'expected {} fields, got {}'.format(len(cls._fields) + 1, len(row)))
                _require(all(row), 'empty field')
                record = _validate(kind, cls(*row[1:]))
                if kind == 'entry':
                    _require(record.member_id not in member_ids and record.order not in orders,
                             'duplicate member ID or order')
                    member_ids.add(record.member_id)
                    orders.add(record.order)
                    entries.append(record)
                elif kind == 'bundle':
                    _require(not bundles, 'duplicate bundle record')
                    bundles.append(record)
                elif kind == 'schema':
                    _require(not schemas, 'duplicate schema record')
                    schemas.append(record)
                records.append(record)
            except ValueError as error:
                raise ValueError('{}:{}: {}: {}'.format(path, line, kind, error)) from error
    _require(len(schemas) == 1 and len(bundles) == 1,
             '{}: expected one schema and one bundle record'.format(path))
    return Manifest(bundles[0], tuple(entries), tuple(records))
