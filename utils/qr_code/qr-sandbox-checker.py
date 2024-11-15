import os
import subprocess
import docker
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cv2
from pyzbar.pyzbar import decode
import json
import requests
from urllib.parse import urlparse
import time

class QRSandboxAnalyzer:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.chrome_options = self._setup_chrome_options()
        
    def _setup_chrome_options(self):
        """Setup isolated Chrome instance options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-javascript')  # Optional: enable if needed
        return chrome_options

    def create_sandbox_container(self):
        """Create an isolated Docker container for analysis"""
        container = self.docker_client.containers.run(
            'alpine:latest',  # Using minimal Alpine Linux
            command='tail -f /dev/null',  # Keep container running
            detach=True,
            remove=True,
            network_mode='none',  # Isolated network
            cpu_quota=50000,  # Limit CPU
            mem_limit='256m',  # Limit memory
            security_opt=['no-new-privileges:true'],
            cap_drop=['ALL'],  # Drop all capabilities
            volumes={
                '/tmp': {'bind': '/sandbox', 'mode': 'ro'}  # Read-only mount
            }
        )
        return container

    def analyze_in_selenium(self, url):
        """Analyze URL behavior in isolated Chrome instance"""
        results = {
            'redirects': [],
            'resources': [],
            'suspicious_behaviors': [],
            'risk_level': 'LOW'
        }
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.set_page_load_timeout(10)
            
            # Create a proxy to intercept requests
            def interceptor(request):
                results['resources'].append({
                    'url': request.url,
                    'type': request.resource_type
                })
            
            driver.request_interceptor = interceptor
            
            # Load URL and monitor behavior
            driver.get(url)
            
            # Check for redirects
            if driver.current_url != url:
                results['redirects'].append({
                    'from': url,
                    'to': driver.current_url
                })
                results['risk_level'] = 'MEDIUM'
            
            # Check for suspicious behaviors
            if len(driver.window_handles) > 1:
                results['suspicious_behaviors'].append('Multiple windows/tabs opened')
                results['risk_level'] = 'HIGH'
            
            # Check for file downloads
            downloads = driver.execute_script(
                "return window.performance.getEntriesByType('resource')"
            )
            for download in downloads:
                if any(ext in download['name'] for ext in ['.exe', '.bat', '.ps1']):
                    results['suspicious_behaviors'].append(f"Attempted download: {download['name']}")
                    results['risk_level'] = 'HIGH'
            
            return results
            
        except Exception as e:
            results['suspicious_behaviors'].append(f"Error during analysis: {str(e)}")
            results['risk_level'] = 'UNKNOWN'
            return results
        finally:
            if 'driver' in locals():
                driver.quit()

    def analyze_in_sandbox(self, qr_data):
        """Full sandbox analysis of QR code content"""
        container = None
        results = {
            'static_analysis': {},
            'dynamic_analysis': {},
            'network_analysis': {},
            'final_verdict': 'UNKNOWN'
        }
        
        try:
            # Create sandbox container
            container = self.create_sandbox_container()
            
            # Static Analysis
            results['static_analysis'] = self.static_analysis(qr_data)
            
            # If URL, perform dynamic analysis
            if urlparse(qr_data).scheme:
                # Selenium-based analysis
                selenium_results = self.analyze_in_selenium(qr_data)
                results['dynamic_analysis'] = selenium_results
                
                # Network analysis in container
                network_results = self.network_analysis(container, qr_data)
                results['network_analysis'] = network_results
            
            # Determine final verdict
            risk_levels = {
                'HIGH': 3,
                'MEDIUM': 2,
                'LOW': 1,
                'UNKNOWN': 0
            }
            
            max_risk = max(
                risk_levels.get(results['static_analysis'].get('risk_level', 'UNKNOWN'), 0),
                risk_levels.get(results['dynamic_analysis'].get('risk_level', 'UNKNOWN'), 0),
                risk_levels.get(results['network_analysis'].get('risk_level', 'UNKNOWN'), 0)
            )
            
            results['final_verdict'] = {
                3: 'HIGH',
                2: 'MEDIUM',
                1: 'LOW',
                0: 'UNKNOWN'
            }[max_risk]
            
            return results
            
        finally:
            if container:
                try:
                    container.stop()
                except:
                    pass

    def static_analysis(self, qr_data):
        """Perform static analysis of QR code content"""
        results = {
            'content_type': None,
            'suspicious_patterns': [],
            'risk_level': 'LOW'
        }
        
        # Check for suspicious patterns
        suspicious_patterns = [
            (r'(?i)\.exe$', 'Executable file'),
            (r'(?i)javascript:', 'JavaScript protocol'),
            (r'(?i)data:', 'Data URL'),
            (r'(?i)file:', 'File protocol'),
            (r'(?i)\\x[0-9a-f]{2}', 'Hex encoding'),
            (r'(?i)base64', 'Base64 encoding')
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, qr_data):
                results['suspicious_patterns'].append(description)
                results['risk_level'] = 'HIGH'
        
        return results

    def network_analysis(self, container, url):
        """Analyze network behavior in sandbox"""
        results = {
            'connections': [],
            'dns_queries': [],
            'risk_level': 'LOW'
        }
        
        try:
            # Install and run tcpdump in container
            container.exec_run('apk add --no-cache tcpdump')
            container.exec_run('tcpdump -i any -w /sandbox/capture.pcap &')
            
            # Attempt connection (with curl)
            container.exec_run(f'curl -L -s {url}')
            time.sleep(2)  # Allow time for capture
            
            # Analyze capture
            capture_data = container.exec_run('tcpdump -r /sandbox/capture.pcap -n')
            
            # Process capture data
            for line in capture_data.output.decode().split('\n'):
                if 'IP' in line:
                    results['connections'].append(line)
                if 'DNS' in line:
                    results['dns_queries'].append(line)
            
            # Risk assessment
            if len(results['connections']) > 5:
                results['risk_level'] = 'MEDIUM'
            if len(results['dns_queries']) > 3:
                results['risk_level'] = 'HIGH'
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            results['risk_level'] = 'UNKNOWN'
            return results

def main():
    # Example usage
    analyzer = QRSandboxAnalyzer()
    
    # Decode QR code
    image = cv2.imread('images/1.png')
    decoded_objects = decode(image)
    
    if decoded_objects:
        qr_data = decoded_objects[0].data.decode('utf-8')
        results = analyzer.analyze_in_sandbox(qr_data)
        
        print(json.dumps(results, indent=2))
        
        if results['final_verdict'] == 'HIGH':
            print("WARNING: High risk QR code detected!")
        elif results['final_verdict'] == 'MEDIUM':
            print("CAUTION: Medium risk detected - proceed with caution")
        else:
            print("Low risk detected - likely safe")

if __name__ == "__main__":
    main()
