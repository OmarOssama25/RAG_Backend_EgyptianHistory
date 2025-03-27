const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const axios = require('axios'); // New import for HTTP requests

// Flask model server URL
const MODEL_SERVER_URL = process.env.MODEL_SERVER_URL || 'http://localhost:5050';

// Track indexing status
let indexingStatus = {
  isIndexing: false,
  progress: 0,
  error: null,
  message: null,
  lastIndexed: null
};

// Upload PDF file
exports.uploadPdf = (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded' });
    }
    
    res.status(200).json({ 
      success: true, 
      message: 'File uploaded successfully', 
      filename: req.file.filename,
      path: req.file.path
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    res.status(500).json({ success: false, message: 'Error uploading file', error: error.message });
  }
};

// Index the document
exports.indexDocument = (req, res) => {
  try {
    if (indexingStatus.isIndexing) {
      return res.status(409).json({ 
        success: false, 
        message: 'Indexing already in progress', 
        progress: indexingStatus.progress 
      });
    }

    const pdfPath = path.join(__dirname, '../../data/egyptian_history.pdf');
    
    if (!fs.existsSync(pdfPath)) {
      return res.status(404).json({ 
        success: false, 
        message: 'PDF file not found. Please upload a file first.' 
      });
    }

    indexingStatus = {
      isIndexing: true,
      progress: 0,
      error: null,
      message: null,
      lastIndexed: null
    };

    // Run the Python indexer script
    const pythonProcess = spawn('python', [
      path.join(__dirname, '../../rag/indexer.py'),
      pdfPath
    ]);

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      console.log('Indexer output:', output);
      
      // Try to parse progress updates
      try {
        if (output.includes('progress:')) {
          const progressMatch = output.match(/progress: (\d+)/);
          if (progressMatch && progressMatch[1]) {
            indexingStatus.progress = parseInt(progressMatch[1]);
          }
        } else if (output.includes('completed')) {
          // This is a completion message
          indexingStatus.message = output;
        }
      } catch (e) {
        console.error('Error parsing progress:', e);
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      const output = data.toString();
      console.log(`Indexer stderr output: ${output}`);
      
      // Determine if this is an actual error or just an info message
      if (output.includes('ERROR') || output.includes('Error:')) {
        indexingStatus.error = output;
      } else if (output.includes('completed') || output.includes('INFO')) {
        // This is likely an info message printed to stderr
        indexingStatus.message = output;
      }
    });

    pythonProcess.on('close', (code) => {
      console.log(`Indexing process exited with code ${code}`);
      indexingStatus.isIndexing = false;
      
      if (code === 0) {
        indexingStatus.progress = 100;
        indexingStatus.lastIndexed = new Date().toISOString();
        if (!indexingStatus.message) {
          indexingStatus.message = `Indexing completed successfully`;
        }
        // Clear any error that might have been set incorrectly
        if (indexingStatus.error && indexingStatus.error.includes('INFO') && indexingStatus.error.includes('completed')) {
          const message = indexingStatus.error;
          indexingStatus.error = null;
          indexingStatus.message = message;
        }
      } else {
        if (!indexingStatus.error) {
          indexingStatus.error = `Process exited with code ${code}`;
        }
      }
    });

    res.status(202).json({ 
      success: true, 
      message: 'Indexing started', 
      status: indexingStatus 
    });
  } catch (error) {
    console.error('Error starting indexing process:', error);
    indexingStatus.isIndexing = false;
    indexingStatus.error = error.message;
    res.status(500).json({ 
      success: false, 
      message: 'Error starting indexing process', 
      error: error.message 
    });
  }
};

// Query the RAG system using the Flask model server
exports.queryRag = async (req, res) => {  // Changed to async function
  try {
    const { query } = req.body;
    
    if (!query) {
      return res.status(400).json({ 
        success: false, 
        message: 'Query is required' 
      });
    }

    // Check if indexing is complete
    if (indexingStatus.isIndexing) {
      return res.status(409).json({ 
        success: false, 
        message: 'Indexing in progress, please wait', 
        progress: indexingStatus.progress 
      });
    }

    if (!indexingStatus.lastIndexed) {
      return res.status(400).json({ 
        success: false, 
        message: 'Document has not been indexed yet. Please index first.' 
      });
    }

    // Call the Flask model server API instead of spawning a Python process
    try {
      console.log(`Sending query to model server: ${MODEL_SERVER_URL}/query`);
      const response = await axios.post(`${MODEL_SERVER_URL}/query`, {
        query: query,
        top_k: 5
      });
      
      res.status(200).json({
        success: true,
        query,
        response: response.data.response
      });
    } catch (error) {
      console.error('Error calling model server:', error.response?.data || error.message);
      res.status(500).json({
        success: false,
        message: 'Error generating response',
        error: error.response?.data?.message || error.message
      });
    }
  } catch (error) {
    console.error('Error querying RAG system:', error);
    res.status(500).json({
      success: false,
      message: 'Error querying RAG system',
      error: error.message
    });
  }
};

// Get indexing status
exports.getStatus = (req, res) => {
  // Create a clean copy of the status for the response
  const statusResponse = {
    isIndexing: indexingStatus.isIndexing,
    progress: indexingStatus.progress,
    message: indexingStatus.message,
    error: indexingStatus.error,
    lastIndexed: indexingStatus.lastIndexed
  };
  
  res.status(200).json({
    success: true,
    status: statusResponse
  });
};