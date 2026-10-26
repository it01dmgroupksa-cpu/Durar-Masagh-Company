# Run: bench --site <site> run-tests --module durar_masagh_company.tests.test_custom_html_block_permissions
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from durar_masagh_company import custom_html_block_permissions as m

READ_ROLES = [
	"CEO", "IT Coordinator", "Metabase", "Internal Controller", "Purchase User", "Sales Person",
	"Technical Coordinator", "DMS Sales Person Access", "AR Accountant",
	"Manufacturing Dashboard Viewer", "Treasury Manager", "Driver Dashboard User",
]
USERS = {
	"driver@x": ["Employee", "Driver", "Driver Dashboard User", "All", "Guest"],
	"sales@x": ["Employee", "Sales Person"],
	"employee@x": ["Employee"],
	"sysman@x": ["System Manager", "Driver Dashboard User"],
	"multi@x": ["CEO", "Driver Dashboard User"],
	"Administrator": ["Administrator"],
}


def meta(_dt):
	return SimpleNamespace(permissions=[SimpleNamespace(role=r, read=1, select=0, permlevel=0) for r in READ_ROLES])


def doc(name):
	return SimpleNamespace(name=name)


@patch.object(m.frappe, "get_meta", side_effect=meta)
@patch.object(m.frappe, "get_roles", side_effect=lambda u: USERS.get(u, []))
class TestCustomHTMLBlockPermissions(unittest.TestCase):
	def test_driver_allowed_block(self, *_):
		self.assertIsNone(m.has_permission(doc("ESS UI - Driver"), "read", "driver@x"))

	def test_driver_denied_other_blocks(self, *_):
		for name in ("CEO Command Center", "Employee Dashboard Prototype", "HR Dashboard Block"):
			self.assertIs(m.has_permission(doc(name), "read", "driver@x"), False)

	def test_driver_denied_write(self, *_):
		for ptype in ("write", "create", "delete", "export", "share"):
			self.assertIs(m.has_permission(doc("ESS UI - Driver"), ptype, "driver@x"), False)

	def test_driver_list_filter(self, *_):
		c = m.get_permission_query_conditions("driver@x", doctype="Custom HTML Block")
		self.assertIn("`tabCustom HTML Block`.`name` in (", c)
		self.assertIn("ESS UI - Driver", c)
		self.assertNotIn("CEO", c)

	def test_unaffected_users(self, *_):
		for user in ("sales@x", "employee@x", "sysman@x", "multi@x", "Administrator"):
			self.assertIsNone(m.has_permission(doc("CEO Command Center"), "read", user))
			self.assertEqual(m.get_permission_query_conditions(user), "")

	def test_hook_never_grants(self, *_):
		for user in USERS:
			for name in ("ESS UI - Driver", "CEO Command Center"):
				self.assertIn(m.has_permission(doc(name), "read", user), (None, False))
