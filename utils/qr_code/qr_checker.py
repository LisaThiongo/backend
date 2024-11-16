import cv2
from pyzbar.pyzbar import decode
import urllib.parse
import re
import requests
import tldextract
import time
import idna
import unidecode
from PIL import Image
import asyncio

# Known URL shortener domains
url_shorteners = {
    'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'tiny.cc',
    'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'bitly.com',
    'rebrand.ly', 'cutt.ly', 'shorturl.at', 'tiny.one',
    'rotf.lol', 'shorturl.asia'
}

# Common malicious patterns
suspicious_patterns = [
    r'(?i)\.exe$',  # Executable files
    r'(?i)\.bat$',  # Batch files
    r'(?i)\.ps1$',  # PowerShell scripts
    r'(?i)phish',   # Potential phishing
    r'(?i)login',   # Login-related (potential phishing)
    r'(?i)password',# Password-related
    r'(?i)bank',    # Banking-related
    r'(?i)wallet',  # Crypto wallet related
    r'data:text/html', # Data URLs
    r'javascript:', # JavaScript protocol
]

# Known safe domains
safe_domains = {
    'google.com',
    'microsoft.com',
    'apple.com',
    'amazon.com',
    'github.com',
    'facebook.com',
    'instagram.com',
    'twitter.com',
    'linkedin.com',
    'pinterest.com',
    'reddit.com',
    'tiktok.com',
    'snapchat.com',
    'youtube.com',
    'whatsapp.com',
    'bbc.com',
    'cnn.com',
    'nytimes.com',
    'theguardian.com',
    'reuters.com',
    'bloomberg.com',
    'aljazeera.com',
    'forbes.com',
    'npr.org',
    'washingtonpost.com',
    'wikipedia.org',
    'netflix.com',
    'spotify.com',
    'stackoverflow.com',
    'dropbox.com'
}


# Request headers to mimic a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Homoglyph map
homoglyph_map = {
    'a': ['а'], 'b': ['Ь', 'б'], 'c': ['с'], 'e': ['е'],
    'h': ['н'], 'i': ['і', '1'], 'l': ['і', '1'], 'o': ['о'],
    'p': ['р'], 's': ['ѕ'], 't': ['т'], 'x': ['х'], 'y': ['у'],
    'z': ['ѕ']
}

async def is_shortlink(url):
    """Check if URL is from a known URL shortener"""
    try:
        domain = tldextract.extract(url).registered_domain
        return domain in url_shorteners
    except Exception:
        return False

async def safely_resolve_url(url, max_redirects=5):
    """Safely resolve shortened URL without actually visiting the final webpage"""
    redirect_chain = []
    current_url = url
    
    try:
        for _ in range(max_redirects):
            redirect_chain.append(current_url)
            head_response = requests.head(current_url, headers=headers, allow_redirects=False, timeout=5)
            
            if head_response.status_code not in [301, 302, 303, 307, 308]:
                break
            
            current_url = head_response.headers.get('location')
            
            if current_url and not current_url.startswith(('http://', 'https://')):
                current_url = urllib.parse.urljoin(url, current_url)
            
            if not current_url:
                break
            
            await asyncio.sleep(0.1)  # Use asyncio.sleep for async functions
        
        return current_url, redirect_chain, None
    
    except requests.exceptions.RequestException as e:
        return None, redirect_chain, f"Error resolving URL: {str(e)}"

async def contains_homoglyphs(url):
    """Check for homoglyphs or visually similar characters."""
    normalized_url = unidecode.unidecode(url)
    for char, homoglyphs in homoglyph_map.items():
        for homoglyph in homoglyphs:
            if homoglyph in url and homoglyph != char:
                return True
    return False

async def detect_homograph_attack(domain):
    """Check if domain contains characters that could be used in homograph attacks."""
    try:
        domain_unicode = idna.decode(domain)
    except idna.IDNAError:
        domain_unicode = domain
    
    return await contains_homoglyphs(domain_unicode)

async def analyze_content(content):
    """Analyze decoded content for security risks"""
    risks = []
    risk_level = "LOW"
    
    try:
        parsed = urllib.parse.urlparse(content)
        if parsed.scheme:
            if await is_shortlink(content):
                final_url, redirects, error = await safely_resolve_url(content)
                
                if error:
                    risks.append(f"Error resolving shortened URL: {error}")
                    risk_level = "HIGH"
                else:
                    redirect_risks = await analyze_redirect_chain(redirects)
                    risks.extend(redirect_risks)
                    
                    if redirect_risks:
                        risk_level = "HIGH"
                    
                    content = final_url
                    risks.append(f"URL redirect chain: {' -> '.join(redirects)}")
            
            domain_info = tldextract.extract(content)
            domain = f"{domain_info.domain}.{domain_info.suffix}"
            
            if await contains_homoglyphs(content):
                risks.append("URL contains visually similar characters (homoglyphs)")
                risk_level = max(risk_level, "MEDIUM")

            if domain not in safe_domains:
                risks.append(f"Unknown domain: {domain}")
                risk_level = max(risk_level, "MEDIUM")
            
            if await detect_homograph_attack(domain):
                risks.append(f"Suspicious homograph attack detected in domain: {domain}")
                risk_level = "HIGH"
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content):
                    risks.append(f"Suspicious pattern found: {pattern}")
                    risk_level = "HIGH"
            
            decoded_url = urllib.parse.unquote(content)
            if decoded_url != content:
                risks.append("URL contains encoded characters")
                risk_level = max(risk_level, "MEDIUM")
            
            if len(domain_info.subdomain.split('.')) > 3:
                risks.append("Suspicious number of subdomains")
                risk_level = "HIGH"
    
    except Exception as e:
        risks.append(f"Error analyzing URL: {str(e)}")
        risk_level = "UNKNOWN"
    

    result = [
        f"- Content of QR: {content}",
        f"- Risk Level: {risk_level}",
        f"- Is Malicious: {'Yes' if risk_level == 'HIGH' else 'No'}",
        f"- Recommendation: {'BLOCK' if risk_level == 'HIGH' else 'WARN' if risk_level == 'MEDIUM' else 'ALLOW'}",
    ]

    if risks:
        result.append("- Risks Detected:")
        for risk in risks:
            result.append(f"  - {risk}")

    return "\n".join(result)

async def analyze_redirect_chain(redirect_chain):
    """Analyze the redirect chain for suspicious patterns"""
    risks = []
    
    if len(redirect_chain) > 3:
        risks.append(f"Suspicious number of redirects: {len(redirect_chain)}")
    
    has_http = any(url.startswith('http://') for url in redirect_chain)
    has_https = any(url.startswith('https://') for url in redirect_chain)
    if has_http and has_https:
        risks.append("Mixed HTTP/HTTPS redirects detected")
    
    domains = [tldextract.extract(url).suffix for url in redirect_chain]
    if len(set(domains)) > 2:
        risks.append(f"Multiple country domains in redirect chain: {', '.join(set(domains))}")
    
    return risks

async def decode_qr(image: Image):
    """Decode QR code from image"""
    try:
        decoded_objects = decode(image)
        if not decoded_objects:
            return None, "No QR code found in image"
        return decoded_objects[0].data.decode('utf-8'), None
    except Exception as e:
        return None, f"Error decoding QR code: {str(e)}"

async def check_qr_safety(image: Image):
    """Main method to check QR code safety"""
    content, error = await decode_qr(image)
    if error:
        return {"error": error}
    
    return await analyze_content(content)

# Example usage
async def process_qr_scan(image: Image):
    result = await check_qr_safety(image)
    
    if result:
        return result
    else:
        return None

# Run with an event loop
# Example: asyncio.run(process_qr_scan(Image.open("path/to/qr/image.png")))
