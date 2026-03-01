#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET

class SalesDeskAITester:
    def __init__(self, base_url="https://814e0dda-6fa6-4e54-8531-53d036ceeb67.preview.emergentagent.com"):
        self.base_url = base_url.rstrip("/")
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log_result(self, test_name, success, details=""):
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name} - {details}")
        
        self.results.append({
            "test": test_name,
            "passed": success,
            "details": details
        })

    def test_page_response(self, path, expected_status=200, description=""):
        """Test if a page returns expected status code"""
        url = f"{self.base_url}{path}"
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            success = response.status_code == expected_status
            self.log_result(f"GET {path} → {expected_status}", success, 
                          f"Got {response.status_code}" if not success else "")
            return success, response
        except Exception as e:
            self.log_result(f"GET {path} → {expected_status}", False, str(e))
            return False, None

    def test_all_26_pages(self):
        """Test all 26 pages mentioned in requirements"""
        print("\n=== Testing All 26 Pages (RU + DE) ===")
        
        # Root page
        self.test_page_response("/")
        
        # Russian pages (13 pages)
        ru_pages = [
            "/ru/",
            "/ru/solutions/",
            "/ru/solutions/beauty/", 
            "/ru/solutions/education/",
            "/ru/pricing/",
            "/ru/demo/",
            "/ru/blog/",
            "/ru/blog/ai-sales-bot-chto-eto/",
            "/ru/about/",
            "/ru/contact/",
            "/ru/privacy/",
            "/ru/terms/",
            "/ru/cases/"
        ]
        
        # German pages (13 pages)  
        de_pages = [
            "/de/",
            "/de/solutions/",
            "/de/solutions/beauty/",
            "/de/solutions/education/", 
            "/de/pricing/",
            "/de/demo/",
            "/de/blog/",
            "/de/blog/ai-sales-bot-chto-eto/",  # Same slug, might not exist
            "/de/about/",
            "/de/contact/", 
            "/de/privacy/",
            "/de/terms/",
            "/de/cases/"
        ]
        
        for page in ru_pages + de_pages:
            self.test_page_response(page)
            
    def test_404_handling(self):
        """Test that non-existent pages return 404"""
        print("\n=== Testing 404 Handling ===")
        non_existent_pages = [
            "/fr/",
            "/en/",
            "/ru/nonexistent/",
            "/de/nonexistent/",
            "/ru/solutions/nonexistent/",
            "/random-page/"
        ]
        
        for page in non_existent_pages:
            self.test_page_response(page, 404)

    def test_sitemap_xml(self):
        """Test sitemap.xml validity and content"""
        print("\n=== Testing Sitemap.xml ===")
        success, response = self.test_page_response("/sitemap.xml")
        
        if success and response:
            try:
                # Parse XML
                root = ET.fromstring(response.text)
                
                # Check if it's a valid sitemap
                urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
                loc_count = len(urls)
                
                # Check for hreflang links
                hreflang_links = root.findall('.//{http://www.w3.org/1999/xhtml}link')
                hreflang_count = len(hreflang_links)
                
                self.log_result("Sitemap XML structure", True, f"{loc_count} URLs, {hreflang_count} hreflang links")
                
                # Check for specific pages
                url_texts = [url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text for url in urls]
                
                key_pages = ["/", "/ru/", "/de/", "/ru/pricing/", "/de/pricing/"]
                for page in key_pages:
                    expected_url = f"{self.base_url}{page}"
                    found = any(expected_url in url for url in url_texts)
                    self.log_result(f"Sitemap contains {page}", found)
                    
            except ET.ParseError as e:
                self.log_result("Sitemap XML parsing", False, f"Invalid XML: {e}")
        
    def test_robots_txt(self):
        """Test robots.txt content"""
        print("\n=== Testing Robots.txt ===")
        success, response = self.test_page_response("/robots.txt")
        
        if success and response:
            content = response.text.lower()
            
            # Check required content
            has_user_agent = "user-agent:" in content
            has_allow = "allow:" in content  
            has_sitemap = "sitemap:" in content and self.base_url.lower() in content
            
            self.log_result("Robots.txt has User-agent", has_user_agent)
            self.log_result("Robots.txt has Allow directive", has_allow)
            self.log_result("Robots.txt has Sitemap URL", has_sitemap)

    def test_api_lead_endpoint(self):
        """Test /api/lead endpoint with various payloads"""
        print("\n=== Testing /api/lead Endpoint ===")
        
        # Test 1: Valid full payload
        valid_payload = {
            "name": "Test User",
            "phone": "+1234567890", 
            "business": "beauty",
            "message": "Test inquiry about AI bot",
            "lang": "de",
            "source": "contact_page",
            "lead_type": "implementation", 
            "page_url": "https://example.com/de/contact/",
            "referrer": "https://google.com",
            "utm_source": "google",
            "utm_medium": "cpc", 
            "utm_campaign": "test_campaign",
            "utm_content": "test_content",
            "utm_term": "ai bot"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/lead", json=valid_payload, timeout=10)
            success = response.status_code == 200 and "ok" in response.text.lower()
            self.log_result("POST /api/lead valid payload → 200", success, 
                          f"Status: {response.status_code}, Response: {response.text[:100]}")
        except Exception as e:
            self.log_result("POST /api/lead valid payload → 200", False, str(e))
        
        # Test 2: Honeypot protection
        honeypot_payload = valid_payload.copy()
        honeypot_payload["website"] = "https://spam.com"
        
        try:
            response = requests.post(f"{self.base_url}/api/lead", json=honeypot_payload, timeout=10)
            success = response.status_code == 200  # Should still return 200 but ignore
            self.log_result("POST /api/lead honeypot → 200 (ignored)", success)
        except Exception as e:
            self.log_result("POST /api/lead honeypot → 200 (ignored)", False, str(e))
        
        # Test 3: Missing required fields
        invalid_payload = {"message": "Missing name and phone"}
        
        try:
            response = requests.post(f"{self.base_url}/api/lead", json=invalid_payload, timeout=10)
            success = response.status_code == 400
            self.log_result("POST /api/lead missing fields → 400", success, 
                          f"Got {response.status_code}")
        except Exception as e:
            self.log_result("POST /api/lead missing fields → 400", False, str(e))

    def test_health_endpoint(self):
        """Test health check endpoint"""
        print("\n=== Testing Health Endpoint ===")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200 and "ok" in response.text.lower()
            self.log_result("GET /api/health → 200", success)
        except Exception as e:
            self.log_result("GET /api/health → 200", False, str(e))

    def test_meta_tags_and_og_images(self):
        """Test OG images and meta tags on key pages"""
        print("\n=== Testing Meta Tags & OG Images ===")
        
        key_pages = ["/ru/", "/de/", "/ru/pricing/", "/de/contact/"]
        
        for page in key_pages:
            success, response = self.test_page_response(page)
            if success and response:
                content = response.text.lower()
                
                # Check for OG image
                has_og_image = 'property="og:image"' in content
                self.log_result(f"{page} has og:image meta tag", has_og_image)
                
                # Check for canonical
                has_canonical = 'rel="canonical"' in content  
                self.log_result(f"{page} has canonical link", has_canonical)
                
                # Check for hreflang
                has_hreflang = 'hreflang=' in content
                self.log_result(f"{page} has hreflang links", has_hreflang)

    def test_german_umlauts(self):
        """Test German content contains proper umlauts"""
        print("\n=== Testing German Umlauts ===")
        
        success, response = self.test_page_response("/de/")
        if success and response:
            content = response.text
            
            # Check for German umlauts in navigation
            has_loesungen = "lösungen" in content.lower()
            has_ueber_uns = "über uns" in content.lower()
            has_preise = "preise" in content.lower()
            
            self.log_result("DE navigation shows 'Lösungen'", has_loesungen)
            self.log_result("DE navigation shows 'Über uns'", has_ueber_uns) 
            self.log_result("DE navigation shows 'Preise'", has_preise)
            
            # Check for DSGVO in consent banner
            success_consent, response_consent = self.test_page_response("/de/contact/")
            if success_consent and response_consent:
                has_dsgvo = "dsgvo" in response_consent.text.lower()
                self.log_result("DE consent banner shows 'DSGVO'", has_dsgvo)

    def test_schema_structured_data(self):
        """Test structured data schemas"""
        print("\n=== Testing Structured Data Schemas ===")
        
        # Home page should have FAQPage + SoftwareApplication + Organization + WebSite
        success, response = self.test_page_response("/ru/")
        if success and response:
            content = response.text
            
            has_faq_schema = '"@type":"FAQPage"' in content or '"@type": "FAQPage"' in content
            has_software_schema = '"@type":"SoftwareApplication"' in content or '"@type": "SoftwareApplication"' in content  
            has_org_schema = '"@type":"Organization"' in content or '"@type": "Organization"' in content
            has_website_schema = '"@type":"WebSite"' in content or '"@type": "WebSite"' in content
            
            self.log_result("Home page has FAQPage schema", has_faq_schema)
            self.log_result("Home page has SoftwareApplication schema", has_software_schema)
            self.log_result("Home page has Organization schema", has_org_schema)
            self.log_result("Home page has WebSite schema", has_website_schema)
        
        # Blog post should have Article schema
        success, response = self.test_page_response("/ru/blog/ai-sales-bot-chto-eto/")
        if success and response:
            content = response.text
            has_article_schema = '"@type":"Article"' in content or '"@type": "Article"' in content
            self.log_result("Blog post has Article schema", has_article_schema)

    def run_all_tests(self):
        """Run all tests"""
        print(f"🧪 Starting SalesDesk AI Testing - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Testing site: {self.base_url}")
        
        self.test_all_26_pages()
        self.test_404_handling() 
        self.test_sitemap_xml()
        self.test_robots_txt()
        self.test_api_lead_endpoint()
        self.test_health_endpoint()
        self.test_meta_tags_and_og_images()
        self.test_german_umlauts()
        self.test_schema_structured_data()
        
        # Final summary
        print(f"\n📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "results": self.results
        }

def main():
    tester = SalesDeskAITester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("/app/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return 0 if results["success_rate"] >= 90 else 1

if __name__ == "__main__":
    exit(main())