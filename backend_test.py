#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for SalesDesk AI Website
Testing all routes, API endpoints, SEO features, and data validation
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import re


class SalesDeskAPITester:
    def __init__(self, base_url: str = "https://814e0dda-6fa6-4e54-8531-53d036ceeb67.preview.emergentagent.com"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SalesDesk-Test-Bot/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []
        
        # Expected page paths
        self.ru_pages = [
            "/ru/", "/ru/solutions/", "/ru/solutions/beauty/", "/ru/solutions/education/",
            "/ru/pricing/", "/ru/demo/", "/ru/blog/", "/ru/blog/ai-sales-bot-chto-eto/",
            "/ru/about/", "/ru/contact/", "/ru/privacy/", "/ru/terms/", "/ru/cases/"
        ]
        
        self.de_pages = [
            "/de/", "/de/solutions/", "/de/solutions/beauty/", "/de/solutions/education/",
            "/de/pricing/", "/de/demo/", "/de/blog/", "/de/blog/ki-sales-bot-was-ist-das/",
            "/de/about/", "/de/contact/", "/de/privacy/", "/de/terms/", "/de/cases/"
        ]

    def log_test(self, name: str, success: bool, details: str = "", status_code: int = 0):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            self.passed_tests.append(f"✅ {name}")
            print(f"✅ {name}")
        else:
            self.failed_tests.append(f"❌ {name}: {details}")
            print(f"❌ {name}: {details} (Status: {status_code})")

    def test_route(self, path: str, expected_status: int = 200, check_content: List[str] = None) -> Tuple[bool, str, int]:
        """Test a single route"""
        try:
            url = f"{self.base_url}{path}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != expected_status:
                return False, f"Expected {expected_status}, got {response.status_code}", response.status_code
            
            if check_content:
                content = response.text.lower()
                for item in check_content:
                    if item.lower() not in content:
                        return False, f"Missing content: '{item}'", response.status_code
            
            return True, "OK", response.status_code
            
        except Exception as e:
            return False, f"Request failed: {str(e)}", 0

    def test_root_language_chooser(self):
        """Test root path returns language chooser"""
        success, details, status_code = self.test_route("/", 200, ["ru", "de", "SalesDesk AI"])
        self.log_test("Root / language chooser", success, details, status_code)

    def test_russian_pages(self):
        """Test all Russian language pages"""
        for page in self.ru_pages:
            success, details, status_code = self.test_route(page, 200, ["SalesDesk AI"])
            self.log_test(f"RU page {page}", success, details, status_code)

    def test_german_pages(self):
        """Test all German language pages"""
        for page in self.de_pages:
            success, details, status_code = self.test_route(page, 200, ["SalesDesk AI"])
            self.log_test(f"DE page {page}", success, details, status_code)

    def test_404_pages(self):
        """Test non-existent pages return 404"""
        test_404_paths = ["/fr/", "/ru/nonexistent/", "/de/invalid/", "/invalid"]
        
        for path in test_404_paths:
            success, details, status_code = self.test_route(path, 404)
            self.log_test(f"404 test {path}", success, details, status_code)

    def test_sitemap_xml(self):
        """Test sitemap.xml returns proper XML with hreflang"""
        try:
            url = f"{self.base_url}/sitemap.xml"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Sitemap XML", False, f"Status {response.status_code}", response.status_code)
                return
            
            content = response.text
            checks = [
                "<urlset" in content,
                "xhtml:link" in content,
                "hreflang=" in content,
                "/ru/" in content,
                "/de/" in content,
                "x-default" in content
            ]
            
            if all(checks):
                self.log_test("Sitemap XML", True)
            else:
                self.log_test("Sitemap XML", False, "Missing required XML elements or hreflang links")
                
        except Exception as e:
            self.log_test("Sitemap XML", False, f"Request failed: {str(e)}")

    def test_robots_txt(self):
        """Test robots.txt returns proper content"""
        try:
            url = f"{self.base_url}/robots.txt"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                self.log_test("Robots.txt", False, f"Status {response.status_code}", response.status_code)
                return
            
            content = response.text
            checks = [
                "User-agent:" in content,
                "Allow:" in content,
                "Sitemap:" in content,
                "/sitemap.xml" in content
            ]
            
            if all(checks):
                self.log_test("Robots.txt", True)
            else:
                self.log_test("Robots.txt", False, "Missing required robots.txt directives")
                
        except Exception as e:
            self.log_test("Robots.txt", False, f"Request failed: {str(e)}")

    def test_api_lead_valid(self):
        """Test POST /api/lead with valid data"""
        try:
            url = f"{self.base_url}/api/lead"
            data = {
                "name": "Test User",
                "phone": "+1234567890",
                "business": "beauty",
                "message": "Test message for API",
                "lang": "ru",
                "source": "test"
            }
            
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if json_response.get("status") == "ok":
                        self.log_test("API /api/lead valid data", True)
                    else:
                        self.log_test("API /api/lead valid data", False, f"Unexpected response: {json_response}")
                except json.JSONDecodeError:
                    self.log_test("API /api/lead valid data", False, "Invalid JSON response")
            else:
                self.log_test("API /api/lead valid data", False, f"Status {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("API /api/lead valid data", False, f"Request failed: {str(e)}")

    def test_api_lead_invalid(self):
        """Test POST /api/lead with invalid data (missing required fields)"""
        try:
            url = f"{self.base_url}/api/lead"
            data = {
                "message": "Missing name and phone"
            }
            
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 400:
                self.log_test("API /api/lead invalid data (400)", True)
            else:
                self.log_test("API /api/lead invalid data (400)", False, f"Expected 400, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("API /api/lead invalid data", False, f"Request failed: {str(e)}")

    def test_api_lead_honeypot(self):
        """Test POST /api/lead with honeypot field (should return 200 but ignore)"""
        try:
            url = f"{self.base_url}/api/lead"
            data = {
                "name": "Test Bot",
                "phone": "+1234567890",
                "website": "https://spam.com",  # honeypot field
                "business": "beauty"
            }
            
            response = self.session.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if json_response.get("status") == "ok":
                        self.log_test("API /api/lead honeypot protection", True)
                    else:
                        self.log_test("API /api/lead honeypot protection", False, f"Unexpected response: {json_response}")
                except json.JSONDecodeError:
                    self.log_test("API /api/lead honeypot protection", False, "Invalid JSON response")
            else:
                self.log_test("API /api/lead honeypot protection", False, f"Status {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("API /api/lead honeypot protection", False, f"Request failed: {str(e)}")

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        try:
            url = f"{self.base_url}/api/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if json_response.get("status") == "ok":
                        self.log_test("API /api/health", True)
                    else:
                        self.log_test("API /api/health", False, f"Unexpected response: {json_response}")
                except json.JSONDecodeError:
                    self.log_test("API /api/health", False, "Invalid JSON response")
            else:
                self.log_test("API /api/health", False, f"Status {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("API /api/health", False, f"Request failed: {str(e)}")

    def test_seo_meta_tags(self):
        """Test SEO meta tags on key pages"""
        test_pages = ["/ru/", "/de/", "/ru/pricing/", "/de/pricing/"]
        
        for page in test_pages:
            try:
                url = f"{self.base_url}{page}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code != 200:
                    self.log_test(f"SEO meta {page}", False, f"Page not accessible: {response.status_code}", response.status_code)
                    continue
                
                content = response.text
                checks = {
                    "title": "<title>" in content,
                    "meta_desc": 'name="description"' in content,
                    "canonical": 'rel="canonical"' in content,
                    "hreflang": 'rel="alternate" hreflang=' in content,
                    "og_title": 'property="og:title"' in content,
                    "schema": 'type="application/ld+json"' in content
                }
                
                failed_checks = [name for name, passed in checks.items() if not passed]
                
                if not failed_checks:
                    self.log_test(f"SEO meta {page}", True)
                else:
                    self.log_test(f"SEO meta {page}", False, f"Missing: {', '.join(failed_checks)}")
                    
            except Exception as e:
                self.log_test(f"SEO meta {page}", False, f"Request failed: {str(e)}")

    def test_json_ld_schemas(self):
        """Test JSON-LD schemas on specific pages"""
        schema_tests = [
            ("/ru/", ["Organization", "WebSite", "FAQPage", "SoftwareApplication"]),
            ("/de/", ["Organization", "WebSite", "FAQPage", "SoftwareApplication"]),
            ("/ru/pricing/", ["Organization", "WebSite", "SoftwareApplication"]),
            ("/ru/blog/ai-sales-bot-chto-eto/", ["Organization", "WebSite", "Article"])
        ]
        
        for page, expected_schemas in schema_tests:
            try:
                url = f"{self.base_url}{page}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code != 200:
                    self.log_test(f"JSON-LD {page}", False, f"Page not accessible: {response.status_code}", response.status_code)
                    continue
                
                content = response.text
                
                missing_schemas = []
                for schema in expected_schemas:
                    if f'"@type": "{schema}"' not in content:
                        missing_schemas.append(schema)
                
                if not missing_schemas:
                    self.log_test(f"JSON-LD {page}", True)
                else:
                    self.log_test(f"JSON-LD {page}", False, f"Missing schemas: {', '.join(missing_schemas)}")
                    
            except Exception as e:
                self.log_test(f"JSON-LD {page}", False, f"Request failed: {str(e)}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting SalesDesk AI Backend Testing...")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        print("\n📍 Testing Core Routes...")
        self.test_root_language_chooser()
        
        print("\n🇷🇺 Testing Russian Pages...")
        self.test_russian_pages()
        
        print("\n🇩🇪 Testing German Pages...")
        self.test_german_pages()
        
        print("\n🔍 Testing 404 Pages...")
        self.test_404_pages()
        
        print("\n🗺️  Testing SEO Files...")
        self.test_sitemap_xml()
        self.test_robots_txt()
        
        print("\n🔗 Testing API Endpoints...")
        self.test_health_endpoint()
        self.test_api_lead_valid()
        self.test_api_lead_invalid()
        self.test_api_lead_honeypot()
        
        print("\n🔍 Testing SEO Meta Tags...")
        self.test_seo_meta_tags()
        
        print("\n📋 Testing JSON-LD Schemas...")
        self.test_json_ld_schemas()
        
        # Results summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"  {test}")
        
        if self.passed_tests:
            print(f"\n✅ Passed Tests ({len(self.passed_tests)}):")
            for test in self.passed_tests[:10]:  # Show first 10
                print(f"  {test}")
            if len(self.passed_tests) > 10:
                print(f"  ... and {len(self.passed_tests) - 10} more")
        
        return len(self.failed_tests) == 0


def main():
    """Main test execution"""
    tester = SalesDeskAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())