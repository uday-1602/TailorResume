import os
import requests
import tarfile
from tenacity import retry, stop_after_attempt, wait_exponential

def compile_tex():
    tex_filename = "tailored_resume.tex"
    tar_filename = "payload.tar.bz2"
    pdf_filename = "tailored_resume.pdf"

    if not os.path.exists(tex_filename):
        print(f"Error: {tex_filename} not found!")
        return

    print(f"\n[COMPILER] Packing {tex_filename} into compressed stream...")
    with tarfile.open(tar_filename, "w:bz2") as tar:
        tar.add(tex_filename)

    print("[COMPILER] Sending payload to cloud compiler API (https://latexonline.cc)...")
    api_url = f"https://latexonline.cc/data?target={tex_filename}&command=pdflatex"

    # We do not use tenacity retry on HTTP 400 since that indicates a code error, not a network/server error.
    # We will raise directly if it is a 400 Client Error.
    def _compile_pdf():
        with open(tar_filename, "rb") as packed_file:
            resp = requests.post(api_url, files={"file": packed_file}, timeout=45)
            if resp.status_code == 400:
                print("\n[COMPILER ERROR LOGS FROM API]:")
                print(resp.text)
                resp.raise_for_status()
            resp.raise_for_status()
            return resp

    try:
        response = _compile_pdf()
        with open(pdf_filename, "wb") as pdf_file:
            pdf_file.write(response.content)
        print(f"\nSUCCESS: '{pdf_filename}' has been successfully compiled and written!")
    except Exception as e:
        print(f"\nCloud compilation failed: {str(e)}")
    finally:
        if os.path.exists(tar_filename):
            os.remove(tar_filename)

if __name__ == "__main__":
    compile_tex()
