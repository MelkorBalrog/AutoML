import unittest
from gui.architecture import SysMLObject, SysMLDiagramWindow, GovernanceDiagramWindow
from sysml.sysml_repository import SysMLRepository, SysMLDiagram


class WorkProductProcessAreaLockTests(unittest.TestCase):
    class DummyCanvas:
        def canvasx(self, x):
            return x

        def canvasy(self, y):
            return y

        def delete(self, *args, **kwargs):
            pass

        def configure(self, **kwargs):
            pass

    class DummyEvent:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    def setUp(self):
        SysMLRepository._instance = None
        self.repo = SysMLRepository.get_instance()

    def _create_window(self):
        repo = self.repo
        diag = SysMLDiagram(diag_id="d", diag_type="Governance Diagram")
        repo.diagrams[diag.diag_id] = diag
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        boundary = SysMLObject(1, "System Boundary", 0.0, 0.0, width=100.0, height=100.0)
        wp = SysMLObject(2, "Work Product", 0.0, 0.0, properties={"boundary": "1", "name": "WP", "name_locked": "1"})
        win.objects = [boundary, wp]
        win.connections = []
        win.canvas = self.DummyCanvas()
        win.zoom = 1.0
        win.current_tool = "Select"
        win.selected_obj = wp
        win.drag_offset = (0, 0)
        win.resizing_obj = None
        win.start = None
        win.select_rect_start = None
        win.dragging_point_index = None
        win.dragging_endpoint = None
        win.conn_drag_offset = None
        win.endpoint_drag_pos = None
        win.app = None
        win.selected_conn = None
        win._constrain_horizontal_movement = SysMLDiagramWindow._constrain_horizontal_movement.__get__(win)
        win.get_object = SysMLDiagramWindow.get_object.__get__(win)
        win.get_ibd_boundary = SysMLDiagramWindow.get_ibd_boundary.__get__(win)
        win.find_boundary_for_obj = SysMLDiagramWindow.find_boundary_for_obj.__get__(win)
        win._object_within = SysMLDiagramWindow._object_within.__get__(win)
        win.redraw = lambda: None
        win._sync_to_repository = lambda: None
        return win, boundary, wp

    def _create_window_with_parent(self):
        repo = self.repo
        diag = SysMLDiagram(diag_id="d", diag_type="Governance Diagram")
        repo.diagrams[diag.diag_id] = diag
        win = GovernanceDiagramWindow.__new__(GovernanceDiagramWindow)
        win.repo = repo
        win.diagram_id = diag.diag_id
        win.objects = []
        win.connections = []
        win.canvas = self.DummyCanvas()
        win.zoom = 1.0
        win.current_tool = "Select"
        win.selected_obj = None
        win.drag_offset = (0, 0)
        win.resizing_obj = None
        win.start = None
        win.select_rect_start = None
        win.dragging_point_index = None
        win.dragging_endpoint = None
        win.conn_drag_offset = None
        win.endpoint_drag_pos = None
        win.app = None
        win.selected_conn = None
        win._constrain_horizontal_movement = SysMLDiagramWindow._constrain_horizontal_movement.__get__(win)
        win.get_object = SysMLDiagramWindow.get_object.__get__(win)
        win.get_ibd_boundary = SysMLDiagramWindow.get_ibd_boundary.__get__(win)
        win.find_boundary_for_obj = SysMLDiagramWindow.find_boundary_for_obj.__get__(win)
        win._object_within = SysMLDiagramWindow._object_within.__get__(win)
        win.redraw = lambda: None
        win._sync_to_repository = lambda: None
        area = win._place_process_area("Risk Assessment", 0.0, 0.0)
        wp = win._place_work_product("Risk Assessment", 10.0, 10.0, area=area)
        win.selected_obj = area
        return win, area, wp

    def test_work_product_remains_in_process_area(self):
        win, boundary, wp = self._create_window()
        win.on_left_drag(self.DummyEvent(200, 0))
        win.on_left_release(self.DummyEvent(200, 0))
        self.assertEqual(wp.properties.get("boundary"), "1")
        expected_x = boundary.x + boundary.width / 2 - wp.width / 2
        self.assertEqual((wp.x, wp.y), (expected_x, boundary.y))

    def test_work_product_position_preserved_on_boundary_move(self):
        win, boundary, wp = self._create_window_with_parent()
        offx = wp.x - boundary.x
        offy = wp.y - boundary.y
        win.on_left_drag(self.DummyEvent(100, 50))
        win.on_left_release(self.DummyEvent(100, 50))
        self.assertEqual((wp.x - boundary.x, wp.y - boundary.y), (offx, offy))


if __name__ == "__main__":
    unittest.main()
