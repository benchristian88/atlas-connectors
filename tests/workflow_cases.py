# SPDX-License-Identifier: Apache-2.0
"""Explicit test profiles, never production authority or an automatic pin choice."""
from dataclasses import dataclass
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
S4 = '2dd1ffcd2f5677dc35bdbc8f68ea28275c91c285'
SUCCESSOR = '4be90c5292f931497473595a0958cc5e0f9d1beb'
SYNTHETIC_SUCCESSOR = 'a' * 40


@dataclass(frozen=True)
class WorkflowCase:
    raw: str
    pin: str
    driver: str
    successor: bool


@pytest.fixture(params=['historical-s4', 'generated-successor', 'adopted-successor'])
def publisher_case(request):
    from prepare_evidence_workflow import template, prepare
    if request.param == 'historical-s4':
        return WorkflowCase(template('catalogue-publish-s4.yml'), S4, 'tools/publish_catalogue.py', False)
    if request.param == 'adopted-successor':
        return WorkflowCase((ROOT / '.github/workflows/catalogue-publish.yml').read_text(),
                            SUCCESSOR, 'tools/catalogue_evidence_driver.py', True)
    return WorkflowCase(prepare(SYNTHETIC_SUCCESSOR), SYNTHETIC_SUCCESSOR, 'tools/catalogue_evidence_driver.py', True)
