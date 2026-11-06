// ==========================================
// 1. SELECT HTML ELEMENTS
// ==========================================

const API_BASE_URL = "";

const fileInput = document.getElementById("file-upload");

const questionInput = document.getElementById("user-question");

const sendButton = document.getElementById("send-btn");

const chatMessages = document.getElementById("chat-messages");

const documentList = document.getElementById("document-list");

const chatForm = document.getElementById("chat-form");

// ==========================================
// 2. STORE DOCUMENTS
// ==========================================

// Each document will have:
// file   -> Actual PDF
// name   -> PDF filename
// status -> uploading, ready, or failed

let uploadedFiles = [];

// ==========================================
// 3. DISPLAY DOCUMENTS
// ==========================================

function displayDocuments() {

// Clear existing document list  
documentList.textContent = "";  

// Check whether documents exist  
if (uploadedFiles.length === 0) {  

    const emptyMessage = document.createElement("p");  

    emptyMessage.textContent = "No documents uploaded yet.";  

    documentList.appendChild(emptyMessage);  

    return;  
}  

// Display each document  
uploadedFiles.forEach(function (doc) {  

    const fileItem = document.createElement("div");  

    fileItem.classList.add("document-item");  


    // Display PDF name  

    const fileName = document.createElement("span");  

    fileName.textContent = "📄 " + doc.name;  


    // Create status element  

    const status = document.createElement("span");  

    status.classList.add("document-status");  


    // Check document status  

    if (doc.status === "uploading") {  

        status.textContent = "Uploading...";  

        status.classList.add("status-uploading");  

    }  

    else if (doc.status === "ready") {  

        status.textContent = "✓ Ready to use";  

        status.classList.add("status-ready");  

    }  

    else if (doc.status === "failed") {  

        status.textContent = "Upload failed";  

        status.classList.add("status-failed");  

    }  


    // Create remove button  

    const removeButton = document.createElement("button");  

    removeButton.textContent = "✕";  

    removeButton.classList.add("remove-file-btn");  


    // Prevent removal while uploading  

    removeButton.disabled = doc.status === "uploading";  


    // Remove document when clicked  

    removeButton.addEventListener("click", function () {  

        uploadedFiles = uploadedFiles.filter(function (item) {  

            return item !== doc;  

        });  

        displayDocuments();  

    });  


    // Add elements to document item  

    fileItem.appendChild(fileName);  

    fileItem.appendChild(status);  

    fileItem.appendChild(removeButton);  


    // Add document to document list  

    documentList.appendChild(fileItem);  

});

}

function addMessage(message, sender) {

    // Create a new message element
    const messageElement = document.createElement("div");

    // Add CSS classes
    messageElement.classList.add("message", sender);

    // Format assistant messages using Markdown
    if (sender === "assistant") {

        // Convert Markdown into HTML
        const rawHTML = marked.parse(message);

        // Sanitize the generated HTML
        const safeHTML = DOMPurify.sanitize(rawHTML);

        // Display the safe HTML
        messageElement.innerHTML = safeHTML;

    } else {

        // Display user messages as plain text
        messageElement.textContent = message;

    }

    // Add message to chat area
    chatMessages.appendChild(messageElement);

    // Automatically scroll to the latest message
    requestAnimationFrame(function () {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: "smooth"
        });
    });

}

async function askQuestion(question) {

    // Send question to FastAPI
    const response = await fetch(`${API_BASE_URL}/ask`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            question: question,

            document_id: null

        })

    });


    // Check whether request was successful
    if (!response.ok) {

        throw new Error("Failed to get response from server.");

    }


    // Convert server response into JavaScript object
    const data = await response.json();


    // Return the generated answer
    return data;

}

chatForm.addEventListener("submit", async function (event) {

    // Prevent the page from refreshing
    event.preventDefault();

    // Get the user's question
    const question = questionInput.value.trim();

    // Check whether the question is empty
    if (question === "") {
        return;
    }

    // Display the user's question
    addMessage(question, "user");

    // Clear the input field
    questionInput.value = "";

    // Disable Send button while processing
    sendButton.disabled = true;

    // Create AI typing indicator
const loadingMessage = document.createElement("div");

loadingMessage.classList.add(
    "message",
    "assistant",
    "typing-indicator"
);

	// Create heading
	const typingHeading = document.createElement("div");

	typingHeading.classList.add("typing-heading");

	typingHeading.innerHTML = `
    		<span class="typing-icon">🤖</span>
    		<span>AI Assistant is thinking</span>
	`;

	// Create dots container
	const dotsContainer = document.createElement("div");

	dotsContainer.classList.add("typing-dots");

	// Create three dots
	for (let i = 0; i < 3; i++) {
   	const dot = document.createElement("span");
    	dotsContainer.appendChild(dot);
	}

	// Add heading and dots
	loadingMessage.appendChild(typingHeading);
	loadingMessage.appendChild(dotsContainer);

    // Display the loading message
    chatMessages.appendChild(loadingMessage);

	// Scroll to the AI thinking indicator
	requestAnimationFrame(function () {
   	 chatMessages.scrollTo({
       	 	top: chatMessages.scrollHeight,
        	behavior: "smooth"
    	});
    });


    try {

        // Send question to backend and wait for answer
        const data = await askQuestion(question);

        // Remove the loading message
        loadingMessage.remove();

        // Display the AI-generated answer
        addMessage(data.answer, "assistant");

    }

    catch (error) {

        // Remove the loading message
        loadingMessage.remove();

        // Display an error message
        addMessage(
            "Sorry, something went wrong while finding your answer. Please try again.",
            "assistant"
        );

        console.error("Error:", error);

    }

    finally {

        // Enable Send button again
        sendButton.disabled = false;

    }

});

// ==========================================
// 4. HANDLE FILE SELECTION
// ==========================================

fileInput.addEventListener("change", function () {

const file = fileInput.files[0];  


// Check whether a file was selected  

if (!file) {  

    return;  

}  


// Check whether selected file is a PDF  

if (  

    file.type !== "application/pdf" &&  

    !file.name.toLowerCase().endsWith(".pdf")  

) {  

    alert("Only PDF files are allowed!");  

    fileInput.value = "";  

    return;  

}  


// Check for duplicate files  

const alreadyExists = uploadedFiles.some(function (uploadedFile) {  

    return uploadedFile.name === file.name &&  

           uploadedFile.file.size === file.size;  

});  


if (!alreadyExists) {  


    // Create document object  

    const uploadedDocument = {  

        file: file,  

        name: file.name,  

        status: "uploading"  

    };  


    // Add document to array  

    uploadedFiles.push(uploadedDocument);  


    // Display uploading status immediately  

    displayDocuments();  


    // Send PDF to backend  

    uploadPDF(uploadedDocument);  


} else {  

    alert("This document has already been added!");  

}  


// Reset file input so the same file can be selected again  

fileInput.value = "";

});


// ==========================================
// 5. UPLOAD PDF TO BACKEND
// ==========================================

async function uploadPDF(uploadedDocument) {

// Prepare PDF for upload  

const formData = new FormData();  

formData.append("file", uploadedDocument.file);  


try {  


    // Send PDF to FastAPI backend  

    const response = await fetch(  

        `${API_BASE_URL}/process-upload`,  

        {  

            method: "POST",  

            body: formData  

        }  

    );  


    // Read backend response  

    const result = await response.json();  


    // Check whether upload was successful  

    if (!response.ok) {  

        throw new Error(result.detail || "Upload failed!");  

    }  


    // Update document status  

    uploadedDocument.status = "ready";  


    // Refresh document list  

    displayDocuments();  


    // No alert needed!  


} catch (error) {  


    // Mark document as failed  

    uploadedDocument.status = "failed";  


    // Refresh document list  

    displayDocuments();  


    console.error("PDF upload failed:", error);  

}

}

