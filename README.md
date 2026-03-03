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

## Notes

- The application currently compresses images within the PDF. It does not alter vector content.
- For extreme compression, image quality is set lower; results may be visibly degraded.
- Ensure the output filename ends with `.pdf`.

Feel free to extend or adapt the interface and compression logic as needed.
