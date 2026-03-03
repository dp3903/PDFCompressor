import io
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import fitz  # PyMuPDF
from PIL import Image


class PDFCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Compressor")
        self.geometry("700x700")
        self.resizable(True, True)
        
        # Set app appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.pdf_path = tk.StringVar()
        self.compression_level = tk.StringVar(value="medium")
        self.selective = tk.BooleanVar(value=False)
        self.threshold = tk.DoubleVar(value=2.0)
        self.convert_png_to_jpg = tk.BooleanVar(value=False)
        self.greyscale = tk.BooleanVar(value=False)
        # new option: optimize images for OCR (binarize / high contrast)
        self.ocr_optimize = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=30, pady=30, fill="both", expand=True)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="PDF Compressor",
            font=("Helvetica", 28, "bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Reduce your PDF file size with flexible compression options",
            font=("Helvetica", 12),
            text_color="#a0a0a0"
        )
        subtitle_label.pack(pady=(0, 20))

        # File Selection Section
        file_section = ctk.CTkFrame(main_frame, corner_radius=10)
        file_section.pack(fill="x", pady=(0, 20))

        file_label = ctk.CTkLabel(
            file_section,
            text="📄 Select PDF File",
            font=("Helvetica", 14, "bold"),
            text_color="#ffffff"
        )
        file_label.pack(anchor="w", padx=15, pady=(10, 5))

        file_input_frame = ctk.CTkFrame(file_section, fg_color="transparent")
        file_input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.pdf_entry = ctk.CTkEntry(
            file_input_frame,
            textvariable=self.pdf_path,
            placeholder_text="No file selected",
            state="readonly"
        )
        self.pdf_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            file_input_frame,
            text="Browse",
            command=self.browse_pdf,
            width=100,
            font=("Helvetica", 12, "bold")
        )
        self.browse_btn.pack(side="right")

        # File size info label
        self.file_size_label = ctk.CTkLabel(
            file_section,
            text="",
            font=("Helvetica", 10),
            text_color="#a0a0a0"
        )
        self.file_size_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Compression Settings Section with Scrollbar
        settings_container = ctk.CTkFrame(main_frame, corner_radius=10)
        settings_container.pack(fill="both", expand=True, pady=(0, 20))

        # Create canvas and scrollbar for settings
        settings_canvas = tk.Canvas(
            settings_container,
            bg="#212121",
            highlightthickness=0
        )
        scrollbar = ctk.CTkScrollbar(settings_container, command=settings_canvas.yview)
        scrollable_settings_frame = ctk.CTkFrame(settings_canvas, fg_color="#212121")

        # Bind the scrollable frame to update the scroll region
        scrollable_settings_frame.bind(
            "<Configure>",
            lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        )

        # Create window in canvas
        settings_canvas.create_window((0, 0), window=scrollable_settings_frame, anchor="nw")
        settings_canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        settings_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        settings_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        settings_label = ctk.CTkLabel(
            scrollable_settings_frame,
            text="⚙️ Compression Settings",
            font=("Helvetica", 14, "bold"),
            text_color="#ffffff"
        )
        settings_label.pack(anchor="w", padx=15, pady=(10, 15))

        # Compression Level
        level_frame = ctk.CTkFrame(scrollable_settings_frame, fg_color="transparent")
        level_frame.pack(fill="x", padx=15, pady=(0, 15))

        level_label = ctk.CTkLabel(
            level_frame,
            text="Compression Level:",
            font=("Helvetica", 12),
            text_color="#ffffff"
        )
        level_label.pack(side="left")

        compression_menu = ctk.CTkOptionMenu(
            level_frame,
            values=["medium", "extreme"],
            variable=self.compression_level,
            font=("Helvetica", 11)
        )
        compression_menu.pack(side="right", fill="x", padx=(10, 0), expand=True)

        # Info text for compression levels
        level_info = ctk.CTkLabel(
            scrollable_settings_frame,
            text="Medium: ~50% quality | Extreme: ~20% quality",
            font=("Helvetica", 10),
            text_color="#707070"
        )
        level_info.pack(anchor="w", padx=15, pady=(0, 15))

        # Selective Compression
        self.selective_check = ctk.CTkCheckBox(
            scrollable_settings_frame,
            text="Enable Selective Compression (Only compress images larger than threshold)",
            variable=self.selective,
            command=self._toggle_threshold_entry,
            font=("Helvetica", 11),
            text_color="#ffffff"
        )
        self.selective_check.pack(anchor="w", padx=15, pady=(0, 8))

        # Threshold Input (appears immediately after selective checkbox)
        self.threshold_frame = ctk.CTkFrame(scrollable_settings_frame, fg_color="transparent")

        threshold_label = ctk.CTkLabel(
            self.threshold_frame,
            text="Size Threshold:",
            font=("Helvetica", 12),
            text_color="#ffffff"
        )
        threshold_label.pack(side="left")

        self.threshold_entry = ctk.CTkEntry(
            self.threshold_frame,
            textvariable=self.threshold,
            placeholder_text="2.0",
            state="normal",
            width=80
        )
        self.threshold_entry.pack(side="left", padx=(10, 5))

        threshold_unit = ctk.CTkLabel(
            self.threshold_frame,
            text="MB",
            font=("Helvetica", 12),
            text_color="#a0a0a0"
        )
        threshold_unit.pack(side="left")

        # Threshold info (appears after threshold controls)
        self.threshold_info_label = ctk.CTkLabel(
            scrollable_settings_frame,
            text="Keep images smaller than this threshold uncompressed",
            font=("Helvetica", 10),
            text_color="#707070"
        )

        # Store reference to scrollable_settings_frame for later use
        self.scrollable_settings_frame = scrollable_settings_frame

        # Option: Convert PNG to JPG
        self.png_convert_check = ctk.CTkCheckBox(
            scrollable_settings_frame,
            text="Convert PNG images to JPG (smaller, may lose transparency)",
            variable=self.convert_png_to_jpg,
            command=self._toggle_png_conversion,
            font=("Helvetica", 11),
            text_color="#ffffff"
        )
        self.png_convert_check.pack(anchor="w", padx=15, pady=(8, 4))

        # PNG hint (appears immediately after PNG checkbox)
        self.png_hint = ctk.CTkLabel(
            scrollable_settings_frame,
            text=("Converting PNG → JPG will NOT preserve transparency and may reduce the sharpness "
                  "of text or thin shapes inside PNGs. Use when images are photographic or when "
                  "file size is more important than exact visual fidelity. Avoid for UI/graphics or "
                  "images with important alpha channels."),
            font=("Helvetica", 10),
            text_color="#ffcc66",
            wraplength=520,
            justify="left"
        )
        self.png_hint.pack_forget()

        # Option: Convert images to greyscale
        self.greyscale_check = ctk.CTkCheckBox(
            scrollable_settings_frame,
            text="Convert all images to greyscale",
            variable=self.greyscale,
            command=self._toggle_greyscale_hint,
            font=("Helvetica", 11),
            text_color="#ffffff"
        )
        self.greyscale_check.pack(anchor="w", padx=15, pady=(8, 4))

        # Greyscale hint (appears immediately after greyscale checkbox)
        self.grey_hint = ctk.CTkLabel(
            scrollable_settings_frame,
            text=("Applying greyscale will remove all color information. "
                  "If used together with PNG→JPG conversion the PNG will first "
                  "be turned grey and then saved as JPEG (alpha will be dropped if JPG)."),
            font=("Helvetica", 10),
            text_color="#ffcc66",
            wraplength=520,
            justify="left"
        )
        self.grey_hint.pack_forget()

        # Option: Optimize images for OCR
        self.ocr_check = ctk.CTkCheckBox(
            scrollable_settings_frame,
            text="Optimize images for OCR",
            variable=self.ocr_optimize,
            command=self._toggle_ocr_hint,
            font=("Helvetica", 11),
            text_color="#ffffff"
        )
        self.ocr_check.pack(anchor="w", padx=15, pady=(8, 4))

        # OCR hint (appears immediately after OCR checkbox)
        self.ocr_hint = ctk.CTkLabel(
            scrollable_settings_frame,
            text=("Converts images to high-contrast black and white to improve "
                  "OCR accuracy. This may increase blockiness and can enlarge "
                  "some images; use for scanned documents only."),
            font=("Helvetica", 10),
            text_color="#ffcc66",
            wraplength=520,
            justify="left"
        )
        self.ocr_hint.pack_forget()

        # Compress Button
        self.compress_btn = ctk.CTkButton(
            main_frame,
            text="Compress PDF",
            command=self.compress,
            height=50,
            font=("Helvetica", 14, "bold"),
            fg_color="#0084d6",
            hover_color="#0066a1"
        )
        self.compress_btn.pack(fill="x", pady=(20, 0))

    def _toggle_threshold_entry(self):
        if self.selective.get():
            # Pack right after the selective checkbox using after= parameter
            self.threshold_frame.pack(fill="x", padx=15, pady=(0, 5), after=self.selective_check)
            self.threshold_info_label.pack(anchor="w", padx=15, pady=(0, 15), after=self.threshold_frame)
            self.threshold_entry.configure(state="normal")
        else:
            self.threshold_frame.pack_forget()
            self.threshold_info_label.pack_forget()
            self.threshold_entry.configure(state="disabled")

    def _toggle_png_conversion(self):
        """Show or hide the PNG->JPG hint when the checkbox is toggled."""
        try:
            if self.convert_png_to_jpg.get():
                self.png_hint.pack(anchor="w", padx=15, pady=(4, 8), after=self.png_convert_check)
            else:
                self.png_hint.pack_forget()
        except Exception:
            # if the widget isn't available for some reason, ignore silently
            pass

    def _toggle_greyscale_hint(self):
        """Show or hide the greyscale hint when the checkbox is toggled."""
        try:
            if self.greyscale.get():
                self.grey_hint.pack(anchor="w", padx=15, pady=(4, 8), after=self.greyscale_check)
            else:
                self.grey_hint.pack_forget()
        except Exception:
            pass

    def _toggle_ocr_hint(self):
        """Show or hide the OCR hint when the checkbox is toggled."""
        try:
            if self.ocr_optimize.get():
                self.ocr_hint.pack(anchor="w", padx=15, pady=(4, 8), after=self.ocr_check)
            else:
                self.ocr_hint.pack_forget()
        except Exception:
            pass

    def browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_path.set(path)
            # Display file size
            try:
                file_size = os.path.getsize(path)
                size_mb = file_size / (1024 * 1024)
                self.file_size_label.configure(text=f"File size: {size_mb:.2f} MB")
            except Exception:
                self.file_size_label.configure(text="")

    def compress(self):
        input_path = self.pdf_path.get()
        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid PDF file.")
            return

        level = self.compression_level.get()
        selective = self.selective.get()
        threshold = self.threshold.get()
        greyscale = self.greyscale.get()
        ocr_optimize = self.ocr_optimize.get()

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not output_path:
            return

        size_threshold_mb = float(threshold) if selective else 1.0

        # disable UI while working
        self._set_widgets_state("disabled")
        # show progress indicator
        self._show_progress_window()

        # run compression in background thread so UI remains responsive
        convert_png = self.convert_png_to_jpg.get()
        thread = threading.Thread(
            target=self._background_compress,
            args=(input_path, output_path, level, selective, size_threshold_mb, convert_png, greyscale, ocr_optimize),
            daemon=True
        )
        thread.start()

    def _background_compress(self, input_path, output_path, level, selective, size_threshold_mb, convert_png, greyscale, ocr_optimize):
        try:
            self._compress_pdf(input_path, output_path, level, selective, size_threshold_mb, convert_png, greyscale, ocr_optimize)
            # Calculate size reduction
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            reduction_bytes = original_size - compressed_size
            reduction_percent = (reduction_bytes / original_size * 100) if original_size > 0 else 0
            original_mb = original_size / (1024 * 1024)
            compressed_mb = compressed_size / (1024 * 1024)
            
            success_msg = f"Compression complete!\n\nOriginal: {original_mb:.2f} MB\nCompressed: {compressed_mb:.2f} MB\nReduction: {reduction_percent:.1f}%\n\nSaved to:\n{output_path}"
            # show success message on main thread
            self.after(0, lambda: messagebox.showinfo("Success", success_msg))
        except Exception as e:
            # log full traceback so user can copy if needed
            import traceback
            traceback.print_exc()
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            # close progress window and re-enable controls
            self.after(0, self._end_progress)

    def _set_widgets_state(self, state):
        # simple state toggler for main widgets to prevent interaction during compression
        # disable entry fields and buttons
        for widget in [self.pdf_entry, self.browse_btn, self.compress_btn]:
            try:
                widget.configure(state=state)
            except Exception:
                pass

    def _show_progress_window(self):
        # create window if not already exist
        self.progress_win = ctk.CTkToplevel(self)
        self.progress_win.title("Compressing...")
        self.progress_win.geometry("300x100")
        self.progress_win.transient(self)
        self.progress_win.grab_set()
        # disable close button
        self.progress_win.protocol("WM_DELETE_WINDOW", lambda: None)

        label = ctk.CTkLabel(self.progress_win, text="Compression in progress...", font=("Helvetica", 12))
        label.pack(pady=(20, 10))

        self.progress_bar = ctk.CTkProgressBar(self.progress_win, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=20)
        # start without interval argument, CustomTkinter handles internally
        self.progress_bar.start()

    def _end_progress(self):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.stop()
        if hasattr(self, 'progress_win'):
            self.progress_win.destroy()
        self._set_widgets_state("normal")


    def _compress_pdf(self, in_path, out_path, level, selective, size_threshold_mb=1.0, convert_png_to_jpg=False, greyscale=False, ocr_optimize=False):
        doc = fitz.open(in_path)
        quality = 50 if level == "medium" else 20
        threshold_bytes = size_threshold_mb * 1024 * 1024

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
                    if selective and original_image_size <= threshold_bytes:
                        # image is below the size threshold so we skip any processing entirely
                        # simply continue to the next image and leave the embedded data untouched.
                        print(f"Page {page_num+1}, Image {img_index+1} (xref {xref}): Original size {original_image_size / (1024*1024):.2f} MB <= {size_threshold_mb:.2f} MB. Keeping uncompressed.")
                        continue
                    else:
                        is_png = image_ext.lower() == "png"
                        # if it's a PNG and user hasn't asked to convert, greyscale or OCR-optimize,
                        # leave it untouched to preserve transparency
                        if is_png and not convert_png_to_jpg and not greyscale and not ocr_optimize:
                            # do nothing, leave original image unmodified to preserve transparency
                            print(f"Page {page_num+1}, Image {img_index+1} (xref {xref}): PNG left intact (conversion disabled and no image filters).")
                            continue
                        else:
                            print(f"Page {page_num+1}, Image {img_index+1} (xref {xref}): Original size {original_image_size / (1024*1024):.2f} MB > {size_threshold_mb:.2f} MB. Compressing... (png->jpg={convert_png_to_jpg}, greyscale={greyscale}, ocr={ocr_optimize})")
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
                                        if ocr_optimize:
                                            print(f"    -> reconstructed RGBA from smask (xref {smask_xref})")
                                except Exception as e:
                                    # if anything goes wrong, fall back to the extracted image
                                    if ocr_optimize:
                                        print(f"    -> smask reconstruction failed: {e}")
                                    pass

                            # apply greyscale if requested
                            if greyscale:
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

                            # OCR optimization: convert to high-contrast black/white
                            if ocr_optimize:
                                # if there is transparency left, composite over white
                                if "A" in img_obj.getbands():
                                    white_bg = Image.new("RGBA", img_obj.size, (255, 255, 255, 255))
                                    img_obj = Image.alpha_composite(white_bg, img_obj.convert("RGBA"))
                                # ensure grayscale first
                                gray = img_obj.convert("L")
                                # simple check for uniform color to catch "flattened to black" images
                                # these show up when the source PDF already lost transparency
                                colors = gray.getcolors(maxcolors=2)
                                if colors and len(colors) == 1:
                                    val = colors[0][1]
                                    if val == 0:
                                        print(f"    -> image already all-black after flattening; PDF may have lost transparency; skipping threshold")
                                    elif val == 255:
                                        print(f"    -> image already all-white; skipping threshold")
                                    # nothing to do, keep the grayscale
                                    img_obj = gray.convert("RGB")
                                else:
                                    # simple threshold at mid-point
                                    print(f"    -> OCR optimization: thresholding image")
                                    img_obj = gray.point(lambda x: 0 if x < 128 else 255, '1')
                                    # back to RGB so saving logic remains consistent
                                    img_obj = img_obj.convert("RGB")

                            img_buffer = io.BytesIO()

                            # determine output format preferences
                            want_jpeg = False
                            if is_png:
                                # user may have opted into PNG->JPG
                                want_jpeg = convert_png_to_jpg
                                # when greyscale is applied and no alpha remains, it's safe and beneficial to convert
                                if greyscale and "A" not in img_obj.getbands():
                                    want_jpeg = True
                            else:
                                # non-PNGs will always be saved as JPEG for compression
                                want_jpeg = True

                            if want_jpeg:
                                # converting to JPEG will drop alpha/transparency
                                print(f"    -> saving as JPEG (quality={quality})")
                                img_obj.convert("RGB").save(img_buffer, format="JPEG", quality=quality, optimize=True)
                            else:
                                # PNG output path (alpha still exists or user wants PNG)
                                # for greyscale PNGs we can quantize to reduce size
                                if greyscale:
                                    try:
                                        img_obj = img_obj.convert("P", palette=Image.ADAPTIVE)
                                    except Exception:
                                        pass
                                print(f"    -> saving as PNG (optimize)")
                                try:
                                    img_obj.save(img_buffer, format="PNG", optimize=True)
                                except Exception:
                                    img_obj.convert("RGBA").save(img_buffer, format="PNG", optimize=True)

                            page.replace_image(xref, stream=img_buffer.getvalue())
                else:
                    print(f"Page {page_num+1}, Image {img_index+1} (xref {xref}): Skipping unsupported image format '{image_ext}'.")

        # Save with garbage collection to remove the old, heavy image data
        # garbage=4: cleans out unused objects
        # deflate=True: compresses streams
        # clean=True: This parameter is crucial for font optimization and other cleanup tasks
        doc.save(out_path, garbage=4, deflate=True, clean=True)
        doc.close()

if __name__ == "__main__":
    app = PDFCompressorApp()
    app.mainloop()
