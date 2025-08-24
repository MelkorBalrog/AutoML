import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gui.architecture import DiagramConnection, SysMLObject, format_control_flow_label
from analysis.governance import GovernanceDiagram
from mainappsrc.models.sysml.sysml_repository import SysMLRepository

class GovernanceFlowGuardTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository.reset_instance()
        self.repo = SysMLRepository.get_instance()

    def test_guard_label_with_operators(self):
        conn = DiagramConnection(1, 2, "Flow", guard=["g1", "g2"], guard_ops=["OR"])
        label = format_control_flow_label(conn, self.repo, "Governance Diagram")
        self.assertEqual(label, "[g1\nOR g2] / <<flow>>")

    def test_guard_used_in_generation(self):
        repo = self.repo
        diag = repo.create_diagram("Governance Diagram", name="Gov")
        o1 = SysMLObject(1, "Action", 0, 0, properties={"name": "A"})
        o2 = SysMLObject(2, "Action", 0, 100, properties={"name": "B"})
        diag.objects = [o1.__dict__, o2.__dict__]
        conn = DiagramConnection(o1.obj_id, o2.obj_id, "Flow", guard=["g1", "g2"], guard_ops=["AND"])
        diag.connections = [conn.__dict__]
        gov = GovernanceDiagram.from_repository(repo, diag.diag_id)
        self.assertEqual(gov.edge_data[("A", "B")]["condition"], "g1 AND g2")

if __name__ == "__main__":
    unittest.main()
