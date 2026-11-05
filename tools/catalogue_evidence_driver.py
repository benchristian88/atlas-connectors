# SPDX-License-Identifier: Apache-2.0
"""Seven-asset successor driver with a release-owned contract approval.

The approval is release-owned code, never an environment/downloaded document.
Runner-local checkpoints are bound to this source/run/original preflight and are
fsynced after every observed provider mutation. Ambiguous writes fail closed.
"""
import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from atlas_connector_sdk.contracts import strict_json
import build_catalogue
from publication_authorization import job_preflight, parse, MAX_REQUEST_BYTES
from publication_contract import canonical_json, digest, require, PublicationError
from publication_evidence import Archive, ArchiveVerifier, HistoricalLimits
from publication_github import Github
from publication_verify import read_regular, Verifier
from publish_catalogue import check_checkouts
from publish_catalogue_evidence import EvidencePublisher


@dataclass(frozen=True)
class SuccessorApproval:
    policy_sha256: str
    selection_seconds: int
    publication_seconds: int
    historical_decision: str
    selection_binding_decision: str
    recovery_decision: str  # This candidate supports only explicitly disabled recovery.


# Owner accepted ADR 0018 at the immutable Atlas commit below on 2026-11-05.
# This approves the contract only; independent security acceptance, a frozen S,
# workflow adoption and explicit operational activation remain outstanding.
# No runtime argument, producer archive or environment variable can replace it.
APPROVED_SUCCESSOR = SuccessorApproval(
    policy_sha256='c9a88eeb6c7e6d0a7f1a08eaa07eeed5ea251449db7104f7757626842cf1bbe9',
    selection_seconds=900,
    publication_seconds=300,
    historical_decision=(
        'https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/'
        'docs/decisions/0018-catalogue-durable-publication-evidence.md#historical-authorization'),
    selection_binding_decision=(
        'https://github.com/benchristian88/atlas/blob/76031dc6358a81c3babd15f74d407e22f0778dee/'
        'docs/decisions/0018-catalogue-durable-publication-evidence.md#selection-binding'),
    recovery_decision='disabled-pending-permanent-archive-decision',
)
# digest(canonical_json(asdict(APPROVED_SUCCESSOR))); never recomputed at runtime.
APPROVED_SUCCESSOR_SHA256 = '8a1c69168ed22dc2f0bff385da182de9bae913e900df031d4b47aabccd7e9070'


def approved_successor():
    value = APPROVED_SUCCESSOR
    require(type(value) is SuccessorApproval and APPROVED_SUCCESSOR_SHA256 is not None,
            'successor_owner_approval_required')
    require(digest(canonical_json(asdict(value))) == APPROVED_SUCCESSOR_SHA256,
            'successor_approval_pin_mismatch')
    require(type(value.policy_sha256) is str and re.fullmatch('[a-f0-9]{64}', value.policy_sha256) is not None,
            'successor_approval_identity')
    HistoricalLimits(value.selection_seconds, value.publication_seconds)
    require(all(type(v) is str and 0 < len(v) <= 256 for v in
                (value.historical_decision, value.selection_binding_decision)), 'successor_decisions_required')
    require(value.recovery_decision == 'disabled-pending-permanent-archive-decision',
            'successor_recovery_decision_required')
    return value


class CheckpointStore:
    def __init__(self, path, context):
        self.path, self.context = Path(path), context
        require(self.path.is_absolute() and self.path.parent.is_dir(), 'checkpoint_path')
        for part in (self.path, *self.path.parents):
            require(not part.is_symlink(), 'checkpoint_path')

    def load(self):
        if not self.path.exists():
            return None
        info = self.path.stat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and info.st_mode & 0o077 == 0, 'checkpoint_permissions')
        value = parse(read_regular(self.path, 32768), 32768)
        require(value.keys() == {'schema', 'context', 'checkpoint'}
                and value['schema'] == 'atlas-evidence-checkpoint/v1'
                and value['context'] == self.context, 'checkpoint_context')
        return value['checkpoint']

    def save(self, checkpoint):
        # Atomic replace prevents a torn checkpoint being mistaken for absence.
        # On an ambiguous provider response no checkpoint is guessed/reconstructed.
        self.load()
        raw = canonical_json({'schema': 'atlas-evidence-checkpoint/v1',
                              'context': self.context, 'checkpoint': checkpoint})
        require(len(raw) <= 32768, 'checkpoint_size')
        fd, name = tempfile.mkstemp(prefix='.checkpoint-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, self.path)
            fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            if os.path.exists(name):
                os.unlink(name)


def build_candidate(source_root):
    sequence, entries = build_catalogue.load_registry(source_root / 'catalogue/candidate-v2')
    require(sequence >= 2, 'candidate_sequence')
    document = build_catalogue.validate_catalogue({'schema_version': '1.0', 'sequence': sequence,
        'generated_at': build_catalogue.commit_timestamp(source_root).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'publisher_id': build_catalogue.PUBLISHER, 'repository': build_catalogue.REPOSITORY, 'entries': entries})
    return canonical_json(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('authorize', 'stage', 'finish', 'recover'))
    args = parser.parse_args()
    try:
        approval = approved_successor()  # Before credentials, checkout use or provider calls.
        require(args.phase != 'recover', 'recovery_archive_approval_required')
        root = Path(__file__).resolve().parents[1]
        source_root = root / 'publication-source'
        implementation = os.environ.get('ATLAS_IMPLEMENTATION_REVISION')
        check_checkouts(source_root, implementation, os.environ.get('GITHUB_SHA'))
        require(os.environ.get('PUBLICATION_OPERATION') == 'publish'
                and os.environ.get('ATLAS_CATALOGUE_EVIDENCE_ENABLED') == 'true', 'successor_execution_context')
        policy_raw = read_regular(source_root / 'catalogue/publication/policy.json', MAX_REQUEST_BYTES)
        require(digest(policy_raw) == approval.policy_sha256, 'successor_policy_pin')
        trust = strict_json(read_regular(source_root / 'catalogue/publication/verifier-trust.json', MAX_REQUEST_BYTES))
        require(trust['signer_revision'] == implementation, 'successor_signer_pin')
        value = job_preflight(os.environ, policy_raw, trust, startup=args.phase == 'authorize')
        if args.phase == 'authorize':
            print('successor original signed preflight admitted before publication credentials')
            return
        temporary = Path(os.environ['RUNNER_TEMP']).resolve(strict=True)
        preflight_dir = temporary / 'publication-preflight'
        archive = Archive.from_files([('preflight.json', read_regular(preflight_dir / 'preflight.json', 262144)),
            ('preflight.sigstore.json', read_regular(preflight_dir / 'preflight.sigstore.json', 1048576)),
            ('policy.json', policy_raw)])
        receipt = parse(read_regular(temporary / 'publication-preflight-started.json', MAX_REQUEST_BYTES), MAX_REQUEST_BYTES)
        context = {'run_id': int(os.environ['GITHUB_RUN_ID']), 'source_commit': os.environ['GITHUB_SHA'],
                   'preflight_sha256': digest(archive.preflight), 'policy_sha256': digest(policy_raw),
                   'implementation_revision': implementation}
        store = CheckpointStore(temporary / 'catalogue-evidence-checkpoint.json', context)
        publisher = EvidencePublisher(Github(os.environ.get('ATLAS_PUBLICATION_TOKEN'), draft_visibility=True),
            Verifier(), strict_json(policy_raw), context['run_id'], source_commit=context['source_commit'],
            token_identity={'app_slug': os.environ.get('ATLAS_APP_SLUG'),
                'installation_id': int(os.environ.get('ATLAS_APP_INSTALLATION_ID', '0'))},
            preflight=value, policy_raw=policy_raw, archive=archive,
            archive_verifier=ArchiveVerifier(trust, frozenset({approval.policy_sha256}),
                HistoricalLimits(approval.selection_seconds, approval.publication_seconds)),
            started_at=receipt['accepted_at'], checkpoint=store.load(), persist_checkpoint=store.save)
        output = root / 'dist/publication'
        output.mkdir(parents=True, exist_ok=True)
        raw = build_candidate(source_root)
        if args.phase == 'stage':
            staged = publisher.stage(raw)
            (output / 'current.json').write_bytes(staged.pointer)
            if staged.bundle is not None:
                (output / 'current.sigstore.json').write_bytes(staged.bundle)
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
                    stream.write(f'needs_attestation={str(staged.bundle is None).lower()}\n')
            result = {'result': 'staged', 'needs_attestation': staged.bundle is None}
        else:
            result = publisher.finish(raw, read_regular(output / 'current.json', 1024),
                                      read_regular(output / 'current.sigstore.json', 1048576))
        print(canonical_json(result).decode(), end='')
    except (ValueError, OSError, KeyError, TypeError, AttributeError):
        parser.exit(1, 'catalogue_evidence_driver_rejected\n')


if __name__ == '__main__':
    main()
