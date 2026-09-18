
const fileType = document.getElementById("fileType");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");

const compressForm = document.getElementById("compressForm");
const loading = document.getElementById("loading");
const message = document.getElementById("message");

const result = document.getElementById("result");
const resultText = document.getElementById("resultText");
const downloadBtn = document.getElementById("downloadBtn");


// ==================================
// FILE TYPE CONFIGURATION
// ==================================

const allowedTypes = {
    image: [
        "image/jpeg",
        "image/png",
        "image/webp"
    ],
    pdf: [
        "application/pdf"
    ]
};


// ==================================
// UPDATE FILE INPUT
// ==================================

function updateFileInput() {

    if (fileType.value === "image") {

        fileInput.accept =
            "image/jpeg,image/png,image/webp";

    } else {

        fileInput.accept =
            "application/pdf";

    }

    fileInput.value = "";
    fileName.textContent = "No file selected";

    clearStatus();
}

fileType.addEventListener("change", updateFileInput);


// ==================================
// FILE SELECTION
// ==================================

fileInput.addEventListener("change", function () {

    const file = fileInput.files[0];

    if (!file) {
        fileName.textContent = "No file selected";
        return;
    }

    const selectedType = fileType.value;

    if (!allowedTypes[selectedType].includes(file.type)) {

        fileName.textContent = "Invalid file type selected.";
        fileInput.value = "";

        message.textContent =
            "Please choose a supported file.";

        return;
    }

    fileName.textContent =
        `${file.name} (${formatSize(file.size)})`;

    clearStatus();

});


// ==================================
// FORM SUBMISSION
// ==================================

compressForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    clearStatus();

    const file = fileInput.files[0];

    if (!file) {

        message.textContent =
            "Please select a file first.";

        return;
    }

    const selectedType = fileType.value;

    if (!allowedTypes[selectedType].includes(file.type)) {

        message.textContent =
            "Please choose a valid file type.";

        return;
    }

    const formData = new FormData();

    formData.append("file", file);
    formData.append("file_type", selectedType);
    formData.append(
        "quality",
        document.getElementById("quality").value
    );

    loading.classList.remove("hidden");

    const submitBtn =
        compressForm.querySelector("button[type='submit']");

    submitBtn.disabled = true;
    submitBtn.textContent = "Compressing...";

    try {

        const response = await fetch("/compress", {

            method: "POST",
            body: formData

        });

        let data;

        try {
            data = await response.json();
        } catch (error) {
            throw new Error("Invalid server response.");
        }

        if (!response.ok || !data.success) {

            throw new Error(
                data.error || "Compression failed."
            );

        }

        result.classList.remove("hidden");

        resultText.textContent =
            data.message || "Your file is ready.";

        downloadBtn.href = data.download_url;

        downloadBtn.setAttribute(
            "download",
            data.filename || "compressed-file"
        );

    } catch (error) {

        message.textContent =
            error.message || "Something went wrong.";

    } finally {

        loading.classList.add("hidden");

        submitBtn.disabled = false;
        submitBtn.textContent = "Compress File";

    }

});


// ==================================
// HELPER FUNCTIONS
// ==================================

function formatSize(bytes) {

    if (bytes === 0) return "0 Bytes";

    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];

    const index =
        Math.floor(Math.log(bytes) / Math.log(1024));

    const size =
        bytes / Math.pow(1024, index);

    return size.toFixed(2) + " " + units[index];

}


function clearStatus() {

    message.textContent = "";

    result.classList.add("hidden");

    resultText.textContent = "";

    downloadBtn.href = "#";

}