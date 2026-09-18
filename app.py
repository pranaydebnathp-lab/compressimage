import io
from pathlib import Path

import streamlit as st
from PIL import Image
import pymupdf


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart File Size Optimizer",
    page_icon="🗜️",
    layout="wide"
)


# =========================================================
# FUNCTIONS
# =========================================================

def format_size(size):
    """Convert bytes into readable format."""

    if size < 1024:
        return f"{size:.2f} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"

    return f"{size / (1024 ** 3):.2f} GB"


def calculate_reduction(original, compressed):
    """Calculate percentage size reduction."""

    if original == 0:
        return 0

    return max(
        0,
        ((original - compressed) / original) * 100
    )


# =========================================================
# IMAGE COMPRESSION
# =========================================================

def compress_image(data, quality=70, max_dimension=None):

    image = Image.open(
        io.BytesIO(data)
    )

    image.load()

    # JPEG does not support transparency.
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    if image.mode == "L":
        image = image.convert("RGB")

    # Resize if requested
    if max_dimension:

        image.thumbnail(
            (max_dimension, max_dimension),
            Image.Resampling.LANCZOS
        )

    output = io.BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=int(quality),
        optimize=True,
        progressive=True
    )

    return output.getvalue()


# =========================================================
# TARGET SIZE IMAGE COMPRESSION
# =========================================================

def compress_to_target(data, target_bytes):

    minimum_quality = 25

    # First try quality-based compression
    for quality in range(
        90,
        minimum_quality - 1,
        -5
    ):

        result = compress_image(
            data,
            quality=quality
        )

        if len(result) <= target_bytes:

            return result, quality


    # If still too large, resize image
    image = Image.open(
        io.BytesIO(data)
    )

    image.load()

    max_dimension = max(
        image.size
    )


    while max_dimension >= 400:

        result = compress_image(
            data,
            quality=minimum_quality,
            max_dimension=max_dimension
        )

        if len(result) <= target_bytes:

            return result, minimum_quality

        max_dimension = int(
            max_dimension * 0.85
        )


    # Final fallback
    result = compress_image(
        data,
        quality=minimum_quality,
        max_dimension=400
    )

    return result, minimum_quality


# =========================================================
# PDF COMPRESSION
# =========================================================

def compress_pdf(
    data,
    dpi=120,
    quality=60
):

    pdf = pymupdf.open(
        stream=data,
        filetype="pdf"
    )

    try:

        pdf.rewrite_images(
            dpi_threshold=max(
                dpi + 40,
                160
            ),

            dpi_target=dpi,

            quality=quality,

            lossy=True,
            lossless=True,
            bitonal=True,
            color=True,
            gray=True
        )

        result = pdf.tobytes(
            garbage=4,
            deflate=True
        )

        return result

    finally:

        pdf.close()


# =========================================================
# TITLE
# =========================================================

st.title(
    "🗜️ Smart File Size Optimizer"
)

st.write(
    "### Image & PDF Compression Using Python"
)

st.caption(
    "B.Tech CSE Mini Project"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "⚙️ Settings"
)


compression_mode = st.sidebar.radio(
    "Compression Mode",
    [
        "Manual Quality",
        "Target File Size"
    ]
)


# Image settings
if compression_mode == "Manual Quality":

    image_quality = st.sidebar.slider(
        "Image Quality",
        20,
        95,
        70
    )

else:

    target_size = st.sidebar.number_input(
        "Target Size (KB)",
        min_value=50,
        max_value=20000,
        value=500,
        step=50
    )


# PDF settings
st.sidebar.subheader(
    "PDF Settings"
)


pdf_dpi = st.sidebar.slider(
    "PDF DPI",
    72,
    200,
    120
)


pdf_quality = st.sidebar.slider(
    "PDF Image Quality",
    20,
    90,
    60
)


# =========================================================
# FILE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "📤 Upload Image or PDF",

    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "pdf"
    ],

    max_upload_size=200
)


# =========================================================
# MAIN PROCESS
# =========================================================

if uploaded_file is not None:

    file_data = uploaded_file.getvalue()

    original_size = len(
        file_data
    )

    extension = Path(
        uploaded_file.name
    ).suffix.lower()


    st.divider()

    # =====================================================
    # FILE INFORMATION
    # =====================================================

    col1, col2 = st.columns(2)


    with col1:

        st.subheader(
            "📁 Original File"
        )

        st.write(
            f"**Name:** {uploaded_file.name}"
        )

        st.write(
            f"**Type:** {extension.upper()}"
        )

        st.metric(
            "Original Size",
            format_size(original_size)
        )


    # =====================================================
    # ORIGINAL IMAGE PREVIEW
    # =====================================================

    if extension != ".pdf":

        try:

            original_image = Image.open(
                io.BytesIO(file_data)
            )

            with col1:

                st.image(
                    original_image,
                    caption="Original Image",
                    use_container_width=True
                )

        except Exception:

            st.warning(
                "Unable to preview image."
            )

    else:

        with col1:

            st.info(
                "📄 PDF file detected."
            )


    # =====================================================
    # COMPRESS FILE
    # =====================================================

    try:

        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        if extension == ".pdf":

            compressed_data = compress_pdf(
                file_data,
                dpi=pdf_dpi,
                quality=pdf_quality
            )

            output_name = (
                Path(uploaded_file.name).stem
                + "_compressed.pdf"
            )

            mime = "application/pdf"


        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        else:

            if compression_mode == "Target File Size":

                target_bytes = (
                    target_size * 1024
                )

                compressed_data, used_quality = (
                    compress_to_target(
                        file_data,
                        target_bytes
                    )
                )

                st.info(
                    f"🤖 Automatic mode selected "
                    f"quality ≈ {used_quality}"
                )

            else:

                compressed_data = compress_image(
                    file_data,
                    quality=image_quality
                )


            output_name = (
                Path(uploaded_file.name).stem
                + "_compressed.jpg"
            )

            mime = "image/jpeg"


        # =================================================
        # CALCULATE RESULTS
        # =================================================

        compressed_size = len(
            compressed_data
        )

        reduction = calculate_reduction(
            original_size,
            compressed_size
        )

        saved_size = (
            original_size
            - compressed_size
        )


        # =================================================
        # RESULT
        # =================================================

        with col2:

            st.subheader(
                "📦 Compressed File"
            )

            st.metric(
                "Compressed Size",
                format_size(compressed_size)
            )

            st.metric(
                "Reduction",
                f"{reduction:.2f}%"
            )

            if saved_size > 0:

                st.success(
                    f"💾 Saved "
                    f"{format_size(saved_size)}"
                )

            else:

                st.warning(
                    "The compressed file is "
                    "not smaller than the original."
                )


        # =================================================
        # COMPRESSED IMAGE PREVIEW
        # =================================================

        if extension != ".pdf":

            try:

                compressed_image = Image.open(
                    io.BytesIO(compressed_data)
                )

                with col2:

                    st.image(
                        compressed_image,
                        caption="Compressed Image",
                        use_container_width=True
                    )

            except Exception:

                pass


        # =================================================
        # COMPARISON
        # =================================================

        st.divider()

        st.subheader(
            "📊 Compression Comparison"
        )


        comparison1, comparison2, comparison3 = (
            st.columns(3)
        )


        with comparison1:

            st.metric(
                "Before",
                format_size(original_size)
            )


        with comparison2:

            st.metric(
                "After",
                format_size(compressed_size)
            )


        with comparison3:

            st.metric(
                "Space Saved",
                f"{reduction:.2f}%"
            )


        # =================================================
        # DOWNLOAD
        # =================================================

        st.divider()

        st.subheader(
            "⬇️ Download"
        )


        st.download_button(
            label="⬇️ Download Compressed File",

            data=compressed_data,

            file_name=output_name,

            mime=mime,

            width="stretch"
        )


    except Exception as error:

        st.error(
            "❌ Compression failed"
        )

        st.exception(error)


# =========================================================
# INFORMATION
# =========================================================

else:

    st.info(
        "👆 Upload an image or PDF to start compression."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Smart File Size Optimizer | "
    "B.Tech CSE Python Mini Project"
)