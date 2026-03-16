# PDF Compressor GUI

A cross-platform Python application that allows you to compress PDF files.

## Building a Standalone Executable

A helper script `build.py` is included to produce a single-file
executable using PyInstaller.  You only need to run the script on the
platform where you want to build.  Install PyInstaller first:

```bash
pip install pyinstaller
```

Then execute:

```bash
python build.py
```

The resulting binary will be placed in `dist/` (`PDFCompressor.exe` on
Windows, `PDFCompressor` on macOS/Linux).  You can also use the
convenience wrappers `build_windows.bat` or `build_unix.sh` if you
prefer.

Additional packaging (e.g. creating a `.app` bundle on macOS) is outside
the scope of this project but can be layered on top of the generated
binary.


## Features

- GUI built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Selectable compression level (`medium` or `extreme`)
- Option for selective compression of images above a pixel threshold
- Uses [PyMuPDF](https://pymupdf.readthedocs.io/) to manipulate PDF contents
- Leverages Pillow for image recompression

## Getting Started

1. Create and activate a virtual environment:
   ```bash
   python -m venv .\venv   # Windows example
   .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Use the GUI to choose a PDF, adjust compression options, and save the result.

## API Usage

This project also includes a REST API (`API.py`) built with FastAPI for programmatic PDF compression. The API converts images to grayscale and compresses them to reduce file size.

### Installing API Dependencies

Install the additional dependencies required for the API:

```bash
pip install -r requirements-API.txt
```

### Running the API Server

Start the API server using Uvicorn:

```bash
uvicorn API:app --reload
```

The server will run on `http://127.0.0.1:8000` by default. You can access the interactive API documentation at `http://127.0.0.1:8000/docs`.

### Using the API

#### Endpoint: POST /compress-pdf

Upload a PDF file to compress it.

- **Request**: Multipart form data with a file field named `file` (PDF only).
- **Response**: The compressed PDF as a downloadable file.

#### Example Usage with curl

```bash
curl -X POST "http://127.0.0.1:8000/compress-pdf" \
     -H "accept: application/pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@yourfile.pdf" \
     --output compressed_yourfile.pdf
```

#### Example Usage with Python

```python
import requests

url = "http://127.0.0.1:8000/compress-pdf"
files = {"file": open("yourfile.pdf", "rb")}
response = requests.post(url, files=files)

if response.status_code == 200:
    with open("compressed_yourfile.pdf", "wb") as f:
        f.write(response.content)
    print("PDF compressed successfully!")
else:
    print(f"Error: {response.status_code}")
```

The API processes images by converting them to grayscale and saving as JPEG with quality set to 20 for maximum compression.

## Notes

- The application currently compresses images within the PDF. It does not alter vector content.
- For extreme compression, image quality is set lower; results may be visibly degraded.
- Ensure the output filename ends with `.pdf`.

Feel free to extend or adapt the interface and compression logic as needed.
