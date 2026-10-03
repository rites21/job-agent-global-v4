import unittest
from unittest.mock import patch

import job_agent_v4_1_gemini as agent


class PrefilterTests(unittest.TestCase):
    profile = {"target_roles": ["Senior Software Engineer"]}

    def test_requested_titles(self):
        cases = [
            ("Senior Software Engineer in Test (SET) — Access Essentials", False),
            ("Senior Software Engineer - Fullstack", False),
            ("Senior Software Engineer Salesforce", False),
            ("Senior Software Engineer - Backend", True),
            ("Senior Software Engineer - Ingestion", True),
            ("Senior Software Engineer", True),
            ("Senior Software Engineer, AI Framework Integrations", True),
            ("Platform Engineer", True),
        ]
        for title, expected in cases:
            with self.subTest(title=title):
                job = {
                    "title": title,
                    "description": "Java backend test automation",
                    "location": "Bengaluru, India",
                }
                self.assertEqual(agent.rough_prefilter(job, self.profile), expected)

    def test_all_hard_exclusions_run_before_positive_checks(self):
        titles = [
            "software engineer in test", "sdet", "qa engineer", "quality engineer",
            "test automation", "salesforce", "frontend", "front-end", "fullstack",
            "full stack", "mobile engineer", "ios engineer", "android engineer",
            "devops", "site reliability", "sre", "release engineer",
            "release engineering", "release infrastructure", "staff engineer",
            "principal engineer", "engineering manager", "software engineering manager",
        ]
        with patch.object(agent, "target_role_signal", side_effect=AssertionError("target checked")), \
                patch.object(agent, "role_family", side_effect=AssertionError("family checked")):
            for title in titles:
                with self.subTest(title=title):
                    # No description: reaching technical matching would raise KeyError.
                    self.assertFalse(agent.rough_prefilter({"title": title.upper()}, self.profile))

    def test_generic_software_titles_need_no_description_keywords(self):
        for title in ("Software Engineer", "Senior Software Engineer", "Platform Engineer"):
            with self.subTest(title=title):
                self.assertTrue(agent.rough_prefilter({"title": title, "description": ""}, {}))


if __name__ == "__main__":
    unittest.main()
