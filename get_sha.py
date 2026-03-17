import zipfile
import hashlib
import sys
import os

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization.pkcs7 import load_der_pkcs7_certificates
except ImportError:
    print("Error: cryptography library not installed.")
    sys.exit(1)

def extract_cert_fingerprints(apk_path):
    if not os.path.exists(apk_path):
        print(f"Error: APK not found at {apk_path}")
        return

    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            # Android v1 (JAR signing) stores certificates in META-INF/*.RSA, *.DSA, *.EC
            cert_files = [f for f in z.namelist() if f.startswith('META-INF/') and f.endswith(('.RSA', '.DSA', '.EC'))]
            
            if not cert_files:
                print("No v1 signature found in the APK. It might only have a v2/v3 signature.")
                return
            
            for cert_file in cert_files:
                print(f"Found certificate file: {cert_file}")
                cert_data = z.read(cert_file)
                
                # Load the PKCS7 certificates enclosed
                certs = load_der_pkcs7_certificates(cert_data)
                
                for i, cert in enumerate(certs):
                    der = cert.public_bytes(encoding=serialization.Encoding.DER)
                    
                    sha1 = hashlib.sha1(der).hexdigest().upper()
                    sha256 = hashlib.sha256(der).hexdigest().upper()
                    
                    sha1_fmt = ':'.join(sha1[i:i+2] for i in range(0, 40, 2))
                    sha256_fmt = ':'.join(sha256[i:i+2] for i in range(0, 64, 2))
                    
                    print(f"\n--- Certificate {i+1} ---")
                    print(f"SHA1:   {sha1_fmt}")
                    print(f"SHA256: {sha256_fmt}")
                
    except Exception as e:
        print(f"Failed to extract fingerprints: {e}")

if __name__ == "__main__":
    apk1 = r"c:\FitnessApp\FitCrave\build\app\outputs\flutter-apk\app-debug.apk"
    apk2 = r"c:\FitnessApp\FitCrave\build\app\outputs\flutter-apk\app-release.apk"
    
    print("=================== DEBUG APK ===================")
    extract_cert_fingerprints(apk1)
    print("\n=================== RELEASE APK =================")
    extract_cert_fingerprints(apk2)
