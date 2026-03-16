import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from PIL import Image
import io

app = FastAPI(title="PDF Grayscale Compressor API")

@app.post("/compress-pdf")
async def compress_pdf(file: UploadFile = File(...)):
    # 1. Validate the file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    try:
        # 2. Read the uploaded file directly into memory
        input_pdf_bytes = await file.read()
        
        # Open the PDF from the memory stream instead of a file path
        doc = fitz.open(stream=input_pdf_bytes, filetype="pdf")
        
        # 3. Process the images (Grayscale ON)
        quality = 20  # JPEG quality level (0-100)

        for page_num in range(doc.page_count):
            page = doc[page_num]

            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                original_image_size = len(image_bytes)

                # Only process if it's a pixel image type that Pillow can handle
                if image_ext.lower() in ["png", "jpeg", "jpg", "ppm", "bmp", "gif", "tiff"]:
                    is_png = image_ext.lower() == "png"
                    
                    print(f"Page {page_num+1}, Image {img_index+1} (xref {xref}): Original size {original_image_size / (1024*1024):.2f} MB. Compressing...")
                    img_obj = Image.open(io.BytesIO(image_bytes))

                    # Attempt to reconstruct alpha from PDF soft-mask (smask) if present
                    # page.get_images(full=True) returns a tuple where index 1 is the smask xref
                    smask_xref = None
                    try:
                        smask_xref = img[1] if len(img) > 1 else None
                    except Exception:
                        smask_xref = None

                    if smask_xref and isinstance(smask_xref, int) and smask_xref > 0:
                        try:
                            smask_info = doc.extract_image(smask_xref)
                            smask_bytes = smask_info.get("image")
                            if smask_bytes:
                                mask = Image.open(io.BytesIO(smask_bytes)).convert("L")
                                # ensure base image is RGBA and attach mask as alpha
                                base_rgba = img_obj.convert("RGBA")
                                base_rgba.putalpha(mask)
                                img_obj = base_rgba
                        except Exception as e:
                            # if anything goes wrong, fall back to the extracted image
                            print(f"    -> smask reconstruction failed: {e}")
                            pass

                    # apply greyscale
                    # Greyscale conversion with proper transparency handling
                    if "A" in img_obj.getbands():
                        # Image has alpha channel - use proper alpha compositing
                        # Only transparent pixels (alpha=0) become white background
                        rgba_img = img_obj.convert("RGBA") if img_obj.mode != "RGBA" else img_obj
                        white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
                        # Alpha composite properly respects the alpha channel
                        composited = Image.alpha_composite(white_bg, rgba_img)
                        # Convert to greyscale
                        img_obj = composited.convert("L").convert("RGB")
                    else:
                        # No alpha channel (already flattened in PDF)
                        # Just greyscale as-is - we can't recover lost transparency
                        img_obj = img_obj.convert("L").convert("RGB")

                    # Optional: Downsample if image is massive (e.g., > 2000px)
                    if max(img_obj.size) > 2000:
                        img_obj.thumbnail((1600, 1600))

                    img_buffer = io.BytesIO()

                    # converting to JPEG will drop alpha/transparency
                    print(f"    -> saving as JPEG (quality={quality})")
                    img_obj.convert("RGB").save(img_buffer, format="JPEG", quality=quality, optimize=True)
                    
                    page.replace_image(xref, stream=img_buffer.getvalue())
                else:
                    print(f"Page {page_num+1}, Image {img_index+1} (xref {xref}): Skipping unsupported image format '{image_ext}'.")

        # Save with garbage collection to remove the old, heavy image data
        # garbage=4: cleans out unused objects
        # deflate=True: compresses streams
        # clean=True: This parameter is crucial for font optimization and other cleanup tasks
        # 4. Save the optimized PDF to a new memory buffer
        output_pdf_buffer = io.BytesIO()
        doc.save(output_pdf_buffer, garbage=4, deflate=True, clean=True)
        doc.close()
        
        # 5. Return the compressed PDF as a direct HTTP response
        return Response(
            content=output_pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="compressed_{file.filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during compression: {str(e)}")