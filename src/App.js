import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function getCSRFToken() {
  const cookie = document.cookie
    .split("; ")
    .find(row => row.startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1] : "";
}

function App() {
  const [message, setMessage] = useState("Loading...");
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filename, setFilename] = useState("No file selected");

  // Fetch API status
  useEffect(() => {
    axios
      .get("http://127.0.0.1:8000/api/upload-invoice/")
      .then((response) => setMessage(response.data.message))
      .catch((error) => {
        console.error("Error fetching data: ", error);
        setMessage("Failed to load data.");
      });
  }, []);

  // Handle file selection
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFilename(selectedFile.name);
    } else {
      setFile(null);
      setFilename("No file selected");
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const csrfToken = getCSRFToken();
      
      const res = await axios.post(
        "http://127.0.0.1:8000/api/upload-invoice/",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            "X-CSRFToken": csrfToken,
          },
          withCredentials: true,
        }
      );

      console.log("Response received:", res.data);
      setResponse(res.data);
    } catch (error) {
      console.error("Error uploading file:", error);
      
      if (error.response) {
        setError(`Server error: ${error.response.data.error || error.response.statusText}`);
      } else if (error.request) {
        setError("No response from server. Please check your connection.");
      } else {
        setError(`Error: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatJson = (json) => {
    if (!json) return "No data";
    
    // If json is already an object, we don't need to parse it
    const data = typeof json === 'string' ? JSON.parse(json) : json;
    
    return (
      <div className="json-display">
        {Object.entries(data).map(([key, value]) => {
          // Skip rendering status and message fields that are already shown elsewhere
          if (key === 'status' || key === 'message' || key === 'file_name' || 
              key === 'file_path' || key === 'invoice_id') {
            return null;
          }
          
          if (key === 'extracted_data') {
            return (
              <div key={key} className="json-section">
                <h4>Extracted Data</h4>
                <pre>{JSON.stringify(value, null, 2)}</pre>
              </div>
            );
          }
          
          return (
            <div key={key} className="json-field">
              <strong>{key.replace(/_/g, ' ').toUpperCase()}: </strong>
              {typeof value === 'object' ? 
                <pre>{JSON.stringify(value, null, 2)}</pre> : 
                <span>{value}</span>}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="container">
      <div className="logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 19l7-7 3 3-7 7-3-3z"></path>
          <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path>
          <path d="M2 2l7.586 7.586"></path>
          <circle cx="11" cy="11" r="2"></circle>
        </svg>
      </div>

      <div className="card">
        <div className="card-illustration">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" fill="none">
            <circle cx="50" cy="40" r="15" stroke="#333" strokeWidth="2" fill="#f0f0f0" />
            <path d="M65 65C65 73.2843 58.2843 80 50 80C41.7157 80 35 73.2843 35 65C35 56.7157 41.7157 50 50 50C58.2843 50 65 56.7157 65 65Z" stroke="#333" strokeWidth="2" fill="#f0f0f0" />
            <path d="M50 100C63.2548 100 74 89.2548 74 76H26C26 89.2548 36.7452 100 50 100Z" stroke="#333" strokeWidth="2" fill="#f0f0f0" />
            <circle cx="80" cy="30" r="2" fill="#ff6d3b" />
            <circle cx="20" cy="80" r="2" fill="#ff6d3b" />
            <circle cx="85" cy="70" r="2" fill="#ff6d3b" />
          </svg>
        </div>
        
        <h1>AI-Powered Invoice Processor</h1>
        <p className="redirect-message">Upload your invoice to extract data automatically</p>
        
        <div className="upload-section">
          <div className="file-input-container">
            <input 
              type="file" 
              className="file-input"
              onChange={handleFileChange} 
              accept=".pdf,.jpg,.jpeg,.png" 
            />
            <p>{filename}</p>
          </div>
          
          <button 
            className="upload-btn" 
            onClick={handleUpload}
            disabled={loading || !file}
          >
            {loading ? "Processing..." : "Upload Invoice"}
          </button>
        </div>
        
        <p className="status-message">{message}</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && <div className="loading">Processing invoice... Please wait</div>}

      {response && (
        <div className="response-container">
          <div className="response-header">
            <h3 className="response-title">Invoice Analysis Results</h3>
            <span className={`response-status ${response.status !== "success" ? "error" : ""}`}>
              {response.status === "success" ? "✓ Success" : "× Failed"}
            </span>
          </div>
          
          {response.file_name && (
            <div className="file-info">
              <p><strong>File:</strong> {response.file_name}</p>
              {response.invoice_id && (
                <p><strong>Invoice ID:</strong> {response.invoice_id}</p>
              )}
            </div>
          )}
          
          <h4>Extracted Invoice Data:</h4>
          <div className="data-display">
            {formatJson(response)}
          </div>
        </div>
      )}

      <div className="footer">
        <div className="language-selector">
          <button className="active">English</button>
          <button>Back_Benchers</button>
        </div>
        <p>©2025 Invoice AI, Inc. All rights reserved.</p>
        <div>
          <a href="#">Terms of use</a>
          <a href="#">Privacy policy</a>
        </div>
      </div>
    </div>
  );
}

export default App;