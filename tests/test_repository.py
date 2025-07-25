import unittest
import os
from sysml_repository import SysMLRepository

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def test_create_elements(self):
        actor = self.repo.create_element("Actor", name="User")
        use_case = self.repo.create_element("Use Case", name="Login")
        self.assertNotEqual(actor.elem_id, use_case.elem_id)
        self.assertEqual(actor.name, "User")
        self.assertEqual(use_case.name, "Login")

    def test_create_relationship(self):
        a = self.repo.create_element("Actor")
        b = self.repo.create_element("Use Case")
        rel = self.repo.create_relationship("Association", a.elem_id, b.elem_id)
        self.assertEqual(rel.source, a.elem_id)
        self.assertEqual(rel.target, b.elem_id)

    def test_serialize(self):
        blk = self.repo.create_element("Block", name="Car")
        js = self.repo.serialize()
        self.assertIn("Car", js)
        self.assertIn(blk.elem_id, js)

    def test_sysml_properties_port(self):
        from sysml_spec import SYSML_PROPERTIES
        self.assertIn("PortUsage", SYSML_PROPERTIES)
        self.assertIn("direction", SYSML_PROPERTIES["PortUsage"])

    def test_packages_and_save_load(self):
        pkg = self.repo.create_package("PkgA")
        blk = self.repo.create_element("Block", name="Engine", owner=pkg.elem_id)
        qn = self.repo.get_qualified_name(blk.elem_id)
        self.assertEqual(qn.split("::")[-1], "Engine")
        path = "repo_test.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        self.assertIn(blk.elem_id, new_repo.elements)
        self.assertEqual(new_repo.get_qualified_name(blk.elem_id), qn)

    def test_diagram_creation_and_persistence(self):
        diag = self.repo.create_diagram("Use Case Diagram", name="UC1")
        actor = self.repo.create_element("Actor")
        self.repo.add_element_to_diagram(diag.diag_id, actor.elem_id)
        path = "repo_diag.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        self.assertIn(diag.diag_id, new_repo.diagrams)
        self.assertIn(actor.elem_id, new_repo.diagrams[diag.diag_id].elements)

    def test_element_diagram_linking(self):
        uc = self.repo.create_element("Use Case")
        ad = self.repo.create_diagram("Activity Diagram", name="AD1")
        self.repo.link_diagram(uc.elem_id, ad.diag_id)
        linked = self.repo.get_linked_diagram(uc.elem_id)
        self.assertEqual(linked, ad.diag_id)
        path = "repo_link.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        self.assertEqual(new_repo.get_linked_diagram(uc.elem_id), ad.diag_id)

    def test_diagram_package(self):
        pkg = self.repo.create_package("PkgA")
        diag = self.repo.create_diagram("Use Case Diagram", name="UC2", package=pkg.elem_id)
        self.assertEqual(diag.package, pkg.elem_id)
        path = "repo_pkg.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        self.assertEqual(new_repo.diagrams[diag.diag_id].package, pkg.elem_id)

    def test_delete_package_reassign(self):
        pkg = self.repo.create_package("P1")
        sub = self.repo.create_package("Sub", parent=pkg.elem_id)
        blk = self.repo.create_element("Block", owner=sub.elem_id)
        diag = self.repo.create_diagram("Use Case Diagram", package=sub.elem_id)
        self.repo.delete_package(sub.elem_id)
        self.assertEqual(self.repo.elements[blk.elem_id].owner, pkg.elem_id)
        self.assertEqual(self.repo.diagrams[diag.diag_id].package, pkg.elem_id)

    def test_diagram_object_persistence(self):
        diag = self.repo.create_diagram("Use Case Diagram", name="UC")
        actor = self.repo.create_element("Actor", name="User")
        self.repo.add_element_to_diagram(diag.diag_id, actor.elem_id)
        diag.objects = [
            {
                "obj_id": 1,
                "obj_type": "Actor",
                "x": 100,
                "y": 100,
                "element_id": actor.elem_id,
                "width": 80.0,
                "height": 40.0,
                "properties": {"name": "User"},
            }
        ]
        path = "repo_objs.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        nd = new_repo.diagrams[diag.diag_id]
        self.assertEqual(len(nd.objects), 1)
        self.assertEqual(nd.objects[0]["element_id"], actor.elem_id)

    def test_object_requirements_persistence(self):
        diag = self.repo.create_diagram("Use Case Diagram", name="UC")
        actor = self.repo.create_element("Actor", name="User")
        self.repo.add_element_to_diagram(diag.diag_id, actor.elem_id)
        diag.objects = [
            {
                "obj_id": 1,
                "obj_type": "Actor",
                "x": 50,
                "y": 60,
                "element_id": actor.elem_id,
                "width": 80.0,
                "height": 40.0,
                "properties": {"name": "User"},
                "requirements": [{"id": "REQ1", "text": "Test"}],
            }
        ]
        path = "repo_req.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        obj = new_repo.diagrams[diag.diag_id].objects[0]
        self.assertEqual(obj.get("requirements")[0]["id"], "REQ1")

    def test_connection_persistence(self):
        diag = self.repo.create_diagram("Block Diagram", name="BD")
        a = self.repo.create_element("Block", name="A")
        b = self.repo.create_element("Block", name="B")
        self.repo.add_element_to_diagram(diag.diag_id, a.elem_id)
        self.repo.add_element_to_diagram(diag.diag_id, b.elem_id)
        diag.objects = [
            {"obj_id": 1, "obj_type": "Block", "x": 0, "y": 0, "element_id": a.elem_id, "width": 80.0, "height": 40.0},
            {"obj_id": 2, "obj_type": "Block", "x": 100, "y": 0, "element_id": b.elem_id, "width": 80.0, "height": 40.0},
        ]
        diag.connections = [
            {"src": 1, "dst": 2, "conn_type": "Association", "style": "Straight", "points": []}
        ]
        path = "repo_conn.json"
        self.repo.save(path)
        SysMLRepository._instance = None
        new_repo = SysMLRepository.get_instance()
        new_repo.load(path)
        os.remove(path)
        nd = new_repo.diagrams[diag.diag_id]
        self.assertEqual(len(nd.connections), 1)
        self.assertEqual(nd.connections[0]["conn_type"], "Association")

if __name__ == '__main__':
    unittest.main()
