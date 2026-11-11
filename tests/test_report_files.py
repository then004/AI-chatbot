import unittest
from pathlib import Path
from core.report_files import resolve_report_files

class ReportFileTests(unittest.TestCase):
    def test_structured_uses_pipeline_run_and_paths(self):
        result = resolve_report_files('ignored', {'run_id': 'm3-test', 'output_dir': r'C:\reports\m3-test'})
        self.assertEqual(result['run_id'], 'm3-test')
        self.assertEqual(result['html_path'], str(Path(r'C:\reports\m3-test') / 'Business_Plan.html'))
        self.assertEqual(result['json_path'], str(Path(r'C:\reports\m3-test') / 'Business_Plan.json'))

    def test_legacy_uses_microsecond_run_id(self):
        result = resolve_report_files(r'C:\startup')
        self.assertRegex(result['run_id'], r'^\d{8}_\d{6}_\d{6}$')
        self.assertIn(result['run_id'], result['html_path'])

    def test_structured_failure_has_no_file_resolution(self):
        with self.assertRaises(KeyError): resolve_report_files('ignored', {'output_dir': r'C:\reports'})

if __name__ == '__main__': unittest.main()
